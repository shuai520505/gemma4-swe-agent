import json
import os
from pathlib import Path
import unittest
from harness_v2.evidence import read_events, atomic_json
from u_re.v01.runner_cases import HERE, GOOD, exercise
from u_re.v01.audit import inspect_case


class RunnerTests(unittest.IsolatedAsyncioTestCase):
    async def run_case(self,arm,name):
        root=Path(os.environ['URE_EVIDENCE'])/(arm+'_'+name)
        result=await exercise(arm,name,root)
        self.assertTrue(json.loads((root/'cleanup.json').read_text())['complete'])
        self.assertEqual(json.loads((root/'cleanup.json').read_text())['leftover_sandboxes'],0)
        for row in result['wire_configuration']:
            self.assertEqual(set(row['tool_names']),{'get_status','run_command','read_file','edit_file','write_file','submit_patch'})
            self.assertEqual(row['output'],16384);self.assertEqual(row['thinking'],4096)
            self.assertEqual(row['seed'],17);self.assertEqual(row['sampling'],{})
        first=json.loads((root/'request_snapshots.jsonl').read_text().splitlines()[0])
        system='\n'.join(v['content'] for v in first['body']['messages'] if v['role']=='system')
        self.assertIn((HERE/f'candidate_{arm}/prompts/system.md').read_text().strip(),system)
        self.assertIn('{"n": 0}',str(first['body']['messages']))
        audit=inspect_case(root);atomic_json(root/'progress_observation.json',audit)
        return root,result,audit

    async def test_A_basic_both_candidates(self):
        for arm in ('noegv','full'):
            root,r,a=await self.run_case(arm,'basic')
            self.assertEqual(r['final_app'],GOOD);self.assertEqual(r['successful_submits'],1)
            self.assertFalse(r['tools_after_first_successful_submit']);self.assertTrue(r['HTTP_audit']['passed'])
            self.assertIn('+    return n >= 0',(root/'returned.patch').read_text())

    async def test_B_real_counterexample_revision_same_assertion_passes(self):
        root,r,a=await self.run_case('full','closed_loop')
        self.assertTrue(r['counterexample_revision_retest'])
        self.assertEqual(r['successful_edits'],2);self.assertEqual(r['successful_submits'],1)
        self.assertEqual(r['final_app'],GOOD);self.assertEqual(a['unchanged_command_repetitions'],0)

    async def test_C_wrong_test_does_not_change_correct_production(self):
        root,r,a=await self.run_case('full','wrong_test')
        self.assertEqual(r['successful_edits'],1);self.assertEqual(r['final_app'],GOOD)
        self.assertTrue(any('WRONG_EXPECTATION' in str(c['result']) and c['result']['status']=='error' for c in r['command_responses']))
        self.assertEqual(r['successful_submits'],1);self.assertNotIn('wrong_probe.py',(root/'returned.patch').read_text())

    async def test_D_cooperative_no_progress_and_first_no_match_is_evidence(self):
        root,r,a=await self.run_case('full','no_progress')
        self.assertEqual(a['unchanged_command_repetitions'],0)
        grep=next(v for v in a['observations'] if v['tool']=='run_command' and v['args']['command'].startswith('grep'))
        self.assertEqual(grep['progress'],'NEW_EVIDENCE');self.assertEqual(grep['response']['status'],'error')

    async def test_D_negative_mock_can_still_repeat_unchanged_check(self):
        root,r,a=await self.run_case('full','repeat_negative')
        self.assertEqual(a['unchanged_command_repetitions'],1)
        self.assertFalse(a['online_enforcement'])

    async def test_E_failed_real_submit_can_be_repaired_and_retried(self):
        root,r,a=await self.run_case('full','submit_failure')
        self.assertTrue(any(e['result']['status']=='error' for e in r['submit_responses']))
        self.assertEqual(r['successful_submits'],1);self.assertEqual(r['final_app'],GOOD)

    async def test_E_negative_successful_submit_is_not_runtime_termination(self):
        root,r,a=await self.run_case('full','post_submit_negative')
        self.assertTrue(r['tools_after_first_successful_submit'])
        self.assertEqual(r['successful_submits'],2)
        # This is an expected demonstration of a missing hard guarantee, NOT
        # a claim that Gemma follows Closure or that Prompt wording enforces it.

    async def test_F_shared_sixty_counted_real_tools_both_arms(self):
        for arm in ('noegv','full'):
            root,r,a=await self.run_case(arm,'exact_tools')
            self.assertEqual(r['counted_tools'],60)
            self.assertTrue(any('BudgetExceeded' in str(v) for v in read_events(root/'adk_events.jsonl')))
            self.assertEqual(r['final_app'],GOOD);self.assertEqual(r['successful_submits'],1)
            self.assertGreater(r['tool_responses'],60)

    async def test_F_supplemental_near_closure_ten_second_fixture(self):
        root,r,a=await self.run_case('full','near_closure')
        self.assertEqual(r['successful_submits'],1);self.assertFalse(r['tools_after_first_successful_submit'])
        self.assertGreaterEqual(r['native_agent_seconds'],8);self.assertLess(r['native_agent_seconds'],11)
        self.assertEqual(json.loads((root/'boundary.json').read_text())['budget_seconds'],10)

    async def test_F_external_cancellation_propagates_and_patch_survives(self):
        root,r,a=await self.run_case('full','external_cancel')
        self.assertTrue(r['external_cancellation_propagated']);self.assertTrue(r['HTTP_cancelled'])
        self.assertTrue((root/'latest.patch').exists());self.assertIsNone(r['HTTP_audit']['rows'][-1]['usage'])
        self.assertEqual(r['HTTP_audit']['rows'][-1]['terminal_status'],'cancelled')
        # Frozen auditor intentionally only admits native deadline cancellation;
        # this explicit external cancellation is retained with its own boundary.
        self.assertIn('unexplained_cancellation',r['HTTP_audit']['reasons'])

    async def test_F_real_300_second_boundary_each_candidate(self):
        for arm in ('noegv','full'):
            root,r,a=await self.run_case(arm,'deadline')
            self.assertGreaterEqual(r['native_agent_seconds'],299)
            self.assertLess(r['native_agent_seconds'],315)
            self.assertIn('session timeout',str(r['error']).lower())
            self.assertTrue(r['HTTP_cancelled']);self.assertTrue(r['HTTP_audit']['passed'])
            self.assertIsNone(r['HTTP_audit']['rows'][-1]['usage'])
            self.assertTrue((root/'latest.patch').exists());self.assertEqual(r['final_app'],GOOD)

    async def test_F_actual_120_second_command_limit_and_no_late_write(self):
        root,r,a=await self.run_case('full','command_limit')
        self.assertTrue(any(c['result']['status']=='error' for c in r['command_responses']))
        durations=[v['elapsed_seconds'] for v in read_events(root/'events.jsonl') if v['kind']=='sandbox_command_end']
        self.assertGreaterEqual(max(durations),119);self.assertLess(max(durations),135)
        self.assertTrue(any(c['result']['status']=='ok' and 'ALIVE False' in str(c['result']) for c in r['command_responses']))
        self.assertEqual(r['successful_submits'],1)

    async def test_G_missing_response_usage_is_partial_not_zero(self):
        root,r,a=await self.run_case('full','missing_usage')
        self.assertFalse(r['HTTP_audit']['passed']);self.assertTrue(r['HTTP_audit']['partial_token_usage'])
        self.assertIsNone(r['HTTP_audit']['rows'][-1]['usage'])
