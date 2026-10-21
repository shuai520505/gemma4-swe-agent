import json
import unittest
from u_re.v01.experiments.fastapi_pilot_01.reconciliation_01.query import HERE
from u_re.v01.experiments.fastapi_pilot_01.reconciliation_01.report import classify


class EvidenceTests(unittest.TestCase):
    def test_absence_signals_cannot_establish_rejection(self):
        for d in ({'exists':None},{'exists':False},{'http_status':403,'complete_paging':True},
                  {'error':'JSONDecodeError'},{'accepted_version':None}):
            self.assertEqual(classify(d),'SAVE_STATUS_UNKNOWN')

    def test_resource_existence_is_not_execution_success(self):
        self.assertEqual(classify({'exists':True}),'SAVE_EXISTS_EXECUTION_UNKNOWN')
        self.assertEqual(classify({'exists':True,'accepted_version':1,'source_matches_original':True}),'SAVE_ACCEPTED_CONFIRMED')

    def test_actual_ledger_is_readonly_and_bounded(self):
        d=json.loads((HERE/'READONLY_QUERY_LEDGER.json').read_bytes())
        self.assertTrue(d['identity_confirmed']);self.assertTrue(d['credential_files_unchanged'])
        self.assertEqual(len(d['HTTP']),5);self.assertEqual(d['SaveKernel_requests'],0)
        self.assertEqual({x['operation'] for x in d['HTTP']},{'IntrospectToken','ListKernels','GetKernel'})
        self.assertEqual(d['pagination']['unique_rows'],170);self.assertEqual(d['pagination']['pages'],2)
        self.assertTrue(d['pagination']['complete']);self.assertFalse(d['pagination']['exact_matches'])
        self.assertEqual([x['http_status'] for x in d['HTTP']],[200,200,200,200,403])
        self.assertTrue(d['control_private_read_confirmed'])

    def test_output_and_task_results_are_null_without_version(self):
        d=json.loads((HERE/'VERSION_OUTPUT_MANIFEST.json').read_bytes())
        for k in ('accepted_version','version_created_at','run_status','outputs','TaskResult','JUnit','cleanup','actual_platform_execution_count'):
            self.assertIsNone(d[k])
        self.assertEqual(d['output_requests'],0);self.assertEqual(d['downloads'],0)
        self.assertEqual(d['confirmed_native_baselines'],0)


if __name__=='__main__':unittest.main()
