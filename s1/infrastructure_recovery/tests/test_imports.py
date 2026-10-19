import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from s1.infrastructure_recovery.import_audit import install,classify


class ImportTests(unittest.TestCase):
    def test_real_process_discriminates_foreign_and_edited_source_despite_exit0(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);venv=root/'venv';workspace=root/'workspace'
            subprocess.run([sys.executable,'-m','venv','--without-pip',str(venv)],check=True,timeout=30)
            install(venv)
            python=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python3')
            # Controlled foreign package stands in for a system-installed package;
            # tests do not assume Requests happens to be installed on this host.
            for parent,value in [(root/'system','foreign'),(workspace/'src','edited')]:
                package=parent/'fixturepkg';package.mkdir(parents=True)
                (package/'__init__.py').write_text('VALUE='+repr(value)+'\n')
            for label,parent in [('wrong',root/'system'),('right',workspace/'src')]:
                out=root/label
                env=dict(os.environ,PYTHONPATH=str(parent),S1_IMPORT_AUDIT_DIR=str(out),S1_IMPORT_AUDIT_MODULES='fixturepkg')
                result=subprocess.run([str(python),'-c','import fixturepkg; print(fixturepkg.VALUE)'],
                    cwd=workspace,capture_output=True,text=True,env=env,timeout=30)
                self.assertEqual(result.returncode,0,result.stderr)
                records=[json.loads(p.read_text()) for p in out.glob('*.json')]
                report=classify(records,workspace)
                self.assertEqual(report['status'],'outside_workspace' if label=='wrong' else 'workspace_source_executed')
                self.assertFalse(report['behavior_verified'])
                self.assertTrue(all('sys_path' in r for r in records))
                self.assertEqual(result.stdout.strip(),'foreign' if label=='wrong' else 'edited')

    def test_no_exit_evidence_does_not_certify_source(self):
        self.assertEqual(classify([dict(stage='startup')],Path('.'))['status'],'unknown')

    def test_no_module_import_is_not_verification(self):
        self.assertEqual(classify([dict(stage='exit',modules={},pid=1)],Path('.'))['status'],'not_imported')
