import unittest
from cure.contract_state import ContractState, ContractBook, Evidence


class StateTests(unittest.TestCase):
    def test_evidence_is_bounded_and_content_addressed(self):
        c = ContractState('a', 'entry point remains compatible')
        for i in range(20): c.update(Evidence.tool_result('x' * 1000 + str(i), str(i)))
        self.assertEqual(len(c.evidence), 8); self.assertEqual(c.dropped_evidence, 12)
        self.assertEqual(len(c.evidence[-1].summary), 400)
        self.assertEqual(len(c.evidence[-1].digest), 64)

    def test_claim_cannot_become_verified(self):
        c = ContractState('a', 'injection honored')
        for kind in ('model_inference', 'unconfirmed_hypothesis'):
            with self.assertRaises(ValueError): c.update(Evidence(kind, 'probably fine', 'model'), uncertainty=.1, ready_to_edit=True)
            with self.assertRaises(ValueError): c.update(Evidence(kind, 'passes', 'model'), verification_status='passed')
        self.assertEqual(c.verification_status, 'unverified'); self.assertFalse(c.evidence)

    def test_zero_exit_read_is_not_verification(self):
        c = ContractState('a', 'behavior')
        with self.assertRaises(ValueError): c.update(Evidence.tool_result('ok', 'r', exit_code=0), verification_status='passed')
        c.update(Evidence.tool_result('ok', 'v', role='verification', exit_code=0), verification_status='passed')
        self.assertEqual(c.verification_status, 'passed')

    def test_contradiction_reopens_contract(self):
        c = ContractState('a', 'caller')
        c.update(Evidence.tool_result('definition', '1'), inspected=True, ready_to_edit=True, uncertainty=.1)
        c.update(Evidence.tool_result('ImportError', '2', role='probe', exit_code=1), contradiction=True)
        self.assertFalse(c.inspected); self.assertFalse(c.ready_to_edit)
        self.assertGreaterEqual(c.uncertainty, .9)

    def test_invalid_input_and_contract_count(self):
        for u in (-1, float('nan'), True):
            with self.assertRaises(ValueError): ContractState('a', 'b', uncertainty=u)
        with self.assertRaises(ValueError): ContractBook([])
        with self.assertRaises(ValueError): ContractState('a', 'x' * 601)
        with self.assertRaises(ValueError): Evidence('observation', 'unreferenced', '')
