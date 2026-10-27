"""Offline endpoint and evidence tests; no model or platform mutation."""
import json
from pathlib import Path
import unittest
from .prepare import HERE,PRIVATE,sha
from .inspect_results import transport,lines
from .finalize_results import primary,ARCHIVE_SHA


class Results(unittest.TestCase):
    def test_missing_submission_cannot_be_rescued_by_green_or_unknown_checks(self):
        self.assertFalse(primary(False,True,True,True,True))
        self.assertFalse(primary(False,None,None,None,None))
        self.assertIsNone(primary(True,True,True,True,None))
        self.assertIsNone(primary(None,None,None,None,None))
        self.assertTrue(primary(True,True,True,True,True))

    def test_unobserved_usage_is_null_and_not_vacuously_complete(self):
        r=transport([])
        self.assertFalse(r['usage_complete'])
        self.assertIsNone(r['observed_response_usage']['total_tokens'])
        self.assertIsNone(r['received_HTTP_latency_seconds'])

    def test_received_usage_does_not_impute_canceled_or_rejected_generation(self):
        for arm,n,good in (('A',23,22),('B',21,20)):
            p=PRIVATE/'verified-output/execution'/arm/'model_transport/http_wire.jsonl'
            rows=lines(p.read_bytes());r=transport(rows)
            self.assertEqual(r['requests'],n);self.assertFalse(r['usage_complete'])
            self.assertEqual(sum(s==200 for s in r['HTTP_statuses']),good)
        c=json.loads((HERE/'COST_COMPARISON.json').read_bytes())
        self.assertEqual(c['total_observed_received_usage']['total_tokens'],444878)
        self.assertEqual(c['canceled_inflight_requests'],1);self.assertEqual(c['HTTP_400'],1)

    def test_submitted_patch_and_fallback_are_distinct(self):
        for arm in 'AB':
            r=json.loads((HERE/f'SESSION_{arm}_RESULT.json').read_bytes())
            self.assertFalse(r['patch_submitted']);self.assertFalse(r['primary_defensible_submitted_repair'])
            self.assertIsNone(r['submitted_patch_sha256']);self.assertIsNone(r['post_edit_target_probe_passed'])
            self.assertEqual(len(r['unsubmitted_fallback_sha256']),64)
            self.assertIsNone(r['official_native_resolved']);self.assertIsNone(r['canonical_swebench_resolved'])
        ev=json.loads((HERE/'TRUSTED_EVALUATION_RESULTS.json').read_bytes())
        for arm in 'AB':
            self.assertIn('Unmodified exact base',ev['arms'][arm]['scope'])
            self.assertIsNone(ev['arms'][arm]['fallback_target_probe_passed'])

    def test_actual_boundary_counts_and_identical_configuration(self):
        root=PRIVATE/'verified-output/execution'
        a=json.loads((root/'A/COMPILED_CONFIGURATION.json').read_bytes())
        b=json.loads((root/'B/COMPILED_CONFIGURATION.json').read_bytes())
        self.assertEqual(a,b);self.assertFalse(a['seed_explicit']);self.assertFalse(a['custom_Context_Guard'])
        counts=json.loads((root/'INITIAL_CONTEXT_ADMISSION.json').read_bytes())
        self.assertEqual(counts['B_overhead_tokens'],678)
        for arm in 'AB':
            wire=lines((root/arm/'model_transport/http_wire.jsonl').read_bytes())
            first=next(r for r in wire if r['kind']=='http_response')
            self.assertEqual(first['body']['usage']['prompt_tokens'],counts['arms'][arm]['input_tokens'])
        self.assertTrue(json.loads((root/'OBSERVED_BOUNDARY_COMPARISON.json').read_bytes())['only_supplement_differs'])

    def test_verified_archive_and_cleanup_really_observed(self):
        root=PRIVATE/'verified-output'
        self.assertEqual(sha((PRIVATE/'range-download/egrd-v032-real-gemma-ab.zip').read_bytes()),ARCHIVE_SHA)
        self.assertTrue(json.loads((root/'execution/MODEL_SERVER_CLEANUP.json').read_bytes())['complete'])
        self.assertTrue(json.loads((root/'OWNED_ROOT_RECOVERY.json').read_bytes())['complete'])
        for arm in 'AB':
            r=json.loads((root/'execution'/arm/'FINAL_AGENT_CLEANUP.json').read_bytes())
            self.assertTrue(r['complete'] and r['lease_files_absent'])


if __name__=='__main__':unittest.main()
