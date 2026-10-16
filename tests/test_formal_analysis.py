import unittest
from experiments.analyze_formal_pair_01 import aggregate,token_fields


class FormalAnalysisTests(unittest.TestCase):
    def test_native_zero_placeholder_does_not_erase_observable_tokens(self):
        fields=token_fields({'total_tokens':0},[{'event':{'usage_metadata':{'total_token_count':123}}}])
        self.assertEqual(fields['native_total_tokens'],0)
        self.assertIsNone(fields['total_tokens'])
        self.assertEqual(fields['observed_native_usage_tokens'],123)

    def rows(self):
        return [dict(instance_id=str(i),arm=arm,status='resolved' if arm=='v1' else 'failed',
            auditable=True,phase2_execution=True,controller_error=None,counters_censored=False,
            llm_calls=10,tool_calls=8,total_tokens=100,duration_seconds=2,official_duration_seconds=1,
            patch_application_confirmed=True) for i in range(4) for arm in ('v0','v1')]

    def test_unknown_suppresses_both_full_rates_and_paired_conclusion(self):
        rows=self.rows();rows[-1].update(status='unknown',auditable=False,llm_calls=None,total_tokens=None,counters_censored=True)
        r=aggregate(rows)
        self.assertFalse(r['full_comparison_auditable'])
        self.assertIsNone(r['arms']['v0']['resolution_rate'])
        self.assertIsNone(r['arms']['v1']['resolution_rate'])
        self.assertEqual(r['arms']['v1']['llm_calls']['observed_n'],3)
        self.assertEqual(r['arms']['v1']['llm_calls']['mean'],10)
        self.assertIsNone(r['paired_wins'])

    def test_known_verdict_without_trace_is_not_complete_comparison(self):
        rows=self.rows();rows[0]['auditable']=False
        self.assertIsNone(aggregate(rows)['paired_wins'])

    def test_complete_four_pair_results_allow_only_exploratory_metrics(self):
        r=aggregate(self.rows())
        self.assertEqual(r['paired_wins'],{'v1':4})
        self.assertEqual(r['arms']['v1']['resolution_rate'],1)
        self.assertIn('Exploratory',r['interpretation'])


if __name__=='__main__':unittest.main()
