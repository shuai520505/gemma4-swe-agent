import ctypes
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from . import landlock_exec as land
from .isolation import policy_for,wrap_popen,ENV_ALLOW
from .cpu_build import factory,CPU,SMOKE

class RecoveryTests(unittest.TestCase):
    def test_probe_code_and_nested_child_code_compile(self):
        from .cpu_isolation import PROBE
        import ast
        tree=ast.parse('TARGETS="W10="\n'+PROBE)
        nested=next(n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign)
                    and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
        compile(nested,'<descendant-probe>','exec')
    def test_landlock_layout_and_rights(self):
        self.assertEqual(ctypes.sizeof(land.Ruleset),8);self.assertEqual(ctypes.sizeof(land.Beneath),12)
        self.assertTrue(land.HANDLED & land.REFER);self.assertTrue(land.HANDLED & land.TRUNCATE)
        self.assertFalse(land.WRITE_ONLY & land.READ);self.assertFalse(land.WRITE_ONLY & land.READDIR)
    def test_unsupported_platform_fails_closed(self):
        with patch.object(land.sys,'platform','win32'),self.assertRaises(RuntimeError):land.probe()
    def test_private_paths_are_not_granted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);paths={n:root/n for n in ('workspace','tmp','venv','wheels')}
            for p in paths.values():p.mkdir()
            private=root/'evaluator';private.mkdir()
            rules=policy_for(paths)
            self.assertNotIn(str(private.resolve()),[r['path'] for r in rules])
            self.assertNotIn(str(root.resolve()),[r['path'] for r in rules])
            self.assertNotIn('KAGGLE_API_TOKEN',ENV_ALLOW);self.assertNotIn('URE_ISOLATION_FAKE_SECRET',ENV_ALLOW)
    def test_unknown_process_shape_cannot_fall_through(self):
        with self.assertRaises(RuntimeError):wrap_popen(None,['python','-c','bad'],dict(shell=False),{})
        with self.assertRaises(RuntimeError):wrap_popen(None,['/bin/bash','-c','bad'],dict(shell=False,pass_fds=[5]),{})
    def test_scoped_builder_not_old_identity(self):
        module,proof=factory()
        self.assertEqual(module.CPU,CPU);self.assertTrue(module.SLUG.endswith('-cpu02'))
        self.assertNotEqual(proof['original_sha256'],proof['adapted_source_sha256'])
        controller=module.controller_module()
        with self.assertRaises(PermissionError):controller.checked_authorization(None,{})
    def test_old_error_and_candidate_manifest_unchanged(self):
        original=json.loads((SMOKE/'cpu01/ARCHIVE_AUDIT.json').read_text(encoding='utf-8'))
        self.assertEqual(original['platform_status'],'ERROR');self.assertFalse(original['full_CPU_gate_passed'])
        manifest=json.loads((SMOKE/'INTEGRITY_MANIFEST.json').read_text(encoding='utf-8'))
        import hashlib
        for name,h in manifest['files'].items():self.assertEqual(hashlib.sha256((SMOKE/name).read_bytes()).hexdigest(),h,name)

if __name__=='__main__':unittest.main(verbosity=2)
