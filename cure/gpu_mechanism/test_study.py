import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from .scenarios import CASES
from .audit import inspect_run


class StudyTests(unittest.TestCase):
    def test_fresh_scenarios_baseline_red_reference_green(self):
        for case in CASES:
            with self.subTest(case=case['id']), tempfile.TemporaryDirectory() as temp:
                root=Path(temp)
                for n,text in case['files'].items():
                    p=root/n; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
                (root/'test_evaluation.py').write_text(case['checks'])
                def run():
                    return subprocess.run([sys.executable,'-m','pytest','-q','test_evaluation.py'],cwd=root,
                        capture_output=True,text=True,timeout=40)
                baseline=run()
                self.assertNotEqual(baseline.returncode,0)
                for n,text in case['reference'].items(): (root/n).write_text(text)
                passed=run()
                self.assertEqual(passed.returncode,0,passed.stdout+passed.stderr)

    def test_incomplete_is_not_admitted(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertFalse(inspect_run(temp,'model')['infrastructure_passed'])

    def test_no_reference_in_repository(self):
        self.assertEqual(len(CASES),4)
        for case in CASES:
            self.assertNotIn('test_evaluation.py',case['files'])
            self.assertNotIn('reference',case['files'])


if __name__=='__main__': unittest.main()
