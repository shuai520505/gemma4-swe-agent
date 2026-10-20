"""No GPU allocation; integrity and refusal tests for this execution wrapper."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from s2.egv_agenttool_t500_early_v01.gpu_session import require_authorization
from . import runtime_gate

HERE = Path(__file__).resolve().parent
EARLY = HERE.parents[2] / 's2/egv_agenttool_t500_early_v01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


class BuildTests(unittest.TestCase):
    def test_original_draft_still_refuses(self):
        cell = read(EARLY / 'notebooks/gpu-draft/study.ipynb')['cells'][0]['source']
        first = ast.parse(cell).body[0]
        self.assertIsInstance(first, ast.Raise)
        with self.assertRaises(RuntimeError):
            exec(compile(ast.Module(body=[first], type_ignores=[]), '<first-raise-only>', 'exec'), {})

    def test_protocol_preserves_design(self):
        old = read(EARLY / 'GPU_MECHANISM_PROTOCOL_DRAFT.json')
        new = read(HERE / 'AUTHORIZED_PROTOCOL.json')
        for key in set(old) - {'status', 'GPU_authorized', 'pending', 'source_hashes'}:
            self.assertEqual(old[key], new[key], key)
        self.assertEqual([r['arm'] for r in new['runs']], ['A', 'B', 'B', 'A'])
        self.assertEqual([r['instance_id'] for r in new['runs']], ['rich_3676'] * 2 + ['fastapi_14492'] * 2)

    def test_payload_and_candidate_bytes(self):
        plan = read(HERE / 'AUTHORIZED_PROTOCOL.json')
        frozen = read(HERE / 'EXECUTION_BUILD_MANIFEST.json')
        raw = (HERE / 'payload.zip').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), frozen['payload_sha256'])
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertIsNone(z.testzip())
            for name, digest in plan['source_hashes'].items():
                self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), digest, name)
            for arm, candidate in plan['candidates'].items():
                raw = (HERE / 'frozen_candidates' / (arm + '.zip')).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), candidate['zip_sha256'])
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    for name, digest in candidate['members'].items():
                        self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
                        self.assertEqual(archive.read(name), z.read(candidate['directory'] + '/' + name))

    def test_machine_flag_not_preapproved(self):
        plan = read(HERE / 'AUTHORIZED_PROTOCOL.json')
        auth = read(HERE / 'GPU_AUTHORIZATION.json')
        self.assertFalse(auth['fresh_quota_and_machine_admission_verified'])
        with self.assertRaises(AssertionError):
            require_authorization(plan, auth, 1)
        require_authorization(plan, dict(auth, fresh_quota_and_machine_admission_verified=True), 1)

    def test_wrong_hardware_refused_before_framework(self):
        replies = [SimpleNamespace(stdout='0, NVIDIA T4, uuid, 15000 MiB, 555\n', stderr=''), SimpleNamespace(stdout='', stderr='')]
        with tempfile.TemporaryDirectory() as path, patch.object(runtime_gate.subprocess, 'run', side_effect=replies):
            with self.assertRaises(AssertionError):
                runtime_gate.admit(HERE, Path(path), 0, {})

    def test_notebook_compiles_without_execution(self):
        notebook = read(HERE / 'notebooks/gpu01/study.ipynb')
        for cell in notebook['cells']:
            compile(cell['source'], '<compile-only>', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        self.assertIn('admit(SOURCE,RUN_DIR,SESSION_STARTED,authorization)', notebook['cells'][1]['source'])
        self.assertIn('psutil.Process(1).create_time()', notebook['cells'][0]['source'])


if __name__ == '__main__':
    unittest.main()
