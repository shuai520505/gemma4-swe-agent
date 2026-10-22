import ast
import base64
import io
import json
import unittest
import zipfile
from . import cpu_repair
from .notebook import ROOT,sha

class RuntimeClosure(unittest.TestCase):
    def payload(self):
        nb=json.loads((cpu_repair.CPU/'notebook/study.ipynb').read_bytes())
        line=next(x for x in nb['cells'][0]['source'].splitlines() if x.startswith("payload=__import__('base64').b64decode("))
        raw=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertIsNone(z.testzip());return {n:z.read(n) for n in z.namelist()}
    def test_lazy_native_baseline_import_is_packaged(self):
        files=self.payload()
        for n in ('u_re/v01/experiments/fastapi_pilot_01/screen.py','experiments/prepare.py'):
            self.assertEqual(files[n],(ROOT/n).read_bytes())
        graph=json.loads((cpu_repair.HERE/'IMPORT_CLOSURE.json').read_bytes())
        self.assertTrue(any(e['importer'].endswith('.session') and e['imported'].endswith('fastapi_pilot_01.screen') for e in graph['edges']))
    def test_all_registered_bytes_are_preserved(self):
        files=self.payload();reg=json.loads(files['repair_registration.json'])
        self.assertEqual(set(files)-{'repair_registration.json'},set(reg['files']))
        for n,h in reg['files'].items():self.assertEqual(sha(files[n]),h)
    def test_cpu_scope_truthful_and_gpu_rejected(self):
        spec=json.loads((cpu_repair.CPU/'BUILD.json').read_bytes());check=cpu_repair.factory().controller_module().checked_config
        self.assertEqual(spec['configuration']['Agent_runs'],1);check(spec)
        for key,value in [('GPU',True),('Gemma_calls',1),('Agent_runs',2),('model_sources',['forbidden'])]:
            with self.assertRaises(AssertionError):check(dict(spec,configuration=dict(spec['configuration'],**{key:value})))

if __name__=='__main__':unittest.main()
