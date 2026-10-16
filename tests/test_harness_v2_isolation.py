"""Safe dependency isolation regression; all installations target disposable venvs."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


class IsolationUnitTests(unittest.TestCase):
    def test_missing_pip_scripts_are_bound_to_checked_venv_python(self):
        m=importlib.import_module('harness_v2.isolation')
        with tempfile.TemporaryDirectory() as tmp:
            env=Path(tmp)/'venv'; (env/'bin').mkdir(parents=True)
            (env/'bin/python3').write_text('fixture')
            probe=dict(prefix=str(env),pip_module='/host/pip/__init__.py',python_version='3.12')
            with mock.patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps(probe),'')):
                result=m.prepare_pip_entrypoints(env)
            self.assertEqual(result['prefix'],str(env))
            for name in ('pip','pip3','pip3.12'):
                text=(env/'bin'/name).read_text()
                self.assertIn(str(env/'bin/python3'),text)
                self.assertIn('-m pip',text)
            self.assertIn('-m pytest',(env/'bin/pytest').read_text())

    def test_wrong_interpreter_prefix_is_rejected_before_installation(self):
        m=importlib.import_module('harness_v2.isolation')
        with tempfile.TemporaryDirectory() as tmp:
            env=Path(tmp)/'venv'; (env/'bin').mkdir(parents=True)
            probe=dict(prefix='/wrong/global',pip_module='/host/pip/__init__.py',python_version='3.12')
            with mock.patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps(probe),'')):
                with self.assertRaises(RuntimeError): m.prepare_pip_entrypoints(env)
            self.assertFalse((env/'bin/pip').exists())


class OfficialIsolationTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='posix','Real organizer subprocess sandbox requires /bin/bash')
    def test_missing_ensurepip_cannot_replace_host_package_across_sandboxes(self):
        from harness_v2.isolation import prepare_pip_entrypoints
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            temp=Path(tmp); host=temp/'disposable_host'
            subprocess.run([sys.executable,'-m','venv','--without-pip','--system-site-packages',str(host)],check=True,timeout=30)
            pure=next(host.glob('lib/python*/site-packages'))
            # Match the organizer fallback in a disposable parent, never mutate
            # the CPU Notebook's global installation to reproduce the defect.
            (pure/'_host_env.pth').write_text('\n'.join(p for p in sys.path if 'site-packages' in p or 'dist-packages' in p)+'\n')
            prepare_pip_entrypoints(host)
            (pure/'hv2_probe.py').write_text("MARKER='host'\n")
            dist=pure/'hv2_probe-1.0.dist-info'; dist.mkdir()
            (dist/'METADATA').write_text('Metadata-Version: 2.1\nName: hv2-probe\nVersion: 1.0\n')
            (dist/'RECORD').write_text('hv2_probe.py,,\nhv2_probe-1.0.dist-info/METADATA,,\nhv2_probe-1.0.dist-info/RECORD,,\n')
            wheel=temp/'hv2_probe-2.0-py3-none-any.whl'
            with zipfile.ZipFile(wheel,'w') as z:
                z.writestr('hv2_probe.py',"MARKER='sandbox'\n")
                z.writestr('hv2_probe-2.0.dist-info/METADATA','Metadata-Version: 2.1\nName: hv2-probe\nVersion: 2.0\n')
                z.writestr('hv2_probe-2.0.dist-info/WHEEL','Wheel-Version: 1.0\nGenerator: hv2-fixture\nRoot-Is-Purelib: true\nTag: py3-none-any\n')
                z.writestr('hv2_probe-2.0.dist-info/RECORD','hv2_probe.py,,\nhv2_probe-2.0.dist-info/METADATA,,\nhv2_probe-2.0.dist-info/WHEEL,,\nhv2_probe-2.0.dist-info/RECORD,,\n')
            driver=r'''
import json,subprocess,sys,venv
from pathlib import Path
from unittest.mock import patch
from harness_v2.official import DurableManager
from harness_v2.evidence import Journal
base,wheel=map(Path,sys.argv[1:])
manager=DurableManager(journal=Journal(base/'journal'),base_dir=base/'sandboxes')
original=venv.create
def without_pip(*args,**kwargs):
    if kwargs.get('with_pip'): raise RuntimeError('fixture: Kaggle ensurepip unavailable')
    return original(*args,**kwargs)
def marker():
    return subprocess.check_output([sys.executable,'-c','import hv2_probe; print(hv2_probe.MARKER)'],text=True).strip()
with patch('swegemma.sandbox.subprocess.venv.create',side_effect=without_pip):
    before=marker(); sid=manager.start()
    try:
        manager.copy_to(sid,wheel,'/tmp/'+wheel.name)
        result=manager.exec(sid,'pip install --no-index --no-deps --force-reinstall /tmp/'+wheel.name)
        assert result.exit_code==0,(result.stdout,result.stderr)
        child=manager.exec(sid,"python -c 'import hv2_probe; print(hv2_probe.MARKER)'").stdout.strip()
        workspace=manager.sandboxes[sid]['workspace']
        (workspace/'test_isolated.py').write_text("def test_marker():\n import hv2_probe\n assert hv2_probe.MARKER=='sandbox'\n")
        checked=manager.exec(sid,'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -p no:cacheprovider test_isolated.py')
        assert checked.exit_code==0,(checked.stdout,checked.stderr)
    finally: manager.stop(sid)
    after=marker(); sid=manager.start()
    try:
        following=manager.exec(sid,"python -c 'import hv2_probe; print(hv2_probe.MARKER)'").stdout.strip()
    finally: manager.stop(sid)
print(json.dumps(dict(before=before,child=child,after=after,following=following)))
'''
            env=dict(os.environ,PYTHONPATH=str(root))
            result=subprocess.run([str(host/'bin/python3'),'-c',driver,str(temp/'driver'),str(wheel)],env=env,
                text=True,capture_output=True,timeout=90)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(json.loads(result.stdout.splitlines()[-1]),dict(before='host',child='sandbox',after='host',following='host'))


if __name__=='__main__': unittest.main()
