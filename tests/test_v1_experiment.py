"""Controller/metric checks only; these never count as model experiments."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from experiments.metrics import classify, summarize
from experiments.prepare import ROOT, archive_bytes, verify_frozen, write_new
from experiments.runtime import unpack_experiment
from experiments.build_notebook import build


class ComparisonTests(unittest.TestCase):
    def test_collection_error_is_not_a_pass_or_executed_test(self):
        text = 'STDOUT:\nERROR collecting tests/example.py\nInterrupted: 1 error during collection\nSTDERR:\n'
        r = classify({'test_exit_code': 2}, text, 'diff --git a/x b/x')
        self.assertTrue(r['phase2_invoked'])
        self.assertTrue(r['collection_failed'])
        self.assertFalse(r['test_bodies_observed'])
        self.assertTrue(r['patch_application_valid'])

    def test_setup_error_does_not_imply_patch_application_or_collection(self):
        r = classify({'test_exit_code': 1}, 'Failed to apply agent patch', 'bad patch')
        self.assertFalse(r['phase2_invoked'])
        self.assertFalse(r['patch_application_valid'])
        self.assertFalse(r['collection_failed'])

    def test_partial_results_are_not_final_rates(self):
        plan = [dict(arm=a, instance_id='x') for a in ('v0', 'v1')]
        result = summarize([dict(arm='v0', instance_id='x', resolved=True)], plan)
        self.assertFalse(result['complete'])
        self.assertIsNone(result['arms']['v1']['resolution_rate'])
        self.assertEqual(result['paired']['n'], 0)

    def test_paired_outcome_and_denominators(self):
        plan = [dict(arm=a, instance_id=i) for i in ('x', 'y') for a in ('v0', 'v1')]
        rows = [dict(arm=a, instance_id=i, resolved=a == 'v1' and i == 'x',
                     phase2_invoked=True, collection_failed=i == 'y',
                     patch_application_valid=True, duration_seconds=2,
                     total_llm_calls=3, tool_calls=4) for i in ('x', 'y') for a in ('v0', 'v1')]
        r = summarize(rows, plan)
        self.assertEqual(r['arms']['v1']['resolution_rate'], 0.5)
        self.assertEqual(r['arms']['v0']['collection_failure_rate_invoked'], 0.5)
        self.assertEqual(r['paired']['v1_only_resolved'], 1)

    def test_frozen_writes_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'a'
            write_new(p, b'one')
            write_new(p, b'one')
            with self.assertRaises(FileExistsError):
                write_new(p, b'two')
            self.assertEqual(p.read_bytes(), b'one')

    def test_payload_contains_only_two_agents_and_plan(self):
        source = ROOT / 'artifacts/v1-pilot/input/submission.bundle'
        with tempfile.TemporaryDirectory() as tmp:
            plan = unpack_experiment(source, Path(tmp) / 'arms')
            self.assertEqual(len(plan['schedule']), 8)
            self.assertNotIn('fastapi_15661', [r['instance_id'] for r in plan['schedule']])
            self.assertEqual([r['index'] for r in plan['schedule']], list(range(1, 9)))
            with zipfile.ZipFile(source) as z:
                self.assertEqual(len(z.namelist()), 7)
                self.assertFalse(any('reference' in n or 'trace' in n or 'analysis' in n for n in z.namelist()))
                damaged = {n: z.read(n) for n in z.namelist()}
            damaged['../escape'] = b'x'
            p = Path(tmp) / 'bad.bundle'
            p.write_bytes(archive_bytes(damaged))
            with self.assertRaises(ValueError):
                unpack_experiment(p, Path(tmp) / 'bad')

    def test_generated_notebook_is_synced_and_v0_is_intact(self):
        expected = json.loads((ROOT / 'experiments/v1_pilot.ipynb').read_text())
        self.assertEqual(expected, build())
        self.assertGreater(verify_frozen(), 30)


if __name__ == '__main__':
    unittest.main()
