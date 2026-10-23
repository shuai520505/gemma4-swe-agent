"""Offline analysis checks on owned cases and immutable prior GPU03 evidence."""
import copy,json,unittest,zipfile
from pathlib import Path
from .notebook import ROOT,HERE
from .results import paired,enrich,_assertion_command,git_destination

class Metrics(unittest.TestCase):
    def test_quoted_unicode_diagnostic_filename_is_not_production(self):
        path=git_destination(r'diff --git "a/\343\200\214owned.py\343\200\215" "b/\343\200\214owned.py\343\200\215"')
        self.assertEqual(path,'\u300cowned.py\u300d');self.assertFalse(path.startswith('fastapi/'))
    def test_unknown_native_never_becomes_neither_or_false(self):
        p=paired([dict(instance_id='owned',arm='A',resolved=False)],['owned'])
        self.assertEqual(p['counts']['Unknown'],1);self.assertIsNone(p['pairs'][0]['Action_First'])
    def test_both_direction_discordances_retained(self):
        r=[dict(instance_id='one',arm='A',resolved=True),dict(instance_id='one',arm='B',resolved=False),dict(instance_id='two',arm='A',resolved=False),dict(instance_id='two',arm='B',resolved=True)]
        p=paired(r,['one','two']);self.assertEqual((p['counts']['A_Only'],p['counts']['B_Only']),(1,1))
    def test_print_only_script_not_a_supported_assertion(self):
        self.assertFalse(_assertion_command('python3 owned.py',{'owned.py':'print(3)'}))
        self.assertTrue(_assertion_command('python3 owned.py',{'owned.py':'assert 3 > 0'}))
    def test_historical_native_success_and_context_stop_remain_independent(self):
        prior=ROOT/'u_re/v01/experiments/action_priority_01/real_gemma_abba03'
        raw=json.loads((prior/'RAW_ARCHIVES.json').read_bytes())['GPU03']['private_path']
        metrics=json.loads((prior/'AGENT_BEHAVIOR_METRICS.json').read_bytes())['runs']
        results=json.loads((prior/'ABBA_RESULTS.json').read_bytes())['runs']
        with zipfile.ZipFile(raw) as z:
            m=enrich(z,copy.deepcopy(metrics[3]),copy.deepcopy(results[3]))
            self.assertTrue(m['context_guard_triggered']);self.assertEqual(m['failure_classification'],'SUCCESSFUL_REPAIR')
            self.assertTrue(m['context_guard_events'][0]['correct_production_patch_at_guard_supported_by_final_native'])
            d=enrich(z,copy.deepcopy(metrics[0]),copy.deepcopy(results[0]))
            self.assertFalse(d['ever_production_modified']);self.assertTrue(d['diagnostic_only_patch'])
            self.assertIsNone(d['first_observed_applicable_patch_seconds'])

if __name__=='__main__':unittest.main()
