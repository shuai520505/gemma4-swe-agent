import json,os,sys,tempfile,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
class ProcessTests(unittest.TestCase):
 def run_case(self,mode,role='session'):
  self.assertTrue((D/'supervision.py').exists(),'Versioned supervisor adapter missing')
  from supervision import supervise
  with tempfile.TemporaryDirectory() as tmp:
   return supervise([sys.executable,str(D/'worker_contract_fixture.py'),tmp,mode],tmp,outer_seconds=20,stage_caps={},poll_seconds=.05,terminate_grace=.2,cwd=D,role=role)
 def test_completed(self):self.assertTrue(self.run_case('normal')['allow_next_run'])
 def test_agent_timeout_has_clean_worker(self):self.assertEqual(self.run_case('agent_timeout')['classification'],'AGENT_TIMEOUT')
 def test_cleanup_failure_stops(self):self.assertEqual(self.run_case('cleanup_failure')['classification'],'CLEANUP_FAILED')
 def test_abnormal_worker_exit(self):self.assertEqual(self.run_case('crash')['classification'],'WORKER_ABNORMAL_EXIT')
 def test_missing_result(self):self.assertEqual(self.run_case('missing')['classification'],'RESULT_MISSING')
 def test_native_failure(self):self.assertEqual(self.run_case('native_failure')['classification'],'NATIVE_EVALUATION_FAILED')
 def test_aggregate_result_no_fake_official_result(self):self.assertEqual(self.run_case('aggregate',role='aggregate')['classification'],'AGGREGATE_COMPLETED')
if __name__=='__main__':unittest.main()
