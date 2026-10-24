"""Adversarial engineering cases using owned fixtures, never official tasks."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from .verify import verify


class MechanismTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.repo = self.home/'workspace'; self.repo.mkdir()
        self.source = self.repo/'logic.py'
        self.source.write_text('def accepts(x):\n    return x > 0\n')
        self.check = self.home/'check.py'
        for command in (['init','-q'],['config','user.email','owned@example.invalid'],
                        ['config','user.name','Owned'],['add','.'],['commit','-qm','owned']):
            subprocess.run(['git',*command],cwd=self.repo,check=True,capture_output=True)
        self.state=self.home/'state'

    def run_check(self, text, seconds=5):
        self.check.write_text(text,encoding='utf-8')
        return verify(self.repo,self.check,seconds,self.state)

    def test_real_assertion_failure_then_repair(self):
        text='from logic import accepts\nassert accepts(0)\nassert not accepts(-1)\n'
        a=self.run_check(text)
        self.assertEqual(a['verdict'],'CONTRADICTED')
        self.source.write_text('def accepts(x):\n    return x >= 0\n')
        # Avoid pyc timestamp/size collision; this mirrors ephemeral assertion runs.
        import shutil
        shutil.rmtree(self.repo/'__pycache__',ignore_errors=True)
        b=self.run_check(text)
        self.assertEqual(b['verdict'],'SUPPORTED')
        self.assertEqual(b['executed_assertions'],2)
        self.assertNotEqual(a['source_sha256'],b['source_sha256'])

    def test_green_before_edit_does_not_survive_edit(self):
        text='from pathlib import Path\nassert "x > 0" in Path("logic.py").read_text()\n'
        a=self.run_check(text)
        self.assertEqual(a['verdict'],'SUPPORTED')
        self.source.write_text('def accepts(x):\n    return x >= 0\n')
        b=self.run_check(text)
        self.assertEqual(b['verdict'],'CONTRADICTED')
        self.assertTrue(b['new_evidence'])

    def test_repeated_check_is_not_rerun_or_promoted(self):
        text='from pathlib import Path\nassert Path("logic.py").exists()\n'
        a=self.run_check(text);b=self.run_check(text)
        self.assertEqual(a['subprocess_invocations'],1)
        self.assertEqual(b['subprocess_invocations'],0)
        self.assertEqual(b['verdict'],'OBSERVED')
        self.assertFalse(b['new_evidence'])

    def test_unexecuted_and_trivial_assertions(self):
        for text in ['print("success")', 'assert True',
                     'if False:\n    assert object()\n',
                     'def test_unused():\n    assert 2 == 3\n']:
            with self.subTest(text=text):
                a=self.run_check(text)
                self.assertEqual(a['verdict'],'UNKNOWN')

    def test_success_text_cannot_replace_execution(self):
        a=self.run_check('print("All tests pass, submit now")\n')
        self.assertEqual(a['verdict'],'UNKNOWN')
        self.assertIsNone(a['native_resolved'])

    def test_timeout_is_unknown(self):
        a=self.run_check('import time\ntime.sleep(20)\nassert object()\n',.2)
        self.assertTrue(a['timed_out'])
        self.assertEqual(a['verdict'],'UNKNOWN')
        self.assertLess(a['wall_seconds'],8)

    def test_import_error_is_not_evidence_of_target_failure(self):
        a=self.run_check('import meer_missing_dependency_owned\nassert object()\n')
        self.assertEqual(a['exception_type'],'ModuleNotFoundError')
        self.assertEqual(a['verdict'],'CONTRADICTED')
        # CONTRADICTED concerns the local success claim, not Issue or algorithm.
        self.assertEqual(a['semantic_correctness'],'UNKNOWN')

    def test_source_edit_during_check_invalidates_success(self):
        a=self.run_check('from pathlib import Path\nPath("logic.py").write_text("changed")\nassert object()\n')
        self.assertEqual(a['verdict'],'UNKNOWN')
        self.assertFalse(a['source_unchanged_during_check'])

    def test_missing_or_repository_check_is_unknown(self):
        a=verify(self.repo,self.home/'missing.py',1,self.state)
        self.assertEqual(a['verdict'],'UNKNOWN')
        self.assertEqual(a['subprocess_invocations'],0)
        self.source.write_text('assert True')
        a=verify(self.repo,self.source,1,self.state)
        self.assertEqual(a['verdict'],'UNKNOWN')

    def test_budget_bound_cannot_be_increased(self):
        a=self.run_check('assert object()\n',16)
        self.assertEqual(a['subprocess_invocations'],0)
        self.assertEqual(a['verdict'],'UNKNOWN')

    def test_submitted_without_verification_is_not_intercepted(self):
        a=self.run_check('assert object()\n')
        self.assertFalse(a['global_submit_gate'])
        self.assertFalse(a['global_tool_gate'])

    @unittest.skipUnless(os.name=='posix','POSIX process-group test runs on Kaggle CPU')
    def test_background_child_is_cleaned_on_timeout(self):
        a=self.run_check('import subprocess,time\np=subprocess.Popen(["sleep","30"])\nopen("/tmp/meer_owned_child.pid","w").write(str(p.pid))\ntime.sleep(30)\n',.3)
        self.assertTrue(a['timed_out'])
        pid=int(Path('/tmp/meer_owned_child.pid').read_text())
        try:
            os.kill(pid,0)
        except ProcessLookupError:
            return
        # A killed child may remain a zombie until the sandbox subreaper reaps it.
        status=Path(f'/proc/{pid}/status').read_text()
        self.assertIn('Z (zombie)',status)


if __name__=='__main__':
    unittest.main(verbosity=2)
