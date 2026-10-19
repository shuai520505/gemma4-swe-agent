import json
import os
from pathlib import Path
import unittest
from .runner_cases import exercise, HERE


class ClosedLoopTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_closed_loop_and_failure_paths(self):
        root=Path(os.environ['S2_CPU_EVIDENCE'])
        cases=['closed_loop','unknown','invalid_probe','ignored','still_fails','old_regression',
               'child_write','forbidden_tool','child_command_timeout','cancel_child','near_deadline',
               'direct_retest','lost_result','budget','submit_fail','parameter_drift','missing_usage','transport_error']
        results={}
        for case in cases:
            with self.subTest(case=case):
                r=await exercise(case,root/case);results[case]=r
                self.assertTrue(json.loads((root/case/'cleanup.json').read_text())['complete'])
                if case in ('closed_loop','direct_retest'):
                    self.assertTrue(r['closed_loop'],r.get('error'))
                    self.assertTrue(r['explicit_submit'])
                    self.assertTrue(r['HTTP']['passed'],r['HTTP'])
                    self.assertFalse(r['child_side_effects'])
                    self.assertIn('return n >= 0',(root/case/'submitted.patch').read_text())
                if case in ('unknown','invalid_probe','ignored','still_fails','old_regression','lost_result'):
                    self.assertFalse(r['closed_loop'])
                if case=='ignored':
                    self.assertTrue(r['feedback_delivered']);self.assertFalse(r['feedback_handled'])
                if case in ('still_fails','old_regression'):
                    self.assertTrue(r['feedback_handled']);self.assertFalse(r['counterevidence_cleared'])
                if case=='child_write':self.assertTrue(r['child_side_effects'])
                if case=='forbidden_tool':
                    self.assertIsNotNone(r['error']);self.assertFalse(r['child_side_effects'])
                if case=='child_command_timeout':
                    self.assertIn('TimeoutExceeded',(root/case/'nested_audit.jsonl').read_text())
                if case=='cancel_child':
                    self.assertTrue(r['child_HTTP_cancelled']);self.assertEqual(r['error'],'CancelledError propagated')
                    self.assertEqual(r['HTTP']['rows'][-1]['terminal_status'],'cancelled')
                if case=='near_deadline':
                    self.assertEqual(r['actors']['egv_verifier'],0);self.assertTrue(r['explicit_submit'])
                if case=='lost_result':self.assertFalse(r['feedback_delivered'])
                if case=='budget':
                    self.assertEqual(r['counted_tools'],3)
                    self.assertIn('BudgetExceeded',(root/case/'nested_audit.jsonl').read_text())
                if case=='submit_fail':
                    self.assertFalse(r['explicit_submit']);self.assertIn('GitDiffError',(root/case/'nested_audit.jsonl').read_text())
                if case=='parameter_drift':self.assertIn('Output cap drift',str(r['error']))
                if case=='missing_usage':self.assertTrue(r['HTTP']['partial_token_usage'])
                if case=='transport_error':self.assertIn('transport_error',(root/case/'http_lifecycle.jsonl').read_text())
        (root/'case_summary.json').write_text(json.dumps({k:{n:v for n,v in r.items() if n!='all_model_rows'} for k,r in results.items()},indent=2))

    async def test_skip_summarization_control_flow(self):
        root=Path(os.environ['S2_CPU_EVIDENCE'])/'skip_true'
        r=await exercise('closed_loop',root,skip=True)
        self.assertTrue(r['target_counterevidence'])
        self.assertFalse(r['closed_loop'])
        self.assertFalse(r['explicit_submit'])

    async def test_official_Harness_native_shared_budget_and_deadline(self):
        root=Path(os.environ['S2_CPU_EVIDENCE'])
        for case in ('closed_loop','budget','native_deadline'):
            with self.subTest(case=case):
                out=root/('native_'+case);r=await exercise(case,out,native=True)
                if case=='closed_loop':
                    self.assertTrue(r['closed_loop'],r['error']);self.assertTrue(r['explicit_submit'])
                if case=='budget':
                    self.assertEqual(r['counted_tools'],3)
                    # The native Harness checks exhaustion between Runner
                    # invocations, not after every nested event. Charged tools
                    # are denied at the shared gate, while a free submit may
                    # still complete in this invocation. CPU03 disproved the
                    # old immediate-termination assumption; preserve it.
                    self.assertTrue(r['explicit_submit'])
                    self.assertFalse(r['closed_loop'])
                    patch=(out/'native.patch').read_text()
                    self.assertIn('return n > 0',patch)
                    self.assertNotIn('return n >= 0',patch)
                    self.assertIn('BudgetExceeded',(out/'nested_audit.jsonl').read_text())
                if case=='native_deadline':
                    self.assertTrue(r['child_HTTP_cancelled'])
                    self.assertIn('session timeout',str(r['error']))
                    self.assertTrue(r['HTTP']['passed'],r['HTTP'])

    async def test_candidate_ZIP_compiles_with_exact_paths_and_parameters(self):
        import tempfile,zipfile
        from adk_submission import ModelRegistry,compile_submission,validate_directory
        from google.adk.models.lite_llm import LiteLlm
        from swegemma.context import SwegemmaContext
        from swegemma.config import build_submission_limits
        from .runner_cases import MODEL
        models=ModelRegistry();models.register(MODEL,LiteLlm(model='openai/'+MODEL,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(HERE/'submission.zip') as z:
                self.assertEqual(len(z.namelist()),5)
                self.assertIn('agent.yaml',z.namelist());z.extractall(tmp)
                self.assertFalse(any(n.endswith('.py') for n in z.namelist()))
            limits,constraints=build_submission_limits();validate_directory(tmp,limits=limits)
            agent=compile_submission(tmp,SwegemmaContext().create_tools(),models,limits=limits,generation_constraints=constraints)
            from s2.egv_agenttool_v01.validation import validate_candidate
            from s1.config import Config
            validate_candidate(agent,Config())
            # Research worker imports actual public APIs without starting a
            # model, sandbox or GPU. The ZIP contains none of this code.
            from s2.egv_agenttool_v01 import worker, worker_entry, runner_observer
            child=agent.tools[-1].agent
            self.assertFalse(agent.tools[-1].skip_summarization)
            self.assertEqual(len(child.tools),3)
            for a in (agent,child):
                cfg=a.generate_content_config
                self.assertEqual(cfg.max_output_tokens,16384);self.assertEqual(cfg.seed,17)
                self.assertEqual(cfg.thinking_config.thinking_budget,4096)
                self.assertIsNone(cfg.thinking_config.include_thoughts)
                self.assertIsNone(cfg.temperature)
            self.assertIn('S2 division of responsibility',agent.instruction)
            self.assertIn('Verification status:',child.instruction)
            # Literal JSON remains task data, not an instruction placeholder.
            self.assertNotIn('{',child.instruction)
