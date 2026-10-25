"""Regression checks against the retained actual archive (no model/network)."""
import json
import os
from pathlib import Path
import unittest
import zipfile

from .read_preflight import HERE, PRIVATE


class ActualEvidenceAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=Path(os.environ.get('MEER_PRIVATE_ARCHIVE',str(PRIVATE/'batch02/read-03/evidence_confirmed/output/meer-v01-gpu-batch2.zip')))
        cls.zip=zipfile.ZipFile(cls.path)
        cls.metrics=json.loads((HERE/'BATCH_02_DERIVED_METRICS.json').read_bytes())['sessions']

    @classmethod
    def tearDownClass(cls):cls.zip.close()

    def rows(self,name):return [json.loads(x) for x in self.zip.read(name).splitlines()]

    def test_snapshot_deployment_is_not_an_Agent_edit(self):
        for m in self.metrics:
            rows=self.rows('execution/runs/'+m['session']+'/agent/events.jsonl')
            start=next(r['recorded_monotonic'] for r in rows if r.get('agent_started'))
            deployment=[r for r in rows if r.get('kind')=='source_boundary_observation' and not r.get('before') and r.get('production_changed')]
            self.assertEqual(len(deployment),1)
            self.assertLess(deployment[0]['end_monotonic'],start)
            self.assertEqual(m['source_changing_operations'],0)
            self.assertIsNone(m['first_source_change_upper_bound_seconds'])

    def test_Guard_rejections_are_read_from_Worker_journal(self):
        for m in self.metrics:
            rows=self.rows('execution/runs/'+m['session']+'/events.jsonl')
            rejects=[r for r in rows if r.get('kind')=='context_admission' and r.get('decision')=='reject']
            self.assertEqual(len(rejects),1)
            self.assertTrue(m['context_guard_triggered'])
            self.assertGreater(rejects[0]['input_tokens'],15360)
            self.assertEqual(rejects[0]['output_reserved'],16384)
            self.assertEqual(rejects[0]['input_tokens'],m['context_rejections'][0]['input_tokens'])

    def test_request_denominator_and_optional_Skill_exposure(self):
        total=0
        for m in self.metrics:
            rows=self.rows('execution/runs/'+m['session']+'/agent/http_wire.jsonl')
            requests=[r for r in rows if r['kind']=='http_request']
            responses=[r for r in rows if r['kind']=='http_response']
            self.assertEqual(len(requests),len(responses))
            self.assertTrue(all(r['status']==200 for r in responses))
            self.assertEqual(sum(r['body']['usage']['total_tokens'] for r in responses),m['observed_received_tokens'])
            if m['arm'] in ('B','C'):
                self.assertIn('run_skill_script',[t['function']['name'] for t in requests[0]['body']['tools']])
                self.assertEqual(m['Skill_invocations'],0)
                self.assertTrue(m['Skill_bypassed'])
            total+=len(requests)
        self.assertEqual(total,40)


if __name__=='__main__':unittest.main(verbosity=2)
