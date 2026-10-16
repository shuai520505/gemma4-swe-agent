"""Postprocessing fixtures never stand in for GPU experiment results."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

from harness_v2 import audit


class AuditTests(unittest.TestCase):
    def test_trailing_interrupted_append_preserves_prior_events_and_gap(self):
        rows,truncated=audit.journal_rows(b'{"kind":"patch"}\n{"kind":')
        self.assertEqual(rows,[{'kind':'patch'}])
        self.assertTrue(truncated)
        with self.assertRaises(ValueError): audit.journal_rows(b'{broken\n{"valid":true}\n')

    def test_bootstrap_failure_keeps_every_preassigned_task_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            registration=root/'harness_v2/registrations'; registration.mkdir(parents=True)
            plan=dict(source_hashes={},tasks=[dict(instance_id='fixture_a',arm='v0'),dict(instance_id='fixture_b',arm='v1')])
            (registration/'fixture.json').write_text(json.dumps(plan))
            archive=root/'fixture.zip'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('source/infra_plan.json',json.dumps(plan))
                z.writestr('exception.json','{"stage":"bootstrap","type":"FixtureError"}')
            with mock.patch.object(audit,'ROOT',root),mock.patch.object(audit,'verify_baseline',return_value=76):
                result=audit.audit(archive,'fixture','gpu')
            self.assertEqual(result['status_counts'],{'not_run':2})
            self.assertFalse(result['development_infrastructure_gate_passed'])
            self.assertIsNone(result['formal_resolution_rate'])
            self.assertTrue(result['development_only'])


if __name__=='__main__': unittest.main()
