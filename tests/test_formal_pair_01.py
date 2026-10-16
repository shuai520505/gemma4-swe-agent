"""Scheduling and admission checks; no model inference."""
import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from experiments.prepare import ROOT


class FormalProtocolTests(unittest.TestCase):
    def test_eight_runs_are_complete_balanced_pairs(self):
        p=json.loads((ROOT/'experiments/formal-paired-01/protocol.json').read_text())
        self.assertEqual([r['index'] for r in p['schedule']],list(range(1,9)))
        self.assertEqual(len({r['repo'] for r in p['schedule']}),4)
        self.assertFalse({r['instance_id'] for r in p['schedule']} & set(p['excluded_tasks']))
        first=[]
        for batch in p['batches']:
            self.assertEqual(len(batch),4)
            for i in (0,2):
                a,b=batch[i:i+2];first.append(a['arm'])
                self.assertEqual(a['instance_id'],b['instance_id'])
                self.assertEqual({a['arm'],b['arm']},{'v0','v1'})
        self.assertEqual(first.count('v0'),2)

    def test_both_notebook_setups_accept_exact_frozen_bundle(self):
        for letter in ('a','b'):
            with self.subTest(batch=letter),tempfile.TemporaryDirectory() as tmp:
                tmp=Path(tmp);inputs=tmp/'input';inputs.mkdir()
                (inputs/'paired-01.bundle').write_bytes((ROOT/'artifacts/formal-paired-01/input/paired-01.bundle').read_bytes())
                nb=json.loads((ROOT/f'artifacts/formal-paired-01/kernel-{letter}/formal.ipynb').read_text())
                for c in nb['cells']:
                    if c['cell_type']=='code':compile(c['source'],'<notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
                setup=nb['cells'][1]['source'].replace("Path('/kaggle/input')",repr(inputs))
                # repr(Path) needs the concrete WindowsPath name on Windows.
                setup=setup.replace("Path('/kaggle/working/formal_paired_01')","Path("+repr(str(tmp/'runs'))+")")
                setup=setup.replace(repr(inputs),"Path("+repr(str(inputs))+")")
                setup+="\nassert len(PLAN['tasks'])==4\nassert json.loads((SOURCE/'infra_plan.json').read_text())==PLAN\nprint('Admission passed; no model started')\n"
                result=subprocess.run([sys.executable,'-c',setup],capture_output=True,text=True,timeout=30,cwd=ROOT)
                self.assertEqual(result.returncode,0,result.stderr)

    def test_tampered_input_is_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);inputs=tmp/'input';inputs.mkdir()
            (inputs/'paired-01.bundle').write_bytes(b'not the registered bundle')
            nb=json.loads((ROOT/'artifacts/formal-paired-01/kernel-a/formal.ipynb').read_text())
            setup=nb['cells'][1]['source'].replace("Path('/kaggle/input')","Path("+repr(str(inputs))+")")
            setup=setup.replace("Path('/kaggle/working/formal_paired_01')","Path("+repr(str(tmp/'runs'))+")")
            result=subprocess.run([sys.executable,'-c',setup],capture_output=True,text=True,timeout=30,cwd=ROOT)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('AssertionError',result.stderr)
            self.assertFalse(any((tmp/'runs').rglob('infra_plan.json')))


if __name__=='__main__':unittest.main()
