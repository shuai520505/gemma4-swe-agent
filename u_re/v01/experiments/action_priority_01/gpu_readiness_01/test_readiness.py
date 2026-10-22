import base64
import hashlib
import io
import json
from pathlib import Path
import unittest
import zipfile

from u_re.v01.experiments.action_priority_01.gpu_readiness_01 import cpu_probe_notebook as builder


class Readiness(unittest.TestCase):
    def test_build_scope_and_payload(self):
        spec=json.loads((builder.CPU/'BUILD.json').read_bytes())
        notebook=(builder.CPU/'notebook/study.ipynb').read_bytes()
        self.assertEqual(hashlib.sha256(notebook).hexdigest(),spec['Notebook_sha256'])
        self.assertEqual(spec['configuration'],dict(GPU=False,TPU=False,internet=False,model_sources=[],Agent_runs=0,Gemma_calls=0,formal_submission=False))
        self.assertEqual(spec['expected_candidates_in_order'],[])
        code=json.loads(notebook)['cells'][0]['source']
        import ast
        tree=ast.parse(code)
        assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='payload' for t in n.targets))
        payload=base64.b64decode(ast.literal_eval(assignment.value.args[0]))
        self.assertEqual(hashlib.sha256(payload).hexdigest(),spec['payload_sha256'])
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            self.assertIsNone(z.testzip())
            self.assertFalse(any(any(v in n.lower() for v in ('evaluator_test','phase2.junit','reference.patch','gold.patch')) for n in z.namelist()))
        self.assertIn('capability_probe',json.loads(notebook)['cells'][1]['source'])

    def test_controller_rejects_wrong_scope(self):
        c=builder.factory();spec=json.loads((builder.CPU/'BUILD.json').read_bytes())
        c.controller_module().checked_config(spec)
        bad=dict(spec,configuration=dict(spec['configuration'],GPU=True))
        with self.assertRaises(AssertionError):c.controller_module().checked_config(bad)
        with self.assertRaises(PermissionError):c.controller_module().checked_authorization(None,spec)

    def test_candidates(self):
        for path,expected in [('u_re/v01/submission_noegv.zip','2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608'),('u_re/v01/submission_full.zip','887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821'),('u_re/v01/experiments/action_priority_01/submission_action_v01.zip','70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8')]:
            self.assertEqual(hashlib.sha256((builder.ROOT/path).read_bytes()).hexdigest(),expected)

    def test_static_order(self):
        p=json.loads((builder.HERE/'TASK_POOL_FREEZE.json').read_bytes())
        self.assertEqual((p['pool_count'],p['refreshed_exclusion_count'],p['ranked_count']),(129,87,42))
        self.assertEqual(p['max_checks'],8)
        self.assertFalse(p['selected_qualified_tasks'])
        self.assertEqual(p['next_max8_in_order'][0]['instance_id'],'fastapi_9425')


if __name__=='__main__':unittest.main()
