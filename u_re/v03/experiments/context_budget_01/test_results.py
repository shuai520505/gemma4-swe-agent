import json,unittest,zipfile
from pathlib import Path
from .common import HERE,ROOT,sha
class ActualResultsTests(unittest.TestCase):
    def test_source_edits_exclude_workspace_initialization(self):
        rows=json.loads((HERE/'AGENT_BEHAVIOR_METRICS.json').read_bytes())['runs']
        self.assertEqual([m['production_edit_operations'] for m in rows],[2,2,3,0])
        self.assertFalse(rows[3]['ever_production_modified'])
    def test_native_and_guard_independent(self):
        native=json.loads((HERE/'NATIVE_RESULTS.json').read_bytes())['runs']
        metric=json.loads((HERE/'AGENT_BEHAVIOR_METRICS.json').read_bytes())['runs']
        self.assertEqual([r['resolved'] for r in native],[True,True,False,False])
        self.assertEqual([r['context_guard_triggered'] for r in metric],[True,False,False,True])
        self.assertTrue(metric[0]['context_guard_events'][0]['correct_production_patch_at_guard_supported_by_final_native'])
    def test_cancelled_usage_is_not_zero(self):
        metric=json.loads((HERE/'AGENT_BEHAVIOR_METRICS.json').read_bytes())['runs'][2]
        self.assertFalse(metric['usage_complete']);self.assertEqual(metric['actual_HTTP_requests'],40);self.assertEqual(metric['actual_HTTP_responses'],39)
        self.assertIsNone(metric['request_usage'][-1]['usage'])
    def test_actual_caps_and_received_finish_reasons(self):
        metric=json.loads((HERE/'AGENT_BEHAVIOR_METRICS.json').read_bytes())['runs']
        self.assertEqual([m['max_output_tokens'] for m in metric],[16384,8192,8192,16384])
        self.assertGreater(metric[1]['max_received_prompt_tokens'],15360)
        self.assertGreater(metric[2]['max_received_prompt_tokens'],15360)
        self.assertEqual(sum(m['output_truncated_requests'] for m in metric),0)
        self.assertEqual(sum(m['malformed_tool_arguments'] for m in metric),0)
if __name__=='__main__':unittest.main()
