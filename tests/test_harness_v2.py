"""CPU regressions. Scripted workers are not Gemma inference or task repairs."""
import asyncio
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


def component(test, name):
    try:
        return importlib.import_module('harness_v2.' + name)
    except ModuleNotFoundError as exc:
        test.fail(f'Harness V2 component is not implemented: {exc.name}')


class ContextTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_summarizer_without_cap_receives_registered_default(self):
        m=component(self,'context_budget')
        async def counter(body): return {'count':100,'max_model_len':32768}
        async def generate(**args): return args
        r=await m.RequestGuard(counter,generate,core_issue='issue').acompletion(
            model='openai/model',messages=[{'role':'user','content':'summary'}])
        self.assertEqual(r['max_completion_tokens'],16384)
    async def test_exact_context_boundary_and_one_token_over(self):
        m = component(self, 'context_budget')
        p = m.ContextPolicy()
        self.assertEqual(p.check(15360, 16384)['decision'], 'allow')
        with self.assertRaises(m.ContextBudgetExceeded):
            p.check(15361, 16384)
        with self.assertRaises(m.ContextBudgetExceeded):
            p.check(16385, 16384)

    async def test_tokenizer_failure_never_sends_generation(self):
        m = component(self, 'context_budget')
        sent = []
        async def counter(body):
            raise OSError('tokenizer unavailable')
        async def generate(**kwargs):
            sent.append(kwargs)
        guard = m.RequestGuard(counter, generate, core_issue='required issue')
        with self.assertRaises(m.ContextCountingError):
            await guard.acompletion(model='openai/model', messages=[], max_completion_tokens=16384)
        self.assertEqual(sent, [])

    async def test_tools_reasoning_and_core_issue_are_counted_before_send(self):
        m = component(self, 'context_budget')
        counted, sent, audit = [], [], []
        async def counter(body):
            counted.append(body)
            return {'count': 100, 'max_model_len': 32768}
        async def generate(**kwargs):
            sent.append(kwargs)
            return 'response'
        guard = m.RequestGuard(counter, generate, core_issue='original issue', emit=audit.append)
        tools = [{'type': 'function', 'function': {'name': 'read_file', 'parameters': {'type': 'object'}}}]
        messages = [{'role': 'system', 'content': 'frozen prompt'}, {'role': 'user', 'content': 'compacted history'}]
        result = await guard.acompletion(model='openai/model', messages=messages, tools=tools,
            max_completion_tokens=16384, extra_body={'chat_template_kwargs': {'enable_thinking': True}})
        self.assertEqual(result, 'response')
        self.assertEqual(messages[1]['content'], 'compacted history')
        self.assertEqual(counted[0]['tools'], tools)
        self.assertEqual(counted[0]['chat_template_kwargs'], {'enable_thinking': True})
        self.assertTrue(any(x.get('content') == 'original issue' for x in sent[0]['messages']))
        self.assertEqual(sent[0]['max_completion_tokens'], 16384)
        self.assertTrue(audit[-1]['core_restored'])

    async def test_oversize_issue_is_preserved_and_clearly_rejected(self):
        m = component(self, 'context_budget')
        sent, audit = [], []
        async def counter(body):
            self.assertEqual(body['messages'][0]['content'], 'core' * 20000)
            return {'count': 32000, 'max_model_len': 32768}
        async def generate(**kwargs):
            sent.append(kwargs)
        guard = m.RequestGuard(counter, generate, core_issue='core' * 20000, emit=audit.append)
        with self.assertRaises(m.ContextBudgetExceeded):
            await guard.acompletion(model='openai/model', messages=[], max_completion_tokens=16384)
        self.assertEqual(sent, [])
        self.assertEqual(audit[-1]['decision'], 'reject')

    async def test_no_issue_duplication_or_output_override(self):
        m = component(self, 'context_budget')
        async def counter(body):
            return {'count': 15360, 'max_model_len': 32768}
        async def generate(**kwargs):
            return kwargs
        guard = m.RequestGuard(counter, generate, core_issue='issue')
        result = await guard.acompletion(model='openai/model', messages=[{'role':'user','content':'full issue body'}],
                                        max_completion_tokens=16384)
        self.assertEqual(len(result['messages']), 1)
        self.assertEqual(result['max_completion_tokens'], 16384)


