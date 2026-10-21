"""Own offline rule/evidence tests,not official task execution."""
import unittest
from .audit import analyze,event_category,draft_admission


class StaticAuditTests(unittest.TestCase):
    def test_real_archived_evidence(self):
        facts=analyze()
        self.assertEqual(facts['overall'],'MIXED_CAUSES')
        self.assertEqual(facts['workspace_hash_count'],1191)
        self.assertTrue(facts['before_after_equal'])

    def test_scope_keywords_alone_are_not_enough(self):
        self.assertEqual(event_category(trace_at_target=True),'UNEXPLAINED_COLLECTION_FAILURE')

    def test_all_four_target_evidence_predicates_required(self):
        flags=dict(target_issue=True,base_absent=True,trace_at_target=True,workspace_proven=True)
        self.assertEqual(event_category(**flags),'TARGET_CAUSED_COLLECTION_FAILURE')
        for k in flags:
            with self.subTest(missing=k):
                self.assertEqual(event_category(**dict(flags,**{k:False})),'UNEXPLAINED_COLLECTION_FAILURE')

    def test_environment_block_dominates_target_failure(self):
        self.assertEqual(draft_admission(['TARGET_CAUSED_COLLECTION_FAILURE','ENVIRONMENT_COLLECTION_FAILURE']),'ENVIRONMENT_BLOCKED')

    def test_target_only_remains_conditional(self):
        self.assertEqual(draft_admission(['TARGET_CAUSED_COLLECTION_FAILURE']),'CONDITIONALLY_ELIGIBLE')
        self.assertEqual(draft_admission(['TARGET_CAUSED_COLLECTION_FAILURE'],independent_validation=True),'CONDITIONALLY_ELIGIBLE')

    def test_unknown_and_integrity_fail_closed(self):
        self.assertEqual(draft_admission(['UNEXPLAINED_COLLECTION_FAILURE']),'STOP_UNEXPLAINED')
        self.assertEqual(draft_admission(['TARGET_BEHAVIOR_FAILURE'],integrity=False),'STOP_INTEGRITY')

    def test_normal_assertions_are_allowed_as_negative_candidates(self):
        self.assertEqual(draft_admission(['TARGET_BEHAVIOR_FAILURE']),'NEGATIVE_BASELINE_CANDIDATE')

    def test_empty_or_all_pass_not_a_discriminating_failure(self):
        self.assertEqual(draft_admission([]),'NOT_EVALUATED')


if __name__=='__main__':unittest.main()
