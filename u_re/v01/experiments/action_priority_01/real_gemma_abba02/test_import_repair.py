import ast
import base64
import io
import json
import unittest
import zipfile
import tempfile
from pathlib import Path
from contextlib import contextmanager
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

    def test_http_observer_does_not_precreate_runner_directory(self):
        # Actual observer and filesystem; official Runner is exercised in Kaggle.
        from s1.infrastructure_recovery.wire import observe_http
        tree=ast.parse((cpu_repair.HERE/'runtime_worker.py').read_bytes())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='observe_without_precreating_agent')
        ns=dict(Path=Path,contextmanager=contextmanager,_observe=observe_http)
        exec(compile(ast.Module(body=[function],type_ignores=[]),'<observer-boundary>','exec'),ns)
        with tempfile.TemporaryDirectory() as temp:
            agent=Path(temp)/'agent'
            with ns[function.name](agent):
                self.assertFalse(agent.exists());agent.mkdir(exist_ok=False)
                for name in ('http_wire.jsonl','http_lifecycle.jsonl'):(Path(temp)/'model_transport'/name).write_bytes(b'owned unchanged event\n')
            for name in ('http_wire.jsonl','http_lifecycle.jsonl'):self.assertEqual((agent/name).read_bytes(),b'owned unchanged event\n')

if __name__=='__main__':unittest.main()
