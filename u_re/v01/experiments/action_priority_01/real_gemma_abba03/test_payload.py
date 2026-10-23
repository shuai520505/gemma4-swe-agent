import ast,base64,io,json,unittest,zipfile
from unittest.mock import patch
from .notebook import HERE,ROOT,PRIOR,ID,SLUG,sha,controller_module
from ..real_gemma_abba01 import test_local as legacy

class Dispatch(legacy.Dispatch):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.object(legacy,'HERE',HERE).start();patch.object(legacy,'SLUG',SLUG).start()
        patch.object(legacy,'controller_module',controller_module).start()

class SharedPayload(unittest.TestCase):
    def test_bytes_pins_and_lazy_import_closure(self):
        manifest=json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes());raw=(HERE/'payload.zip').read_bytes()
        self.assertEqual(sha(raw),manifest['payload_sha256'])
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertIsNone(z.testzip())
            for n,h in manifest['files'].items():self.assertEqual(sha(z.read(n)),h)
            lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
            for n,h in lock['source_pins'].items():self.assertEqual(sha(z.read((PRIOR/n).relative_to(ROOT).as_posix())),h)
            self.assertIn('u_re/v01/experiments/fastapi_pilot_01/screen.py',z.namelist())
            self.assertIn('experiments/prepare.py',z.namelist())
            self.assertFalse(any(n.endswith(('cpu_transport.py','cpu_probe.py','cpu_probe_v2.py')) for n in z.namelist()))
    def test_exact_same_payload_in_cpu_and_gpu_notebooks(self):
        want=(HERE/'payload.zip').read_bytes()
        for d in (HERE,HERE/'cpu-e2e01'):
            nb=json.loads((d/'notebook/study.ipynb').read_bytes())
            line=next(l for l in nb['cells'][0]['source'].splitlines() if l.startswith("payload=__import__('base64').b64decode("))
            actual=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]));self.assertEqual(actual,want)
        gpu=json.loads((HERE/'notebook/study.ipynb').read_bytes())['cells'][1]['source']
        self.assertIn("mode='GPU'",gpu);self.assertNotIn('CPUTransport',gpu)
    def test_gpu_rejects_scripted_transport(self):
        tree=ast.parse((HERE/'session.py').read_bytes())
        run=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='run')
        gate=next(n for n in run.body if isinstance(n,ast.Assert) and isinstance(n.msg,ast.Constant) and n.msg.value=='GPU route cannot use scripted transport')
        code=compile(ast.Expression(gate.test),'<real-mode-gate>','eval')
        self.assertTrue(eval(code,dict(mode='GPU',cpu_transport=None)))
        self.assertFalse(eval(code,dict(mode='GPU',cpu_transport=object())))
        self.assertTrue(eval(code,dict(mode='CPU_DRY_RUN',cpu_transport=object())))
    def test_shared_entry_and_worker_observer_are_production_paths(self):
        source=(HERE/'session.py').read_text(encoding='utf-8')
        self.assertIn("__package__+'.worker'",source)
        self.assertIn('baseline=await native_baseline',source)
        worker=(HERE/'worker.py').read_text(encoding='utf-8')
        self.assertIn("directory.parent/'model_transport'",worker)
        self.assertIn('await _evaluate(spec,directory)',worker)

if __name__=='__main__':unittest.main()
