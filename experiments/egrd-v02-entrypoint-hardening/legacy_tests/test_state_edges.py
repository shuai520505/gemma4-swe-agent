"""Post-freeze consistency regression tests; isolated from pilot package bytes."""
import test_core
import unittest
class StateEdges(unittest.TestCase):
 setUp=test_core.CoreTests.setUp
 support=test_core.CoreTests.support
 intent=test_core.CoreTests.intent
 edit=test_core.CoreTests.edit
 def test_changed_check_invalidates_advisory_acceptance(self):
  self.intent();self.edit();p=self.home/'check.py';p.write_text('from logic import f\nassert f(0)\n')
  self.s.check(p,['R1','R2'],'TARGET',3);self.s.check(p,['R1','R2'],'REGRESSION',3);self.s.review_diff();self.s.accept()
  p.write_text('assert False\n');self.s.refresh();self.assertNotEqual(self.s.phase,'PATCH_ACCEPTED')
 def test_stale_hypothesis_does_not_recommend_edit(self):
  self.support();(self.repo/'logic.py').write_text('def f(x):\n    return x != 0\n')
  self.assertNotEqual(self.s.next_action()['action'],'EDIT')
 def test_policy_advances_target_regression_diff_submit(self):
  self.intent();self.edit();self.assertEqual(self.s.next_action()['action'],'RUN_TARGETED_TEST')
  p=self.home/'check.py';p.write_text('from logic import f\nassert f(0)\nassert not f(-1)\n')
  self.s.check(p,['R1','R2'],'TARGET',3);self.assertEqual(self.s.next_action()['action'],'RUN_REGRESSION_TEST')
  self.s.check(p,['R1','R2'],'REGRESSION',3);self.assertEqual(self.s.next_action()['reason'],'CURRENT_DIFF_REVIEW_REQUIRED')
  self.s.review_diff();self.s.accept();self.assertEqual(self.s.next_action()['action'],'SUBMIT')
 def test_policy_counterexample_recommends_revision(self):
  self.intent();self.edit();p=self.home/'check.py';p.write_text('from logic import f\nassert not f(0)\n')
  self.s.check(p,['R1'],'TARGET',3);self.assertEqual(self.s.next_action()['action'],'REVISE_PATCH')
 def test_staged_edit_is_in_reviewed_diff(self):
  self.intent();self.edit()
  import subprocess
  subprocess.run(['git','add','logic.py'],cwd=self.repo,check=True)
  self.assertIn('+    return x >= 0',self.s.review_diff()['diff'])
 def test_untracked_patch_cannot_be_accepted_as_reviewed(self):
  self.support();self.s.intent(dict(files=['new.py'],regions=['module'],behavior='new helper',requirements=['R1','R2'],support=[self.s.evidence[0]['id']],regressions=['negative'],preserve='negative',discriminating_test='new helper works'))
  (self.repo/'new.py').write_text('value=1\n');self.s.record_patch()
  p=self.home/'check.py';p.write_text('from new import value\nassert value == 1\n')
  self.s.check(p,['R1','R2'],'TARGET',3);self.s.check(p,['R1','R2'],'REGRESSION',3);self.s.review_diff()
  with self.assertRaises(ValueError):self.s.accept()
if __name__=='__main__':unittest.main()
