"""CPU-only executable contract for previously missing research runtime tools."""
import importlib.metadata as md
import json,shlex
from pathlib import Path
from gemma_pair.common import write
from gemma_pair.data import prepare
from gemma_pair.sandbox import SubprocessManager
from harness_v2.evidence import Journal

FIXTURE='''import pytest
@pytest.fixture
def value():return 7
@pytest.mark.parametrize('offset',[1,2])
def test_fixture_and_writable_tmp(value,offset,tmp_path):
    path=tmp_path/'value.txt'
    path.write_text(str(value+offset))
    assert int(path.read_text())==7+offset
'''
PROBES={
    'python_alias':("python -c 'import sys; print(sys.version_info[:2])'",'(3, 12)'),
    'pytest_module':('python3 -m pytest --version','pytest 8.4.2'),
    'pytest_entrypoint':('pytest --version','pytest 8.4.2'),
    'pip_module':('python3 -m pip --version','pip '),
    'pip_entrypoint':('pip --version','pip '),
    'which':('which python','/usr/bin/python'),
    'touch':('touch /workspace/runtime-touch && test -f /workspace/runtime-touch && echo TOUCH_OK','TOUCH_OK'),
    'pytest_functional':('PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q /workspace/test_runtime_surface.py','2 passed'),
}

def contract(manager,sid):
    results={}
    for name,(command,marker) in PROBES.items():
        r=manager.exec(sid,command,timeout=60)
        results[name]=dict(passed=r.exit_code==0 and marker in r.stdout,exit_code=r.exit_code,
                           stdout=r.stdout,stderr=r.stderr)
    return results

def run(out,fixer=None):
    import torch
    assert torch.cuda.device_count()==0
    out=Path(out);out.mkdir(exist_ok=False)
    fixture=out/'test_runtime_surface.py';fixture.write_text(FIXTURE,encoding='utf8')
    bindings=prepare(out/'data');rows=[]
    for task,bound in bindings.items():
        folder=out/task;folder.mkdir()
        manager=SubprocessManager(journal=Journal(folder),base_dir=folder/'roots',task_wheels=Path(bound['wheels']))
        row=dict(task=task,cleanup=False)
        try:
            sid=manager.start()
            manager.copy_to(sid,fixture,'/workspace/test_runtime_surface.py')
            positive=manager.exec(sid,"python3 -c 'print(12345)' && git --version",timeout=20)
            assert positive.exit_code==0 and '12345' in positive.stdout and 'git version' in positive.stdout
            before=contract(manager,sid);row['before']=before
            assert not any(r['passed'] for r in before.values()),'Existing missing surface unexpectedly changed'
            if fixer:
                row['repair_manifest']=fixer(manager.sandboxes[sid]['root'])
                after=contract(manager,sid);row['after']=after
                assert all(r['passed'] for r in after.values()),'Repaired runtime contract failed'
                confined=manager.exec(sid,"python -c "+shlex.quote("import os,pathlib,pytest,pip\nassert os.geteuid()!=0\nassert str(pathlib.Path(pytest.__file__).resolve()).startswith('/opt/approved/')\nassert str(pathlib.Path(pip.__file__).resolve()).startswith('/opt/approved/')\nassert not os.access('/opt/approved/pytest/__init__.py',os.W_OK)\nassert os.environ['PIP_NO_INDEX']=='1'\nprint('CONFINEMENT_RETAINED')"),timeout=20)
                assert confined.exit_code==0 and 'CONFINEMENT_RETAINED' in confined.stdout
                row['confinement_retained']=True
        finally:
            manager.cleanup_all()
            row['cleanup']=not manager.sandboxes and all(not Path(e['lease']).exists() for e in manager.entries)
            write(folder/'CONTRACT.json',row)
        assert row['cleanup'];rows.append(row)
    result=dict(passed=True,phase='GREEN' if fixer else 'RED',GPU_devices=0,Gemma_requests=0,
                scope='Research sandbox executable entrypoints and generic pytest fixtures only; full project regression not claimed',
                all_three_task_groups=True,host_distribution_versions={n:md.version(n) for n in ('pytest','pip','packaging','pluggy','iniconfig','pygments')},sessions=rows)
    write(out/'ENV_CONTRACT_RESULTS.json',result)
    print('ENV_CONTRACT_RESULTS',json.dumps(result),flush=True)
    return result
