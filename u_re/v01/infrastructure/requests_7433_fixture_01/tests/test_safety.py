import ast
import hashlib
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[3]


class SafetyTests(unittest.TestCase):
    def test_all_inherited_bytes_are_unchanged(self):
        baseline=json.loads((HERE/'evidence/INITIAL_HISTORY.json').read_text())
        for name,digest in baseline['files'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)

    def test_frozen_candidates(self):
        expected={'noegv':'2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608',
                  'full':'887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821'}
        for arm,h in expected.items():
            self.assertEqual(hashlib.sha256((ROOT/f'u_re/v01/submission_{arm}.zip').read_bytes()).hexdigest(),h)

    def test_observer_defines_no_fixture(self):
        tree=ast.parse((HERE/'observer.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                self.assertFalse(any('fixture' in ast.unparse(d).lower() for d in node.decorator_list))

    def test_diagnostic_exec_cannot_overwrite_native_observer_files(self):
        tree=ast.parse((HERE/'diagnose.py').read_text())
        execute=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='execute')
        dispatch=[ast.unparse(n.func) for n in ast.walk(execute) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='exec']
        self.assertEqual(dispatch,['Organizer.exec'])

    def test_synthetic_controls_are_not_claimed_as_requests_repair(self):
        result=json.loads((HERE/'evidence/local_minimal_01/result.json').read_text())
        self.assertTrue(result['passed'])
        self.assertFalse(result['official_workspace_used'])
        self.assertEqual([(r['exit_code'],r['counts']['errors']) for r in result['cases']],[(1,2),(0,0),(0,0),(1,2)])

    def test_notebook_is_cpu_offline_without_model_and_static_downloads(self):
        meta=json.loads((HERE/'notebooks/cpu01/kernel-metadata.json').read_text())
        self.assertIs(meta['enable_gpu'],False)
        self.assertIs(meta['enable_tpu'],False)
        self.assertIs(meta['enable_internet'],False)
        self.assertEqual(meta['model_sources'],[])
        reg=json.loads((HERE/'registrations/cpu01.json').read_text())
        self.assertFalse(any('/evidence/upstream_provider/' in n or '/toy_plugins/' in n for n in reg['source_hashes']))


if __name__=='__main__':unittest.main()
