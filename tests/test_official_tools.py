"""Scripted integration check, explicitly NOT a Gemma inference evaluation."""
from pathlib import Path
import tempfile
import unittest
from swegemma.context import SwegemmaContext
from swegemma.sandbox.subprocess import SubprocessManager


class OfficialToolsTests(unittest.TestCase):
    def test_repair_test_diff_submit_with_real_tools(self):
        with tempfile.TemporaryDirectory() as temp:
            manager = SubprocessManager(base_dir=Path(temp))
            sandbox_id = manager.start()
            try:
                ctx = SwegemmaContext(docker_manager=manager, container_id=sandbox_id,
                                      repo='test/mock_repo', max_tool_calls=20)
                tools = ctx.create_tools()
                def command(text):
                    return tools['run_command'](command=text)
                setup = command("git init -q && git config user.name Smoke && git config user.email smoke@example.invalid && printf 'def add(a, b): return a - b\\n' > calc.py && git add calc.py && git commit -qm baseline")
                self.assertEqual(setup['status'], 'ok', setup)
                test = "python -B -c 'from calc import add; assert add(2, 3) == 5'"
                self.assertNotEqual(command(test)['status'], 'ok')
                self.assertEqual(tools['read_file'](filepath='calc.py')['status'], 'ok')
                edited = tools['edit_file'](filepath='calc.py', old_string='return a - b', new_string='return a + b')
                self.assertEqual(edited['status'], 'ok', edited)
                result = command(test)
                self.assertEqual(result['status'], 'ok', result)
                self.assertEqual(command('git diff --check')['status'], 'ok')
                self.assertIn('return a + b', command('git diff')['stdout'])
                submitted = tools['submit_patch']()
                self.assertEqual(submitted['status'], 'ok', submitted)
                self.assertTrue(ctx.patch_submitted)
                self.assertIn('+def add(a, b): return a + b', ctx.submitted_patch)
            finally:
                manager.stop(sandbox_id)
