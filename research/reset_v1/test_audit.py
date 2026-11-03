import json,unittest
from pathlib import Path
from paired_statistics import cp,paired

HERE=Path(__file__).resolve().parent
class AuditTests(unittest.TestCase):
    def test_exact_boundaries(self):
        self.assertAlmostEqual(cp(0,10)[1],1-.025**.1)
        self.assertAlmostEqual(cp(10,10)[0],.025**.1)
        self.assertEqual(cp(0,0),[None,None])
    def test_paired_null_and_symmetry(self):
        self.assertEqual(paired(0,0,0,0)['absolute_difference'],None)
        self.assertEqual(paired(5,0,0,5)['mcnemar_exact_p'],1)
        self.assertAlmostEqual(paired(0,6,0,0)['mcnemar_exact_p'],.03125)
        a=paired(2,4,1,3);b=paired(2,1,4,3)
        self.assertAlmostEqual(a['absolute_difference'],-b['absolute_difference'])
        self.assertAlmostEqual(a['difference_exact_conservative95'][0],-b['difference_exact_conservative95'][1])
    def test_unique_sessions(self):
        d=json.loads((HERE/'HISTORICAL_EXPERIMENT_DATASET.json').read_text())['sessions']
        self.assertEqual(len(d),len({s['session_id'] for s in d}))
        self.assertEqual(len(d),len({(s['evidence']['result_sha256'],s['evidence']['trace_sha256']) for s in d}))
    def test_no_cpu_replay_in_gemma(self):
        d=json.loads((HERE/'HISTORICAL_EXPERIMENT_DATASET.json').read_text())['sessions']
        self.assertFalse(any('CPU_evidence' in s['evidence']['result_member'] for s in d))
    def test_cohorts(self):
        c=json.loads((HERE/'TASK_COHORT_LOCK.json').read_text());a=c['diagnostic_pilot'];b=c['confirmation']
        ids=[r['instance_id'] for r in a+b]
        self.assertEqual(len(a),6);self.assertEqual(len(b),16)
        self.assertEqual(len(ids),len(set(ids)))
        self.assertFalse(set(ids)&set(c['excluded_exposed_task_ids']))
        self.assertTrue(all(x['snapshot_sha256'] is None for x in a+b))
    def test_package_parity(self):
        d=json.loads((HERE/'CONFIGURATION_PARITY.json').read_text())
        rows=[r for r in d['rows'] if r['mode']=='common_public_defaults']
        self.assertEqual(rows[0]['generation'],rows[1]['generation'])
        self.assertEqual(rows[0]['base_tools'],rows[1]['base_tools'])
        self.assertEqual(d['real_model_calls'],0)
if __name__=='__main__':unittest.main()
