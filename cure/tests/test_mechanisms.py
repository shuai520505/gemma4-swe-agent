import json
from pathlib import Path
import tempfile
import unittest
from cure.mechanisms import run_case


class MechanismTests(unittest.TestCase):
    def test_changed_investigation_with_same_scripted_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = run_case('interface', 'B', Path(tmp) / 'B')
            c = run_case('interface', 'C', Path(tmp) / 'C')
            self.assertTrue(b['verification_passed']); self.assertTrue(c['verification_passed'])
            self.assertEqual(c['actions'][2:5], ['probe', 'inspect', 'edit'])
            self.assertEqual(c['tools_used'] - b['tools_used'], 1)

    def test_extra_investigation_can_lose_under_tight_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = run_case('interface', 'B', Path(tmp) / 'B', tool_limit=6)
            c = run_case('interface', 'C', Path(tmp) / 'C', tool_limit=6)
            self.assertTrue(b['verification_passed'])
            self.assertFalse(c['verification_passed']); self.assertFalse(c['patch_ready'])

    def test_regression_detects_bad_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = run_case('old_behavior', 'C', Path(tmp) / 'C', bad_edit=True)
            self.assertFalse(c['verification_passed'])
            self.assertGreater(c['contradictions'], 0)
