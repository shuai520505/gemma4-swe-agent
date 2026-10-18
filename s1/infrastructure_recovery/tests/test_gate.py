import json
from pathlib import Path
import tempfile
import unittest

from harness_v2.evidence import Journal,atomic_json
from s1.infrastructure_recovery.session import deadline_proof
from s1.infrastructure_recovery.wire import audit_requests


class GateTests(unittest.TestCase):
    def test_deadline_proof_requires_actual_timeout_budget_and_process_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            atomic_json(p/'official_result.json',dict(error_message='Agent exceeded session timeout (5.0 min)',resolved=False,test_exit_code=1))
            atomic_json(p/'runtime_config.json',dict(budget=dict(agent_seconds=300)))
            atomic_json(p/'progress.json',dict(agent_elapsed_seconds=299.99))
            atomic_json(p/'audit_result.json',dict(process_tree_stopped=True,cleanup_complete=True))
            atomic_json(p/'worker_done.json',dict(cleanup_complete=True))
            self.assertFalse(deadline_proof(p)['official_agent_deadline'])
            Journal(p).append(dict(kind='stage',stage='save_patch',agent_elapsed_seconds=299.99))
            self.assertTrue(deadline_proof(p)['official_agent_deadline'])
            self.assertTrue(deadline_proof(p)['cleanup_verified'])
            atomic_json(p/'audit_result.json',dict(process_tree_stopped=False,cleanup_complete=True))
            self.assertFalse(deadline_proof(p)['cleanup_verified'])

    def test_historical_unmatched_request_is_not_retroactively_explained(self):
        old=Path(__file__).resolve().parents[2]/'experiments/e1_outputcap_smoke_02/results/gpu/runs/01-requests_7328-control'
        # The frozen raw archive is not needed in uploaded test source; build a
        # schema-equivalent historical request with no ID or terminal evidence.
        with tempfile.TemporaryDirectory() as tmp:
            j=Journal(tmp);j.append(dict(kind='http_request',body={}),filename='http_wire.jsonl')
            result=audit_requests(tmp,deadline_evidence=dict(official_agent_deadline=True,cleanup_verified=True))
            self.assertFalse(result['passed'])
            self.assertIn('missing_or_duplicate_request_id',result['reasons'])
            self.assertTrue(result['partial_token_usage'])

    def test_duplicate_terminal_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            j=Journal(tmp)
            j.append(dict(kind='http_request',request_id='one',body_sha256='digest'),filename='http_wire.jsonl')
            j.append(dict(kind='request_sent',request_id='one',body_sha256='digest'),filename='http_lifecycle.jsonl')
            for _ in range(2):j.append(dict(kind='terminal_status',request_id='one',status='cancelled'),filename='http_lifecycle.jsonl')
            result=audit_requests(tmp,deadline_evidence=dict(official_agent_deadline=True,cleanup_verified=True))
            self.assertFalse(result['passed'])
