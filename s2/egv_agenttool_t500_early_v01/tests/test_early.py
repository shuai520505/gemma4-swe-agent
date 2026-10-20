import hashlib
import json
import os
from pathlib import Path
import unittest
from harness_v2.evidence import read_events,atomic_json
from s2.egv_agenttool_t500_early_v01.runner_cases import exercise,HERE,BAD


class EarlyTests(unittest.IsolatedAsyncioTestCase):
    def out(self,name):return Path(os.environ['S2_EARLY_EVIDENCE'])/name

    def rows(self,p):return read_events(p/'nested_audit.jsonl')

    def assert_prompt_and_cleanup(self,p,r):
        self.assertTrue(json.loads((p/'cleanup.json').read_text())['complete'])
        self.assertEqual(json.loads((p/'cleanup.json').read_text())['leftover_sandboxes'],0)
        self.assertFalse(r['child_side_effects'])
        text=(HERE/'candidate/prompts/main.md').read_text()
        for row in r['all_model_rows']:
            system=row['body']['messages'][0]['content']
            if row['actor']=='main_coding_agent':self.assertIn(text.strip(),system)
            else:self.assertIn((HERE/'candidate/sub_agents/egv_verifier.md').read_text().strip(),system)
        self.assertNotIn('{',text)

    async def test_A_pre_patch_delegation_real_tools(self):
        p=self.out('A_pre_patch');r=await exercise('early_only',p)
        self.assertTrue(r['target_counterevidence']);self.assertTrue(r['feedback_delivered'])
        self.assertFalse(r['feedback_handled']);self.assertFalse(r['closed_loop'])
        start=next(e for e in self.rows(p) if e['kind']=='tool_start' and e['tool']=='egv_verifier')
        self.assertEqual(start['files']['app.py'],hashlib.sha256(BAD.encode()).hexdigest())
        self.assertIn('No patch exists',start['args']['request'])
        self.assertFalse(any(e['kind']=='tool_start' and e['tool'] in ('edit_file','write_file') for e in self.rows(p)))
        # Session is created empty by the real fixture; the declared child
        # output_key legitimately adds its report after delegation.
        self.assertIn('Counterevidence: zero',json.loads((p/'state.json').read_text())['egv_latest_report'])
        self.assert_prompt_and_cleanup(p,r)

    async def test_B_pre_patch_counterevidence_repair_retest_submit(self):
        p=self.out('B_early_repair');r=await exercise('early_repair',p,native=True,research_observer=True)
        self.assertTrue(r['closed_loop'],r['error']);self.assertTrue(r['explicit_submit'])
        self.assertIn('return n >= 0',(p/'native.patch').read_text())
        self.assert_prompt_and_cleanup(p,r)

    async def test_C_post_patch_repair_and_child_retest(self):
        p=self.out('C_post_patch');r=await exercise('closed_loop',p,native=True,research_observer=True)
        self.assertTrue(r['closed_loop']);self.assertTrue(r['explicit_submit'])
        self.assertEqual(sum(e['kind']=='tool_start' and e['tool']=='egv_verifier' for e in self.rows(p)),2)
        self.assert_prompt_and_cleanup(p,r)

    async def test_D_late_status_skip_delegate_and_submit(self):
        p=self.out('D_close');r=await exercise('near_deadline',p)
        self.assertTrue(r['explicit_submit']);self.assertEqual(r['actors']['egv_verifier'],0)
        status=next(e['result'] for e in self.rows(p) if e['kind']=='tool_end' and e['tool']=='get_status')
        atomic_json(p/'actual_late_status.json',status)
        self.assertLess(status['time_seconds_remaining'],60)
        self.assertGreater(status['time_seconds_remaining'],0)
        self.assert_prompt_and_cleanup(p,r)

    async def test_E_real_diagnostic_cleanup_not_in_patch(self):
        p=self.out('E_cleanup');r=await exercise('cleanup',p)
        self.assertTrue(r['explicit_submit'])
        self.assertNotIn('scratch_probe.py',json.loads((p/'final_files.json').read_text()))
        self.assertNotIn('scratch_probe.py',(p/'submitted.patch').read_text())
        self.assertIn('app.py',(p/'submitted.patch').read_text())
        self.assert_prompt_and_cleanup(p,r)

    async def test_F_controlled_probe_attribution_four_cases(self):
        labels={}
        for case in ('wrong_expectation','production_regression','probe_environment','unverified'):
            with self.subTest(case=case):
                p=self.out('F_'+case);r=await exercise(case,p)
                commands=[e for e in self.rows(p) if e['kind']=='tool_end' and e['tool']=='run_command']
                probe=commands[0]['result'];canonical=commands[1]['result'] if len(commands)>1 else None
                if case=='wrong_expectation':
                    self.assertIn('WRONG_EXPECTATION',str(probe));self.assertIn('OLD_PASSED',str(canonical))
                    label='invalid_custom_expectation'
                elif case=='production_regression':
                    self.assertIn('TARGET_BOUNDARY',str(probe));self.assertIn('TARGET_BOUNDARY',str(canonical))
                    label='production_behavior_failure'
                elif case=='probe_environment':
                    self.assertIn('ModuleNotFoundError',str(probe));self.assertIn('OLD_PASSED',str(canonical))
                    label='probe_dependency_error'
                else:
                    self.assertIsNone(canonical);self.assertEqual(probe['exit_code'],0)
                    label='unverified'
                labels[case]=dict(classification=label,probe_result=probe,immutable_contract_result=canonical,
                    basis='Controlled fixture contract: accepts(0)=True, accepts(-1)=False; original checks.py unchanged. Not a universal exit-code classifier.')
                self.assert_prompt_and_cleanup(p,r)
        atomic_json(self.out('F_attribution.json'),labels)

    async def test_G_nested_cancel_missing_usage_and_side_effect_audit(self):
        for case in ('cancel_child','missing_usage','child_write'):
            with self.subTest(case=case):
                p=self.out('G_'+case);r=await exercise(case,p)
                self.assertTrue(json.loads((p/'cleanup.json').read_text())['complete'])
                if case=='cancel_child':
                    self.assertTrue(r['child_HTTP_cancelled']);self.assertEqual(r['error'],'CancelledError propagated')
                    self.assertIsNone(r['HTTP']['rows'][-1]['usage'])
                elif case=='missing_usage':self.assertTrue(r['HTTP']['partial_token_usage'])
                else:self.assertTrue(r['child_side_effects'])

    async def test_H_valid_direct_repair_no_mandatory_delegate(self):
        p=self.out('H_direct');r=await exercise('near_deadline',p)
        self.assertTrue(r['explicit_submit']);self.assertEqual(r['actors']['egv_verifier'],0)
        self.assertIn('return n >= 0',(p/'submitted.patch').read_text())
        self.assert_prompt_and_cleanup(p,r)
