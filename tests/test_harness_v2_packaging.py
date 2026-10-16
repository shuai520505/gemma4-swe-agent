"""Notebook failure-path integration; no GPU or model inference."""
import ast
import contextlib
import io
import json
import logging
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

from harness_v2 import gpu_build
from harness_v2.evidence import bundle


class PackagingTests(unittest.TestCase):
    def notebook(self):
        generated={}
        gate=gpu_build.ROOT/'docs/validation/harness-v2/official-cpu-r07.json'
        with mock.patch.object(gpu_build,'write_new',side_effect=lambda p,b: generated.update({Path(p).name:b})),mock.patch.object(gpu_build,'require_cpu_gate',return_value=json.loads(gate.read_text())),contextlib.redirect_stdout(io.StringIO()):
            gpu_build.build('r07',gate)
        return json.loads(generated['gpu.ipynb'])

    def bind_diagnostics(self,notebook,namespace):
        # Execute the actual generated alias and organizer INSTALL failure path.
        aliases=[node for node in ast.parse(notebook['cells'][1]['source']).body
                 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='bundle_run' for t in node.targets)]
        exec(compile(ast.Module(body=aliases,type_ignores=[]),'<generated-diagnostic-bindings>','exec'),namespace)

    def test_install_failure_retains_original_exception_and_diagnostic_zip(self):
        notebook=self.notebook()
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)/'run'; directory.mkdir()
            (directory/'prior-evidence.log').write_text('kept before installation failed')
            namespace=dict(Path=Path,RUN_DIR=directory,bundle=bundle,
                exception_record=lambda path,stage,exc: (path/'exception.json').write_text(json.dumps(dict(stage=stage,type=type(exc).__name__))))
            self.bind_diagnostics(notebook,namespace)
            failure=subprocess.CalledProcessError(1,['nvidia-smi'])
            with mock.patch('subprocess.run',side_effect=failure),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(subprocess.CalledProcessError) as caught:
                    exec(compile(notebook['cells'][3]['source'],'<official-INSTALL>','exec'),namespace)
            self.assertIs(caught.exception,failure)
            with zipfile.ZipFile(directory.with_suffix('.zip')) as archive:
                self.assertEqual(archive.read('prior-evidence.log').decode(),'kept before installation failed')
                self.assertEqual(json.loads(archive.read('exception.json'))['type'],'CalledProcessError')
                self.assertIsNone(archive.testzip())

    def test_server_admission_failure_creates_diagnostic_zip(self):
        notebook=self.notebook()
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)/'run'; directory.mkdir()
            namespace=dict(Path=Path,RUN_DIR=directory,bundle=bundle,logging=logging,
                admission_seconds=lambda *args:0,SESSION_STARTED=0,profile={'task_wall_minutes':25.5},
                server_instance=None,exception_record=lambda path,stage,exc: (path/'exception.json').write_text(stage))
            self.bind_diagnostics(notebook,namespace)
            try:
                with contextlib.redirect_stdout(io.StringIO()),self.assertRaisesRegex(TimeoutError,'Insufficient session time'):
                    exec(compile(notebook['cells'][5]['source'],'<official-SERVER>','exec'),namespace)
                with zipfile.ZipFile(directory.with_suffix('.zip')) as archive:
                    self.assertEqual(archive.read('exception.json').decode(),'vllm_startup_or_compile')
            finally:
                handler=namespace.get('handler')
                if handler:
                    handler.close()
                    for name in ('swegemma','adk_submission'): logging.getLogger(name).removeHandler(handler)


if __name__=='__main__': unittest.main()
