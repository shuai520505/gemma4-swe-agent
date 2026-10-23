import asyncio,json,unittest,zipfile
from pathlib import Path
from .common import HERE,ROOT,CONTROL,CONTROL_SHA,sha
class CandidateTests(unittest.TestCase):
    def test_only_prompt_changed(self):
        a=CONTROL.parent/'submission_action_v01.zip';self.assertEqual(sha(a.read_bytes()),CONTROL_SHA)
        with zipfile.ZipFile(a) as old,zipfile.ZipFile(HERE/'submission_egr_v04.zip') as new:
            self.assertIsNone(new.testzip());self.assertEqual(set(new.namelist()),set(old.namelist()))
            self.assertEqual([n for n in old.namelist() if old.read(n)!=new.read(n)],['prompts/system.md'])
    def test_old_prompt_sections_preserved(self):
        a=(CONTROL/'prompts/system.md').read_bytes();b=(HERE/'candidate_egr_v04/prompts/system.md').read_bytes()
        self.assertEqual(b.replace((HERE/'EGR_INSTRUCTION_BLOCK.md').read_bytes(),(CONTROL.parent/'ACTION_FIRST_INSTRUCTION_BLOCK.md').read_bytes()),a)
        self.assertIn(b'After a successful submit_patch',b);self.assertIn(b'Correctness takes priority',b)
    def test_payload_is_exact_and_no_CPU_transport(self):
        from .notebook import validate
        self.assertTrue(validate('cpu-e2e01'))
        with zipfile.ZipFile(HERE/'payload.zip') as z:
            self.assertFalse(any(n.endswith('cpu_transport.py') for n in z.namelist()))
            for n in z.namelist():
                if n.endswith('.py'):compile(z.read(n),n,'exec')
    def test_cpu_transport_loadable(self):
        ns={};exec((HERE/'cpu-e2e01/CPU_ONLY_TRANSPORT.py').read_bytes(),ns)
        self.assertTrue(issubclass(ns['CPUTransport'],ns['original'].CPUTransport))
    def test_GPU_denied_before_model_import(self):
        from .session import run
        with self.assertRaises(AssertionError):asyncio.run(run('unused',0,mode='GPU'))
    def test_coordinator_actual_source_compiles(self):
        from .session import coordinator
        f=coordinator(json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes()),{})
        self.assertEqual(f.__globals__['__package__'],'u_re.v04.experiments.evidence_guided_repair_01')
    def test_real_CPU_evidence_and_corruption_rejected(self):
        import tempfile
        from .audit import audit_cpu
        proof=json.loads((HERE/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
        self.assertEqual(audit_cpu(proof['raw_archive_path'],'cpu-e2e01')['status'],'V04_EGR_CPU_READY')
        with tempfile.TemporaryDirectory() as tmp:
            broken=Path(tmp)/'corrupt.zip';raw=Path(proof['raw_archive_path']).read_bytes()
            broken.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
            with self.assertRaises(AssertionError):audit_cpu(broken,'cpu-e2e01')
    def test_future_samples_exclude_development_and_reservations(self):
        protocol=json.loads((HERE/'GPU_REPLICATION_PROTOCOL.json').read_bytes())
        ids={r['instance_id'] for r in protocol['ranked_candidates']}
        self.assertFalse(ids & set(protocol['excluded_ids']))
        self.assertFalse(ids & set(protocol['preserved_prior_reservations']))
        self.assertFalse(ids & {'fastapi_5077','fastapi_11355','fastapi_9425','fastapi_14786'})
        self.assertIsNone(protocol['selected_tasks']);self.assertFalse(protocol['GPU_authorized'])
        self.assertTrue(all(r['admission']=='NOT_ADMITTED' for r in protocol['ranked_candidates']))
if __name__=='__main__':unittest.main()
