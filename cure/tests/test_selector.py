import tempfile
import unittest
from cure.action_selector import Budget, Checklist, select
from cure.contract_state import ContractBook, ContractState, Evidence


class SelectorTests(unittest.TestCase):
    def test_observation_changes_edit_to_inspect_at_same_budget(self):
        c = ContractState('r', 'public entry', proposed_probe='import caller')
        c.update(Evidence.tool_result('located and read', '1'), located=True, inspected=True, ready_to_edit=True, uncertainty=.1)
        book = ContractBook([c]); budget = Budget(100, 10)
        self.assertEqual(select(book, budget).action, 'edit')
        c.update(Evidence.tool_result('caller import fails', '2', role='probe', exit_code=1), contradiction=True)
        self.assertEqual(select(book, budget).action, 'inspect')
        self.assertEqual({o.action for o in select(book, budget).options}, {'locate', 'inspect', 'probe', 'edit', 'verify', 'submit'})

    def test_priority_responds_to_impact(self):
        a = ContractState('low', 'minor', impact=.1); b = ContractState('high', 'critical', impact=.9)
        self.assertEqual(select(ContractBook([a, b]), Budget(100, 10)).contract_id, 'high')

    def test_probe_requires_a_specific_proposal(self):
        c = ContractState('r', 'x', proposed_probe='boundary check')
        c.update(Evidence.tool_result('read', '1'), located=True, inspected=True)
        self.assertEqual(select(ContractBook([c]), Budget(100, 10)).action, 'probe')

    def test_exhaustion_never_invokes_another_tool(self):
        for budget in (Budget(0, 10), Budget(100, 0)):
            d = select(ContractBook([ContractState('r', 'x')]), budget)
            self.assertFalse(d.feasible); self.assertIn('exhausted', d.reason)

    def test_low_budget_preserves_available_patch(self):
        d = select(ContractBook([ContractState('r', 'x')], patch_ready=True), Budget(3, 1))
        self.assertEqual(d.action, 'submit'); self.assertIn('unresolved', d.reason)

    def test_checklist_does_not_reorder_after_contradiction(self):
        policy = Checklist(); book = ContractBook([ContractState('r', 'x')])
        policy.index = 3
        book.contracts[0].update(Evidence.tool_result('bad', 'x'), contradiction=True)
        self.assertEqual(policy.choose(book, Budget(100, 10)).action, 'edit')
