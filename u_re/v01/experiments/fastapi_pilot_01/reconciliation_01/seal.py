"""Seal only this supplement; verify all original frozen entries unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from .query import HERE,PILOT,ROOT
from u_re.v01.experiments.fastapi_pilot_01.auth_diagnose import inventory

MANIFEST=HERE/'INTEGRITY_MANIFEST.json'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def check_history():
    rows=json.loads((HERE/'INITIAL_HISTORY.json').read_bytes())
    for n,h in rows.items():assert sha(ROOT/n)==h,'Inherited drift: '+n
    pins=json.loads((PILOT/'CANDIDATE_INTEGRITY.json').read_bytes())['candidates']
    for n,pin in pins.items():
        path=ROOT/'u_re/v01'/('submission_'+n+'.zip')
        assert sha(path)==pin['zip_sha256']
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            assert {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}==pin['members']
    original=json.loads((PILOT/'INTEGRITY_MANIFEST.json').read_bytes())
    for name,h in original['files'].items():assert sha(PILOT/name)==h,name
    return dict(passed=True,inherited_files_unchanged=len(rows),candidates=pins,
        original_pilot_manifest_sha256=sha(PILOT/'INTEGRITY_MANIFEST.json'),
        original_pilot_entries_verified=len(original['files']),
        previous_candidate_and_history_seals_unmodified=True,
        scope='New reconciliation namespace is intentionally additional; verify old seals by their frozen entry lists,not by equating expanded directory membership')


def describe():
    history=check_history()
    assert json.loads((HERE/'HISTORY_AUDIT.json').read_bytes())==history
    _,_,_,secrets=inventory();files={}
    for p in sorted(HERE.rglob('*')):
        if not p.is_file() or p==MANIFEST or {'__pycache__','download','.pytest_cache'}&set(p.relative_to(HERE).parts):continue
        raw=p.read_bytes()
        for secret in secrets:
            if secret:assert secret.encode() not in raw,'Credential detected; seal refused'
        files[p.relative_to(HERE).as_posix()]=hashlib.sha256(raw).hexdigest()
    return dict(status='SAVE_STATUS_UNKNOWN',outcome='D',
        base_commit='2b3fb4d3476dd2f0141b766528a7d4850b04aaec',
        query_commit='6c086bd2cba52758828e49d04981e7745d2a93fa',
        actual_readonly_HTTP_dispatches=5,new_SaveKernel=0,GPU=0,Gemma=0,formal_Submission=0,
        accepted_version=None,confirmed_native_results=0,actual_platform_execution_count=None,
        inherited_files_verified=history['inherited_files_unchanged'],candidates=history['candidates'],
        local_guard_evidence_tests=7,tests_are_native_baselines=False,
        credential_values_detected=False,file_count=len(files),files=files,manifest_self_excluded=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--create',action='store_true');args=p.parse_args()
    if args.create:
        with (HERE/'HISTORY_AUDIT.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(check_history(),f,indent=2);f.write('\n')
        actual=describe()
        with MANIFEST.open('x',encoding='utf-8',newline='\n') as f:json.dump(actual,f,indent=2);f.write('\n')
    else:assert json.loads(MANIFEST.read_bytes())==describe(),'Supplement seal drift'
    print(json.dumps(dict(manifest_sha256=sha(MANIFEST),inherited_files=check_history()['inherited_files_unchanged'],
        status='SAVE_STATUS_UNKNOWN',new_SaveKernel=0)))


if __name__=='__main__':main()
