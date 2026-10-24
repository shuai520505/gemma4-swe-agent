"""Offline binding and fail-closed authorization tests, no model or Kaggle."""
import asyncio
import hashlib
import json
from pathlib import Path
import unittest
import zipfile
from .prepare import HERE, MEER, evidence_audit, sha
from .session import authorize, coordinator
from .worker import verify_candidate, evaluate


class BindingTests(unittest.TestCase):
    def test_frozen_candidate_and_actual_private_evidence(self):
        self.assertTrue(evidence_audit()['candidate_ZIPs_and_members_rehashed'])

    def test_authorization_absent_fails_closed(self):
        m=json.loads((HERE/'EXECUTION_MANIFEST.json').read_bytes())
        for grant in (None,{},dict(GPU_authorized=False),dict(GPU_authorized=True)):
            with self.assertRaises(PermissionError):authorize(grant,m,1,{})

    def test_grant_binds_exact_batch_and_payload(self):
        m=json.loads((HERE/'EXECUTION_MANIFEST.json').read_bytes())
        identity=dict(payload_sha256='OWNED_TEST_ONLY',production_entry='meer.v01.gpu01.session.run')
        grant=dict(GPU_authorized=True,owner_authorization_reference='UNIT_TEST_NOT_AN_OWNER_GRANT',
            experiment_id=m['experiment_id'],manifest_sha256=sha((HERE/'EXECUTION_MANIFEST.json').read_bytes()),
            payload_sha256=identity['payload_sha256'],batch=1,order=m['batches']['1'],arms=m['arms'],
            environment_lock_sha256=m['environment_lock_sha256'],model_files=m['model']['files'],
            max_SaveKernel_dispatches=1,max_Agent_runs=3,GPU_count=4,GPU_type='NVIDIA L4',TP=4,
            Agent_seconds=300,platform_window_seconds=10000)
        self.assertEqual(authorize(grant,m,1,identity),grant)
        with self.assertRaises(PermissionError):authorize(grant,m,2,identity)
        with self.assertRaises(PermissionError):authorize(dict(grant,max_Agent_runs=4),m,1,identity)
        with self.assertRaises(PermissionError):authorize(grant,m,1,dict(identity,payload_sha256='different'))

    def test_all_three_exact_candidate_directories(self):
        for arm in ('A','B','C'):verify_candidate(dict(arm=arm,agent_dir=str(MEER/'candidates'/arm)))

    def test_gpu_worker_refuses_scripted_route_before_official_imports(self):
        with self.assertRaisesRegex(ValueError,'reject scripted'):
            asyncio.run(evaluate(dict(arm='B',agent_dir=str(MEER/'candidates/B'),model_transport='CPU_SCRIPTED_ONLY'),HERE/'never-created'))
        self.assertFalse((HERE/'never-created').exists())

    def test_packaged_member_closure(self):
        build=json.loads((HERE/'PAYLOAD_BUILD.json').read_bytes())
        raw=(HERE/'payload.zip').read_bytes();self.assertEqual(sha(raw),build['payload_sha256'])
        with zipfile.ZipFile(HERE/'payload.zip') as z:
            self.assertIsNone(z.testzip())
            for n,h in build['payload_members'].items():self.assertEqual(sha(z.read(n)),h,n)
            for n in ('CPU_GATE_PIN.json','fastapi_pilot_01/screen.py'):
                self.assertTrue(any(p.endswith(n) for p in z.namelist()))
            self.assertNotIn('meer/v01/owned_transport.py',z.namelist())
            self.assertNotIn('meer/v01/gpu01/cpu_validation.py',z.namelist())

    def test_coordinator_source_binding(self):
        m=json.loads((HERE/'RUNTIME_LOCK.json').read_bytes())
        # Construction imports only existing local research code; no model start.
        fn=coordinator(m,{})
        self.assertEqual(fn.__globals__['__package__'],'meer.v01.gpu01')
        self.assertEqual(fn.__globals__['LOCK']['order'],m['order'])
        self.assertTrue(fn.__globals__['native_baseline'].__module__.endswith('prospective_admission_01.session'))

    def test_context_reservation_equal_and_boundary(self):
        from harness_v2.context_budget import ContextPolicy,ContextBudgetExceeded
        p=ContextPolicy()
        self.assertEqual(p.check(15360,16384)['decision'],'allow')
        with self.assertRaises(ContextBudgetExceeded):p.check(15361,16384)


if __name__=='__main__':unittest.main(verbosity=2)
