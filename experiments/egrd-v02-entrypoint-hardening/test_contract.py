import hashlib,json,tempfile,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
def write(p,r):p.write_text(json.dumps(r));return hashlib.sha256(p.read_bytes()).hexdigest()
class ContractTests(unittest.TestCase):
 def fixture(self,d,classification='AGENT_COMPLETED',cleanup=True,native=True):
  sid='cpu-owned';c=write(d/'CLEANUP.json',dict(schema='EGRD_CLEANUP_V2',session_id=sid,complete=cleanup,records=[]))
  n=write(d/'NATIVE_RESULT.json',dict(resolved=False,status='SUCCESS',test_exit_code=1)) if native else None
  (d/'native-junit-0.xml').write_text('<testsuites><testsuite><testcase name="control"/><testcase name="target"><failure/></testcase></testsuite></testsuites>')
  r=write(d/'SESSION_RESULT.json',dict(schema='EGRD_SESSION_V2',session_id=sid,failure_classification=classification,native_result_path='NATIVE_RESULT.json',native_result_sha256=n))
  write(d/'worker_done.json',dict(schema='EGRD_DONE_V2',session_id=sid,exit_code=0,session_result_sha256=r,cleanup_sha256=c,cleanup_complete=cleanup,native_result_sha256=n))
 def assess(self,d,exit=0,controller=None):
  self.assertTrue((D/'result_contract.py').exists(),'Worker result contract adapter missing')
  from result_contract import assess
  return assess(d,dict(process_exit_code=exit,process_tree_stopped=True,controller_error=controller),role='session')
 def test_normal_worker_native_false_is_ordinary_repair_failure(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d);r=self.assess(d);self.assertEqual(r['classification'],'AGENT_COMPLETED');self.assertTrue(r['allow_next_run']);self.assertFalse(r['native_resolved'])
 def test_agent_timeout_is_not_worker_timeout(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d,'AGENT_TIMEOUT');r=self.assess(d);self.assertTrue(r['allow_next_run']);self.assertEqual(r['classification'],'AGENT_TIMEOUT')
 def test_nonzero_worker_exit(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d);self.assertEqual(self.assess(d,2)['classification'],'WORKER_ABNORMAL_EXIT')
 def test_worker_outer_timeout(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d);self.assertEqual(self.assess(d,-1,'outer_timeout')['classification'],'WORKER_TIMEOUT')
 def test_cleanup_failure(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d,cleanup=False);r=self.assess(d);self.assertEqual(r['classification'],'CLEANUP_FAILED');self.assertFalse(r['allow_next_run'])
 def test_missing_result(self):
  with tempfile.TemporaryDirectory() as t:self.assertEqual(self.assess(Path(t))['classification'],'RESULT_MISSING')
 def test_native_result_missing(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d,native=False);self.assertEqual(self.assess(d)['classification'],'NATIVE_EVALUATION_FAILED')
 def test_receipt_hash_drift(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d);write(d/'CLEANUP.json',dict(complete=True));self.assertEqual(self.assess(d)['classification'],'RESULT_CONTRACT_INVALID')
 def test_cleanup_failure_retained_on_nonzero_worker_exit(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d,cleanup=False)
   done=json.loads((d/'worker_done.json').read_bytes());done['exit_code']=2;write(d/'worker_done.json',done)
   self.assertEqual(self.assess(d,2)['classification'],'CLEANUP_FAILED')
 def test_native_setup_errors_are_not_ordinary_repair_failure(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d)
   (d/'native-junit-0.xml').write_text('<testsuites><testsuite><testcase name="x"><error message="missing fixture"/></testcase></testsuite></testsuites>')
   self.assertEqual(self.assess(d)['classification'],'NATIVE_EVALUATION_FAILED')
 def test_native_junit_missing_stops(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d);(d/'native-junit-0.xml').unlink()
   self.assertEqual(self.assess(d)['classification'],'NATIVE_EVALUATION_FAILED')
 def test_native_empty_junit_stops(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d);(d/'native-junit-0.xml').write_text('<testsuites/>')
   self.assertEqual(self.assess(d)['classification'],'NATIVE_EVALUATION_FAILED')
 def test_native_all_skipped_stops(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);self.fixture(d);(d/'native-junit-0.xml').write_text('<testsuites><testsuite><testcase name="x"><skipped/></testcase></testsuite></testsuites>')
   self.assertEqual(self.assess(d)['classification'],'NATIVE_EVALUATION_FAILED')
if __name__=='__main__':unittest.main()
