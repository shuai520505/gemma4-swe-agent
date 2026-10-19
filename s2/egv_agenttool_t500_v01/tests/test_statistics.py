import unittest
from s2.egv_agenttool_t500_v01.analyze import summarize,mechanism


class StatisticsTests(unittest.TestCase):
    def test_missing_and_unknown_are_not_confirmed_failures(self):
        ids=[str(i) for i in range(8)]
        rows={('0','A'):dict(started=True,infrastructure_passed=True,official_result=dict(resolved=False)),
              ('0','B'):dict(started=True,infrastructure_passed=True,official_result=dict(resolved=True)),
              ('1','A'):dict(started=True,infrastructure_passed=False,official_result=dict(resolved=False))}
        r=summarize(rows,ids)
        self.assertEqual(r['auditable_pairs'],1)
        self.assertEqual(r['B_only_resolved'],1)
        self.assertIsNone(r['full_experiment_resolution_rates'])
        self.assertEqual(r['task_pairs'][1]['A'],'unknown')
        self.assertEqual(r['task_pairs'][1]['B'],'not_run')
        self.assertIsNone(mechanism([])['closed_loop_rate'])

    def test_all_pairs_and_unhandled_counterevidence(self):
        ids=[str(i) for i in range(8)]
        rows={(i,a):dict(infrastructure_passed=True,official_result=dict(resolved=a=='B')) for i in ids for a in ('A','B')}
        r=summarize(rows,ids)
        self.assertTrue(r['complete_eight_task_experiment'])
        self.assertEqual(r['full_experiment_resolution_rates'],dict(A=0.,B=1.))
        m=mechanism([dict(actionable=True,evidence_level=1,discovery_tool_pointer='raw:1',delivery_tool_pointer='raw:2')])
        self.assertEqual(m['handling_rate'],0.)
        self.assertEqual(m['closed_loop_rate'],0.)
