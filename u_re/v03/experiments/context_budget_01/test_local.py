import asyncio,ast,base64,io,json,tempfile,unittest,zipfile
from pathlib import Path
from .common import HERE,ROOT,sha
from .policy import boundary_checks,research_candidate
from .notebook import validate
class PolicyTests(unittest.TestCase):
    def test_actual_guard_boundaries(self):
        rows=asyncio.run(boundary_checks());self.assertEqual([x['rejected'] for x in rows],[False,True,False,False,True])
    def test_only_output_yaml_changes(self):
        with tempfile.TemporaryDirectory() as t:
            root=ROOT/'u_re/v01/experiments/action_priority_01/candidate_action_v01'
            for arm in ('A','B'):
                derived=research_candidate(root,Path(t)/arm,arm)
                for p in root.rglob('*'):
                    if p.is_file() and p.name!='agent.yaml':self.assertEqual(p.read_bytes(),(derived/p.relative_to(root)).read_bytes())
    def test_payload_bytes_and_no_mock(self):
        self.assertTrue(validate('cpu-e2e03'))
        with zipfile.ZipFile(HERE/'payload.zip') as z:
            self.assertFalse(any(n.endswith('cpu_transport.py') for n in z.namelist()))
            self.assertIn('u_re/v01/experiments/action_priority_01/integrated_cpu_01/CPU_GATE_PIN.json',z.namelist())
            for n in z.namelist():
                if n.endswith('.py'):compile(z.read(n),n,'exec')
    def test_external_cpu_transport_loads(self):
        ns={};exec((HERE/'cpu-e2e03/CPU_ONLY_TRANSPORT.py').read_bytes(),ns)
        self.assertTrue(issubclass(ns['CPUTransport'],ns['original'].CPUTransport))
    def test_historical_candidates(self):
        for p,h in [('u_re/v01/submission_noegv.zip','2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608'),('u_re/v01/submission_full.zip','887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821'),('u_re/v01/experiments/action_priority_01/submission_action_v01.zip','70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8')]:self.assertEqual(sha((ROOT/p).read_bytes()),h)
    def test_gpu_rejects_scripted_before_imports(self):
        from .session import run
        with self.assertRaises(AssertionError):asyncio.run(run('unused',0,mode='GPU',cpu_transport=object(),authorization={}))
    def test_exact_CPU_archive_and_GPU_policy_binding(self):
        from .notebook import verify_cpu
        self.assertEqual(verify_cpu()['Notebook_id'],140394362)
        self.assertTrue(validate('gpu01'))
    def test_second_dispatch_blocked_before_SDK(self):
        from .notebook import gpu_launch
        with self.assertRaises(AssertionError):gpu_launch()
    def test_prior_UNKNOWN_not_reclassified(self):
        old=ROOT/'u_re/v02/experiments/real_gemma_replication_01/BATCH_02_EXECUTION.json'
        value=json.loads(old.read_bytes())
        self.assertEqual(value['status'],'SAVE_STATUS_UNKNOWN')
        self.assertIsNone(value['Notebook_id'])
if __name__=='__main__':unittest.main()
