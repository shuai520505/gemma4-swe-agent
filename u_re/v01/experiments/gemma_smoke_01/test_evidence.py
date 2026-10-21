import json
from pathlib import Path
import tempfile
import unittest
from .audit_cpu_archive import expected_cancel
from .closure_metrics import summarize

HERE=Path(__file__).resolve().parent

class EvidenceTests(unittest.TestCase):
    def test_actual_partial_cpu_result_is_not_a_pass(self):
        d=json.loads((HERE/'cpu01/ARCHIVE_AUDIT.json').read_text(encoding='utf-8'))
        self.assertFalse(d['full_CPU_gate_passed']);self.assertEqual(d['platform_status'],'ERROR')
        self.assertEqual(len(d['tools_with_real_responses']),6)
        self.assertTrue(d['checks']['external_cancel']['expected_synthetic_cancellation'])
        self.assertEqual(d['native_TaskResult'],'NOT_RUN');self.assertEqual(d['native_JUnit'],'NOT_RUN')
    def test_missing_cancellation_evidence_cannot_be_explained(self):
        r=dict(external_cancellation_propagated=True,HTTP_cancelled=True,
            HTTP_audit=dict(reasons=['unexplained_cancellation'],rows=[dict(terminal_status='cancelled',usage=None,usage_complete=False)]))
        c=dict(complete=True,leftover_sandboxes=0)
        self.assertTrue(expected_cancel(r,c))
        r['external_cancellation_propagated']=False;self.assertFalse(expected_cancel(r,c))
        r['external_cancellation_propagated']=True;c['complete']=False;self.assertFalse(expected_cancel(r,c))
    def test_actual_preserved_unknown_then_independent_identity(self):
        root=HERE/'cpu01'
        states=[json.loads(p.read_text(encoding='utf-8'))['state'] for p in sorted((root/'execution/events').glob('*.json'))]
        self.assertIn('UNKNOWN_STOP',states);self.assertNotIn('ACCEPTED_CONFIRMED',states)
        d=json.loads((root/'read_observations/read-02/RESOURCE_IDENTITY.json').read_text(encoding='utf-8'))
        self.assertEqual(d['state'],'IDENTITY_CONFIRMED');self.assertEqual(d['metadata']['id'],140042899)
        self.assertTrue(d['source']['payload_match'])
    def test_post_submit_tools_are_observed_not_suppressed(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            native=[dict(stage='agent',agent_started=True,recorded_monotonic=10),
                    dict(kind='patch',sha256='synthetic',recorded_monotonic=16),
                    dict(stage='save_patch',agent_elapsed_seconds=20,recorded_monotonic=30)]
            tools=[dict(recorded_monotonic=15,event=dict(content=dict(parts=[dict(function_response=dict(name='submit_patch',response={'status':'ok'}))]))),
                   dict(recorded_monotonic=20,event=dict(content=dict(parts=[dict(function_call=dict(name='run_command',args={}))]))),
                   dict(recorded_monotonic=25,event=dict(content=dict(parts=[dict(function_response=dict(name='submit_patch',response={'status':'ok'}))])))]
            for name,values in [('events.jsonl',native),('adk_events.jsonl',tools)]:
                (d/name).write_text('\n'.join(json.dumps(v) for v in values))
            r=summarize(d)
            self.assertEqual(r['tools_after_first_successful_submit'],1);self.assertEqual(r['successful_resubmissions'],1)
            self.assertEqual(r['continued_seconds_after_submit'],15);self.assertEqual(r['first_successful_submit_seconds'],5)

if __name__=='__main__':unittest.main(verbosity=2)
