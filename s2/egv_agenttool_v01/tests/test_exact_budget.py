"""Actual300-second native cancellation and real60-count shared tool boundary."""
import json
import os
from pathlib import Path
import unittest
from harness_v2.evidence import read_events
from .runner_cases import exercise


class ExactBudgetTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_sixty_counted_tools_across_AgentTool_boundary(self):
        root=Path(os.environ['S2_CPU_EVIDENCE'])/'exact_budget'
        r=await exercise('exact_budget',root,native=True,research_observer=True)
        self.assertEqual(r['counted_tools'],60)
        self.assertTrue(r['explicit_submit'])
        self.assertFalse(r['closed_loop'])
        rows=[e for e in read_events(root/'nested_audit.jsonl') if e['kind']=='tool_end']
        denied=[e for e in rows if isinstance(e['result'],dict) and e['result'].get('error_type')=='BudgetExceeded']
        self.assertTrue(any(e['actor']=='egv_verifier' for e in denied))
        self.assertTrue(any(e['actor']=='main_coding_agent' for e in denied))
        self.assertTrue(all(e['counted_tools']==60 for e in denied))
        self.assertGreater(r['actual_tool_events'],60)

    async def test_actual_300_second_native_deadline_cancels_child_request(self):
        root=Path(os.environ['S2_CPU_EVIDENCE'])/'exact_deadline'
        r=await exercise('exact_deadline',root,native=True,research_observer=True)
        self.assertTrue(r['child_HTTP_cancelled'])
        self.assertIn('session timeout (5',r['error'])
        native=json.loads((root/'native_boundary.json').read_text())
        self.assertGreaterEqual(native['agent_seconds'],299)
        self.assertLess(native['agent_seconds'],315)
        self.assertTrue(r['HTTP']['passed'],r['HTTP'])
        self.assertIsNone(r['HTTP']['rows'][-1]['usage'])
        self.assertTrue(json.loads((root/'cleanup.json').read_text())['complete'])
