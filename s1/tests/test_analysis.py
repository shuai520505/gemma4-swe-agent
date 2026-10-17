"""Offline analysis tests; these do not alter or authorize the frozen GPU runner."""
import unittest
from s1.analyze import summarize


class AnalysisTests(unittest.TestCase):
    def plan(self):
        return dict(experiment_id='analysis_fixture',batches=dict(smoke=[dict(index=1,instance_id='smoke',arm='control')],
            screen_a=[dict(index=2,instance_id='new',arm='control'),dict(index=3,instance_id='new',arm='e1_output8192')]))

    def result(self,index,arm,status,infra=True,task='new'):
        return dict(index=index,arm=arm,instance_id=task,audit=dict(outcome=dict(status=status),infrastructure_passed=infra))

    def test_partial_pair_has_no_rate_or_primary(self):
        r=summarize(self.plan(),[self.result(2,'control','resolved')])
        self.assertIsNone(r['primary_resolved_difference'])
        self.assertIsNone(r['full_resolution_rates']['control'])
        self.assertEqual(r['counts']['e1_output8192']['not_run'],1)

    def test_unknown_not_a_loss(self):
        r=summarize(self.plan(),[self.result(2,'control','unknown',False),self.result(3,'e1_output8192','resolved')])
        self.assertEqual(r['discordant']['e1_only'],0)
        self.assertIsNone(r['primary_resolved_difference'])

    def test_smoke_excluded_and_complete_pair_difference(self):
        r=summarize(self.plan(),[self.result(1,'control','resolved',task='smoke'),
            self.result(2,'control','failed'),self.result(3,'e1_output8192','resolved')])
        self.assertEqual(r['primary_resolved_difference'],1)
        self.assertEqual(r['counts']['control']['resolved'],0)
        self.assertFalse(r['sufficient_for_S1_freeze'])

    def test_duplicate_or_drifted_identity_rejected(self):
        row=self.result(2,'control','resolved')
        with self.assertRaises(ValueError):summarize(self.plan(),[row,row])
        with self.assertRaises(ValueError):summarize(self.plan(),[self.result(2,'e1_output8192','resolved')])


if __name__=='__main__':unittest.main()