class OutcomeTests(unittest.TestCase):
    def test_missing_and_not_run_are_not_official_failures(self):
        m = component(self, 'outcomes')
        self.assertEqual(m.normalize(None, started=False)['status'], 'not_run')
        self.assertEqual(m.normalize(None, started=True, stage='agent')['status'], 'unknown')

    def test_only_confirmed_test_failure_is_failed(self):
        m = component(self, 'outcomes')
        raw = dict(resolved=False, test_exit_code=1, test_output='STDOUT:\n1 failed\nSTDERR:\n', error=None)
        before = json.dumps(raw, sort_keys=True)
        self.assertEqual(m.normalize(raw, started=True)['status'], 'failed')
        self.assertEqual(json.dumps(raw, sort_keys=True), before)
        raw.update(test_exit_code=124)
        result = m.normalize(raw, started=True)
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['failure_stage'], 'verification')

    def test_agent_timeout_does_not_erase_later_confirmed_test_failure(self):
        m=component(self,'outcomes')
        raw=dict(resolved=False,test_exit_code=1,error_message='Agent timed out',
            test_output='STDOUT:\n1 failed, 2 passed\nSTDERR:\n')
        self.assertEqual(m.normalize(raw,started=True)['status'],'failed')

    def test_agent_timeout_and_context_failure_are_unknown(self):
        m = component(self, 'outcomes')
        for error in ('Agent timed out', 'Sandbox execution error: ContextBudgetExceeded', 'Evaluation error: disk full'):
            raw = dict(resolved=False, test_exit_code=-1, error=error, test_output='')
            self.assertEqual(m.normalize(raw, started=True)['status'], 'unknown')
        self.assertEqual(m.normalize(dict(resolved=False,test_exit_code=1,
            error_message='Evaluation error: setup failed'),started=True)['status'],'unknown')
        for error in ('ContextBudgetExceeded','ContextCountingError','ContextWindowExceededError'):
            r=m.normalize(dict(resolved=False,test_exit_code=-1,error_message=error),started=True,stage='cleanup')
            self.assertEqual(r['failure_stage'],'context_admission')

    def test_resolved_and_collection_failure_preserve_official_values(self):
        m = component(self, 'outcomes')
        self.assertEqual(m.normalize(dict(resolved=True, test_exit_code=0), started=True)['status'], 'resolved')
        r = m.normalize(dict(resolved=False, test_exit_code=2,
            test_output='STDOUT:\nERROR collecting test_x.py\nSTDERR:\n'), started=True)
        self.assertEqual(r['status'], 'failed')
        self.assertEqual(r['failure_stage'], 'test_collection')

    def test_unknown_cannot_be_in_confirmed_failure_denominator(self):
        m = component(self, 'outcomes')
        rows = [dict(arm='v0', status=s) for s in ('resolved','failed','unknown','not_run')]
        summary = m.summarize(rows, planned_per_arm={'v0':4})['v0']
        self.assertEqual(summary['failed'], 1)
        self.assertEqual(summary['unknown'], 1)
        self.assertEqual(summary['not_run'], 1)
        self.assertIsNone(summary['resolution_rate'])
        rows[2]['status']='failed'; rows[3]['status']='failed'
        self.assertEqual(m.summarize(rows, planned_per_arm={'v0':4})['v0']['resolution_rate'], .25)

    def test_partial_other_arm_blocks_complete_comparison_rate(self):
        m=component(self,'outcomes')
        r=m.summarize([dict(arm='v0',status='resolved'),dict(arm='v1',status='unknown')],
            planned_per_arm={'v0':1,'v1':1})
        self.assertIsNone(r['v0']['resolution_rate'])

    def test_verifier_internal_error_is_unknown(self):
        m=component(self,'outcomes')
        self.assertEqual(m.normalize(dict(resolved=False,test_exit_code=3,
            test_output='STDOUT:\nINTERNALERROR\nSTDERR:\n'),started=True)['status'],'unknown')


class BudgetAndEvidenceTests(unittest.TestCase):
    def test_complete_pairs_are_not_split_across_notebooks(self):
        m=component(self,'batch')
        rows=[dict(instance_id=i,arm=a) for i in ('a','b','c','d') for a in ('v0','v1')]
        batches=m.split_pairs(rows)
        self.assertEqual([len(b) for b in batches],[4,4])
        for b in batches:
            self.assertEqual(len({r['instance_id'] for r in b}),2)
        with self.assertRaises(ValueError): m.split_pairs(rows[:-1])

    def test_cpu_gate_failure_blocks_gpu(self):
        m=component(self,'batch')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'gate.json'; p.write_text('{"passed":false}')
            with self.assertRaises(ValueError): m.require_cpu_gate(p,{},ROOT)
    def test_outer_budget_covers_every_stage_and_batch_fits(self):
        m = component(self, 'budgets')
        p = m.Budgets()
        self.assertGreater(p.outer_seconds, 8*60 + 5*60)
        self.assertEqual(p.outer_seconds, sum(p.stage_caps.values()) + p.safety_seconds)
        self.assertLessEqual(4*p.outer_seconds + 45*60 + 15*60, 180*60)

    def test_atomic_patch_versions_and_torn_journal_recovery(self):
        m = component(self, 'evidence')
        with tempfile.TemporaryDirectory() as tmp:
            j = m.Journal(Path(tmp))
            j.stage('agent')
            j.patch('first patch', source='explicit_submit')
            j.patch('second patch', source='agent_boundary')
            j.patch('second patch', source='agent_boundary')
            versions=list((Path(tmp)/'patches').glob('*.patch'))
            self.assertEqual(len(versions), 2)
            self.assertEqual((Path(tmp)/'latest.patch').read_text(), 'second patch')
            with (Path(tmp)/'events.jsonl').open('ab') as f:
                f.write(b'{"torn":')
            events=m.read_events(Path(tmp)/'events.jsonl')
            self.assertGreaterEqual(len(events), 3)
            self.assertEqual(events[0]['kind'], 'stage')

    def test_baseline_hashes_and_archives_remain_unchanged(self):
        m = component(self, 'integrity')
        self.assertGreaterEqual(m.verify_baseline(), 76)


