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


if __name__=='__main__':unittest.main()
