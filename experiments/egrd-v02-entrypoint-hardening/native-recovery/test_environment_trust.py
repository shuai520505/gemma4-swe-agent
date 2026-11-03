"""Regression of observed Native failures; no HTTP service or substitute evaluator."""
import json,sys,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
D=Path(__file__).resolve().parents[1];sys.path.insert(0,str(D))
from result_contract import native_execution_check

class NetworkTrustTests(unittest.TestCase):
 def fixture(self,xml):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);p=Path(tmp.name)
  (p/'NATIVE_RESULT.json').write_text(json.dumps(dict(status='SUCCESS',resolved=False,test_exit_code=1)))
  (p/'native-junit-0.xml').write_text(xml)
  return p/'NATIVE_RESULT.json'
 def test_actual_cpu02_network_failures_alone_cannot_pass_trust(self):
  # Remove nothing from official evaluation: this owned XML regression tests
  # the classifier on four already observed raw failure records in isolation.
  original=ET.parse(D/'cpu02-evidence/worker/trusted/native-junit-0.xml').getroot()
  out=ET.Element('testsuites');suite=ET.SubElement(out,'testsuite')
  for c in original.findall('.//testcase'):
   if c.find('failure') is not None:suite.append(c)
  self.assertEqual(len(suite),4)
  r=native_execution_check(self.fixture(ET.tostring(out,encoding='unicode')))
  self.assertFalse(r['passed'],'Four real sandbox EACCES failures were classified as ordinary repair failures')
  self.assertEqual(r['infrastructure_failure_cases'],4)
 def test_normal_behavioral_failure_is_allowed(self):
  r=native_execution_check(self.fixture('<testsuites><testsuite><testcase name="target"><failure>AssertionError: expected 2 got 1</failure></testcase></testsuite></testsuites>'))
  self.assertTrue(r['passed']);self.assertEqual(r.get('infrastructure_failure_cases',0),0)
 def test_errno_text_without_network_exception_is_not_automatic_network_diagnosis(self):
  r=native_execution_check(self.fixture('<testsuites><testsuite><testcase name="target"><failure>AssertionError: expected text [Errno 13] Permission denied</failure></testcase></testsuite></testsuites>'))
  self.assertTrue(r['passed'])
 def test_setup_errors_do_not_count_as_executed_test_bodies(self):
  r=native_execution_check(D/'cpu02-evidence/worker/trusted/NATIVE_RESULT.json')
  self.assertEqual(r['executed'],135,'131 passes and4 failures executed bodies;187 setup errors did not')
if __name__=='__main__':unittest.main()
