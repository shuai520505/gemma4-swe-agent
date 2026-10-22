import ast
import hashlib
import io
import base64
import json
from pathlib import Path
import unittest
import zipfile
from . import CPU_NOTEBOOK as build


class Checks(unittest.TestCase):
    def test_candidate_identity(self):
        for name,sha in [('u_re/v01/submission_noegv.zip','2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608'),('u_re/v01/submission_full.zip','887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821'),('u_re/v01/experiments/action_priority_01/submission_action_v01.zip','70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8')]:
            self.assertEqual(hashlib.sha256((build.ROOT/name).read_bytes()).hexdigest(),sha)
    def test_synthetic_embedded_programs(self):
        tree=ast.parse((build.HERE/'acceptance.py').read_text())
        text=next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='CANARY' for x in n.targets))
        code=ast.parse(text.replace('TARGETS',repr(['/owned/canary'])))
        nested=next(n.value.value for n in code.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='code' for x in n.targets))
        compile(nested,'child-probe','exec')
    def test_abstract_methods_present(self):
        tree=ast.parse((build.HERE/'CHROOT_TASK_RUNTIME.py').read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
        self.assertTrue({'initialize','run_command','read_file','write_file','copy_to','copy_from','reset','close','work_dir'}<={n.name for n in cls.body if isinstance(n,ast.FunctionDef)})
    def test_frozen_notebook(self):
        cpu,_,_=build.identity('runner01');spec=json.loads((cpu/'BUILD.json').read_bytes());raw=(cpu/'notebook/study.ipynb').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),spec['Notebook_sha256'])
        self.assertEqual(spec['configuration'],dict(GPU=False,TPU=False,internet=False,model_sources=[],Agent_runs=4,Gemma_calls=0,formal_submission=False))
        nb=json.loads(raw)
        tree=ast.parse(nb['cells'][0]['source']);node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='payload' for t in n.targets))
        payload=base64.b64decode(ast.literal_eval(node.value.args[0]))
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            self.assertIsNone(z.testzip())
            self.assertFalse(any(any(x in n for x in ('tasks.jsonl','evaluator_test_text','phase2.junit','gold.patch','reference.patch')) for n in z.namelist()))
        self.assertIn('Task wheel drift',nb['cells'][1]['source'])
        self.assertIn('integrated_cpu_01.acceptance',nb['cells'][1]['source'])
    def test_all_attempts_cpu_scope(self):
        for attempt,agents in [('runner01',4),('runner02',4),('screen01',0),('taskruntime01',2)]:
            cpu,_,slug=build.identity(attempt);spec=json.loads((cpu/'BUILD.json').read_bytes())
            meta=json.loads((cpu/'notebook/kernel-metadata.json').read_bytes())
            self.assertEqual(meta['id'],slug)
            self.assertTrue(all(meta[k] is False for k in ('enable_gpu','enable_tpu','enable_internet')))
            self.assertEqual(meta['model_sources'],[])
            self.assertEqual(spec['configuration']['Agent_runs'],agents)
            self.assertEqual(spec['configuration']['Gemma_calls'],0)
            self.assertEqual(hashlib.sha256((cpu/'notebook/study.ipynb').read_bytes()).hexdigest(),spec['Notebook_sha256'])
    def test_frozen_screening_results(self):
        d=json.loads((build.HERE/'TASK_ADMISSION_LEDGER.json').read_bytes())
        self.assertEqual(d['checked'],4);self.assertIsNone(d['stop'])
        self.assertEqual([r['instance_id'] for r in d['selected']],['fastapi_9425','fastapi_14786'])
        self.assertEqual([r['status'] for r in d['rows'][:4]],['BASELINE_ELIGIBLE','ENVIRONMENT_BLOCKED','ENVIRONMENT_BLOCKED','BASELINE_ELIGIBLE'])
        for r in d['rows'][4:]:
            self.assertEqual(r['status'],'NOT_RUN');self.assertIsNone(r['counts'])
    def test_registration_is_not_execution_authorization(self):
        p=json.loads((build.HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
        self.assertEqual([r['arm'] for r in p['order']],list('ABBA'))
        self.assertEqual([r['instance_id'] for r in p['order']],['fastapi_9425','fastapi_9425','fastapi_14786','fastapi_14786'])
        for k in ('execute','gpu_authorized','formal_submission'):self.assertIs(p[k],False)
        self.assertEqual((p['budget']['Agent_seconds'],p['budget']['charged_tools'],p['budget']['command_seconds']),(300,60,120))


if __name__=='__main__':unittest.main()
