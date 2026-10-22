import ast
import base64
import io
import json
import unittest
from unittest.mock import patch
import zipfile
from ..real_gemma_abba01 import test_local as legacy
from .notebook import HERE,ROOT,PRIOR,ID,SLUG,sha,factory

class NewDispatchScope(legacy.Dispatch):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.object(legacy,'HERE',HERE).start();patch.object(legacy,'SLUG',SLUG).start()
        patch.object(legacy,'controller_module',factory().controller_module).start()

class Closure(unittest.TestCase):
    def payload(self):
        nb=json.loads((HERE/'notebook/study.ipynb').read_bytes())
        line=next(l for l in nb['cells'][0]['source'].splitlines() if l.startswith("payload=__import__('base64').b64decode("))
        raw=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertIsNone(z.testzip());return {n:z.read(n) for n in z.namelist()}
    def test_complete_registered_bytes_and_pins(self):
        files=self.payload();reg=json.loads(files['gpu_registration.json'])
        self.assertEqual(reg['execution_id'],ID)
        for n,h in reg['files'].items():self.assertEqual(sha(files[n]),h)
        lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
        for n,h in lock['source_pins'].items():self.assertEqual(sha(files[(PRIOR/n).relative_to(ROOT).as_posix()]),h)
    def test_only_new_authorization_differs_from_cpu_proven_closure(self):
        from ..real_gemma_abba01.repair import corrected_files
        files=self.payload();before=corrected_files();auth='u_re/v01/experiments/action_priority_01/real_gemma_abba01/GPU_AUTHORIZATION.json'
        self.assertEqual(set(files)-{'gpu_registration.json'},set(before))
        self.assertEqual([n for n in before if before[n]!=files[n]],[auth])
        value=json.loads(files[auth]);self.assertEqual(value['execution_id'],ID);self.assertEqual(value['slug'],SLUG)
    def test_original_gpu01_notebook_and_claim_unchanged(self):
        old=HERE.parent/'real_gemma_abba01';spec=json.loads((old/'BUILD.json').read_bytes())
        self.assertEqual(sha((old/'notebook/study.ipynb').read_bytes()),spec['Notebook_sha256'])
        self.assertTrue((old/'execution/dispatch.claim').exists())

if __name__=='__main__':unittest.main()