class SupervisorTests(unittest.TestCase):
    def test_empty_checkpoint_is_not_mistaken_for_nonempty_patch(self):
        r,p=self.run_worker('empty')
        self.assertTrue(r['evidence']['patch_checkpoint'])
        self.assertEqual(r['evidence']['patch_checkpoint_bytes'],0)

    def test_bootstrap_failure_is_unknown_in_preparation_stage(self):
        m=component(self,'supervisor')
        with tempfile.TemporaryDirectory() as tmp:
            r=m.supervise([sys.executable,'-c','raise ImportError("fixture")'],Path(tmp)/'run',
                outer_seconds=5,stage_caps={},poll_seconds=.02)
        self.assertEqual(r['status'],'unknown')
        self.assertEqual(r['failure_stage'],'prepare_agent')
        self.assertEqual(r['controller_failure_stage'],'prepare_agent')

    def run_worker(self, mode, *, stage_caps=None, outer_seconds=8):
        m = component(self, 'supervisor')
        base=os.environ.get('HARNESS_V2_TEST_EVIDENCE_DIR')
        if base:
            output=Path(base)/self._testMethodName
        else:
            tmp = tempfile.TemporaryDirectory()
            self.addCleanup(tmp.cleanup)
            output=Path(tmp.name)/'run'
        cmd=[sys.executable, str(ROOT/'tests/harness_v2_fixture.py'), mode, str(output)]
        result=m.supervise(cmd, output, outer_seconds=outer_seconds,
            stage_caps=stage_caps or {}, poll_seconds=.02, terminate_grace=.1)
        return result,output

    def test_patch_survives_outer_timeout_without_official_result(self):
        r,p=self.run_worker('outer',outer_seconds=2)
        self.assertEqual(r['status'],'unknown')
        self.assertTrue((p/'latest.patch').is_file())
        self.assertFalse((p/'official_result.json').exists())
        self.assertTrue(r['process_tree_stopped'])
        time.sleep(.3)
        self.assertFalse((p/'contamination.txt').exists())

    def test_agent_stage_deadline_retains_evidence(self):
        r,p=self.run_worker('agent',stage_caps={'agent':.1})
        self.assertEqual(r['status'],'unknown')
        self.assertEqual(r['failure_stage'],'agent')
        self.assertTrue((p/'latest.patch').exists())

    def test_verifier_stage_deadline_retains_patch_and_native_trace(self):
        r,p=self.run_worker('verifier',stage_caps={'verification':.1})
        self.assertEqual(r['status'],'unknown')
        self.assertEqual(r['failure_stage'],'verification')
        self.assertTrue((p/'latest.patch').exists())
        self.assertTrue((p/'adk_events.jsonl').exists())
        self.assertTrue(r['evidence']['agent_boundary_trace'])

    def test_cleanup_delay_blocks_next_run_without_erasing_native_result(self):
        r,p=self.run_worker('cleanup',stage_caps={'cleanup':.1})
        self.assertEqual(r['status'],'resolved',str(r)+(p/'worker.stderr.log').read_text())
        self.assertEqual(json.loads((p/'official_result.json').read_text())['resolved'],True)
        self.assertFalse(r['allow_next_run'])
        self.assertEqual(r['controller_failure_stage'],'cleanup')

    def test_clean_completion_can_admit_next_run(self):
        r,p=self.run_worker('ok')
        self.assertEqual(r['status'],'resolved')
        self.assertTrue(r['allow_next_run'])
        self.assertTrue(r['process_tree_stopped'])

    def test_launcher_exit_does_not_kill_still_running_worker(self):
        r,p=self.run_worker('launcher')
        self.assertEqual(r['status'],'resolved',str(r)+(p/'worker.stderr.log').read_text())
        self.assertTrue(r['allow_next_run'])

    def test_orphaned_worker_is_stopped_at_outer_deadline(self):
        r,p=self.run_worker('launcher_outer',outer_seconds=2)
        self.assertEqual(r['status'],'unknown')
        self.assertTrue(r['process_tree_stopped'],str(r))
        self.assertFalse(r['allow_next_run'])


if __name__=='__main__':
    unittest.main()
