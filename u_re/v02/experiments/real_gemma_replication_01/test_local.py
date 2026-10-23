"""Offline external-authorization and exact-payload checks, no GPU/model calls."""
import json,unittest
from . import notebook as n

class Boundaries(unittest.TestCase):
    def test_original_raw_CPU_acceptance_and_shared_ZIP_match(self):
        lock,proof=n.verify_shared();self.assertEqual(proof['payload_sha256'],n.PAYLOAD_SHA);self.assertEqual(len(lock['tasks']),4)
    def test_current_grant_is_new_and_not_historical_false_record(self):
        a=json.loads((n.HERE/'GPU_AUTHORIZATION_RECORD.json').read_bytes())
        self.assertTrue(a['GPU_authorized']);self.assertEqual(a['execution_experiment_id'],n.ID)
        self.assertFalse(json.loads((n.PRODUCTION/'GPU_AUTHORIZATION.json').read_bytes())['GPU_authorized'])
        self.assertEqual(a['max_Agent_sessions'],8);self.assertFalse(a['retries_authorized'])
    def test_frozen_order_and_batch_membership(self):
        a=json.loads((n.HERE/'GPU_AUTHORIZATION_RECORD.json').read_bytes())
        self.assertEqual([r['arm'] for r in a['frozen_order']],list('ABBAABBA'))
        self.assertEqual([r['batch'] for r in a['frozen_order']],[1]*4+[2]*4)
    def test_save_precheck_failure_cannot_reach_SDK_or_network(self):
        from unittest.mock import patch
        with patch.object(n,'validate',side_effect=ValueError('OWNED_PAYLOAD_INVALID')):
            with self.assertRaisesRegex(ValueError,'OWNED_PAYLOAD_INVALID'):n.launch(1)
    def test_controller_rejects_no_human_authorization(self):
        with self.assertRaises(AssertionError):n.controller(1).checked_authorization({}, {})
    def test_final_GPU_notebook_calls_accepted_entry_with_exact_external_grant(self):
        self.assertTrue(n.validate(1))

if __name__=='__main__':unittest.main()
