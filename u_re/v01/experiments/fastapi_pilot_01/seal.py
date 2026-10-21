"""Exclusive byte seal: inherited files/candidates/new evidence, never credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from .register import HERE,ROOT,PREVIOUS
from .auth_diagnose import inventory

IGNORED={'__pycache__','_local','download','.pytest_cache'}
MANIFEST=HERE/'INTEGRITY_MANIFEST.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def describe():
    history=json.loads((HERE/'evidence/INITIAL_HISTORY.json').read_bytes())
    for name,h in history.items():assert sha(ROOT/name)==h,'Historical drift: '+name
    candidates=json.loads((HERE/'CANDIDATE_INTEGRITY.json').read_bytes())['candidates']
    for name,pin in candidates.items():
        path=ROOT/'u_re/v01'/('submission_'+name+'.zip')
        assert sha(path)==pin['zip_sha256']
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            assert {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}==pin['members']
    _,_,_,secrets=inventory()
    files={}
    for p in sorted(HERE.rglob('*')):
        if not p.is_file() or p==MANIFEST or set(p.relative_to(HERE).parts)&IGNORED:continue
        raw=p.read_bytes()
        for secret in secrets:
            if secret:assert secret.encode() not in raw,'Credential detected; refuse seal'
        files[p.relative_to(HERE).as_posix()]=hashlib.sha256(raw).hexdigest()
    return dict(experiment_id='U-RE-V01-FASTAPI-PILOT-01',status='TASK_ADMISSION_BLOCKED',
        execution_stop='CPU_SAVE_UNCONFIRMED_STOP',auth_status='AUTH_READONLY_GO',
        base_commit='582a016fb0c836222b6a3d653bb732e0c5e6130d',
        selection_commit='77ad02301c5c3b490d8f28fc3c397a5531854618',
        CPU_build_commit='e6db9ac349c8f521f63fc3d9ca7c0cac29b34197',
        inherited_files_verified=len(history),inherited_inventory='evidence/INITIAL_HISTORY.json',
        candidates=candidates,selected_tasks=[],confirmed_native_baselines=0,
        actual_platform_native_baselines=None,SaveKernel_dispatches=1,SaveKernel_retries=0,
        accepted_Notebook_version=None,GPU_runs=0,Gemma_inference=0,formal_submissions=0,
        local_test_methods_passed=14,local_tests_are_native_baselines=False,
        credential_values_detected=False,file_count=len(files),files=files,
        manifest_self_excluded=True,excluded_directories=sorted(IGNORED))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--create',action='store_true');args=parser.parse_args()
    actual=describe()
    if args.create:
        with MANIFEST.open('x',encoding='utf-8',newline='\n') as f:json.dump(actual,f,indent=2);f.write('\n')
    else:assert json.loads(MANIFEST.read_bytes())==actual,'Seal drift; never overwrite an existing manifest'
    print(json.dumps(dict(manifest_sha256=sha(MANIFEST),new_files=actual['file_count'],
                         inherited_files=actual['inherited_files_verified'],credentials_detected=False,
                         status=actual['status'],CPU_stop=actual['execution_stop'])))


if __name__=='__main__':main()
