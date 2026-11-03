import json,subprocess,tempfile,unittest
from pathlib import Path
import core

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name);self.repo=self.home/'repo';self.repo.mkdir()
        (self.repo/'logic.py').write_text('def f(x):\n    return x > 0\n')
        for args in [['init','-q'],['config','user.name','Fixture'],['config','user.email','fixture@example.invalid'],['add','.'],['commit','-qm','fixture']]:
            subprocess.run(['git',*args],cwd=self.repo,check=True,capture_output=True)
        self.s=core.RepairState.create('fixture','Accept zero. Negative values remain false.',self.repo,'model-fixture')
        self.s.contract['requirements']=[dict(id='R1',text='Accept zero.',status='OBSERVED'),dict(id='R2',text='Negative values remain false.',status='OBSERVED')]
    def support(self):
        e=self.s.observe_source('logic.py',1,2,['R1'])
        self.s.hypothesis(dict(location='logic.py:f',mechanism='strict comparison excludes zero',support=[e['id']],contradictions=[],prediction='zero false before, true after',confidence=.8,next_experiment='assert f(0)',requirements=['R1']))
    def intent(self):
        self.support();self.s.intent(dict(files=['logic.py'],regions=['f'],behavior='accept zero',requirements=['R1','R2'],support=[self.s.evidence[0]['id']],regressions=['negative input'],preserve='negative false',discriminating_test='assert f(0) and not f(-1)'))
    def edit(self):
        (self.repo/'logic.py').write_text('def f(x):\n    return x >= 0\n');self.s.record_patch()
    def test_contract_observation_needs_original_quote(self):
        self.s.contract['requirements'][0]['text']='invented fact'
        with self.assertRaises(ValueError):self.s.validate_contract()
    def test_ledger_actual_source_and_bounds(self):
        e=self.s.observe_source('logic.py',1,2,['R1']);self.assertEqual(e['type'],'SOURCE_CODE');self.assertIn('return x > 0',e['observation']);self.assertFalse(e['stale'])
        with self.assertRaises(ValueError):self.s.observe_source('../secret.py',1,2,['R1'])
    def test_hypothesis_is_not_verified_semantics(self):
        self.support();self.assertEqual(self.s.cause['semantic_status'],'UNVERIFIED');self.assertEqual(self.s.next_action()['action'],'EDIT')
    def test_unlinked_patch_and_unrelated_file_flag(self):
        self.intent();(self.repo/'other.py').write_text('x=1\n');self.s.record_patch();self.assertIn('other.py',self.s.flags['outside_intent'])
        with self.assertRaises(ValueError):self.s.accept()
    def test_repeated_search_is_suppressed(self):
        self.s.action('SEARCH','grep f');self.s.action('SEARCH','grep f');self.assertEqual(self.s.next_action()['reason'],'REPEATED_UNCHANGED_ACTION')
    def test_pass_before_edit_is_stale(self):
        p=self.home/'check.py';p.write_text('from logic import f\nassert f(1)\n')
        self.s.check(p,['R1','R2'],'TARGET',3);self.intent();self.edit();self.assertTrue(any(e['stale'] for e in self.s.evidence if e['type']=='TEST_RESULT'))
        with self.assertRaises(ValueError):self.s.accept()
    def test_valid_patch_requires_fresh_checks_and_diff(self):
        self.intent();self.edit();p=self.home/'check.py';p.write_text('from logic import f\nassert f(0)\nassert not f(-1)\n')
        self.s.check(p,['R1','R2'],'TARGET',3)
        with self.assertRaises(ValueError):self.s.accept()
        self.s.check(p,['R1','R2'],'REGRESSION',3)
        self.s.review_diff();self.s.accept();self.assertEqual(self.s.phase,'PATCH_ACCEPTED');self.assertIsNone(self.s.native_resolved)
    def test_counterexample_blocks_acceptance(self):
        self.intent();self.edit();p=self.home/'check.py';p.write_text('from logic import f\nassert not f(0)\n')
        r=self.s.check(p,['R1'],'TARGET',3);self.assertEqual(r['verification'],'FAIL');self.s.review_diff()
        with self.assertRaises(ValueError):self.s.accept()
    def test_runtime_import_is_environment_unknown(self):
        p=self.home/'check.py';p.write_text('import definitely_missing_egrd_fixture\nassert object()\n')
        r=self.s.check(p,['R1'],'TARGET',3);self.assertEqual(r['type'],'ENVIRONMENT_RESULT');self.assertEqual(r['verification'],'UNKNOWN')
    def test_edited_check_cannot_reuse_pass(self):
        self.intent();self.edit();p=self.home/'check.py';p.write_text('from logic import f\nassert f(0)\n');self.s.check(p,['R1','R2'],'TARGET',3)
        p.write_text('assert False\n');self.s.refresh();self.assertTrue(self.s.evidence[-1]['stale'])
    def test_revision_bound_and_real_rollback(self):
        self.s.max_revisions=0;self.intent();self.edit()
        with self.assertRaises(ValueError):self.s.revise()
        self.s.rollback();self.assertIn('x > 0',(self.repo/'logic.py').read_text());self.assertNotEqual(self.s.phase,'PATCH_ACCEPTED')
    def test_record_patch_cannot_bypass_revision_limit(self):
        self.s.max_revisions=0;self.intent();self.edit();(self.repo/'logic.py').write_text('def f(x):\n    return True\n')
        with self.assertRaises(ValueError):self.s.record_patch()
    def test_budget_reserve_and_unknown_tokens(self):
        self.s.budget['limit_seconds']=10
        self.assertEqual(self.s.next_action()['action'],'SUBMIT');self.assertIsNone(self.s.budget['tokens'])
        p=self.home/'check.py';p.write_text('assert object()\n')
        with self.assertRaises(ValueError):self.s.check(p,['R1'],'TARGET',3)
    def test_mutation_during_test_is_not_pass(self):
        p=self.home/'check.py';p.write_text("from pathlib import Path\nPath('logic.py').write_text('x=2\\n')\nassert object()\n")
        r=self.s.check(p,['R1'],'TARGET',3);self.assertNotEqual(r['verification'],'PASS')
    def test_repeated_check_no_new_subprocess(self):
        p=self.home/'check.py';p.write_text('from logic import f\nassert f(1)\n');a=self.s.check(p,['R1'],'TARGET',3);b=self.s.check(p,['R1'],'TARGET',3)
        self.assertEqual(a['id'],b['id'])
    def test_source_update_after_accept_invalidates_state(self):
        self.intent();self.edit();p=self.home/'check.py';p.write_text('from logic import f\nassert f(0)\n');self.s.check(p,['R1','R2'],'TARGET',3);self.s.check(p,['R1','R2'],'REGRESSION',3);self.s.review_diff();self.s.accept()
        (self.repo/'logic.py').write_text('x=3\n');self.s.refresh();self.assertNotEqual(self.s.phase,'PATCH_ACCEPTED')
if __name__=='__main__':unittest.main()
