"""Seal CPU02 engineering readiness, not execution/admission authorization."""
import argparse
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile
from .prepare import HERE,PILOT,ROOT,write
from .launch import validate_local
from u_re.v01.experiments.fastapi_pilot_01.auth_diagnose import inventory

MANIFEST=HERE/'INTEGRITY_MANIFEST.json'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def history():
    before=json.loads((HERE/'evidence/INITIAL_HISTORY.json').read_bytes())
    for n,h in before.items():assert sha(ROOT/n)==h,'Inherited drift: '+n
    candidates=json.loads((PILOT/'CANDIDATE_INTEGRITY.json').read_bytes())['candidates']
    for n,p in candidates.items():
        path=ROOT/'u_re/v01'/('submission_'+n+'.zip');assert sha(path)==p['zip_sha256']
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            assert {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}==p['members']
    assert json.loads((PILOT/'reconciliation_01/ASSESSMENT.json').read_bytes())['status']=='SAVE_STATUS_UNKNOWN'
    spec=validate_local()
    return dict(passed=True,inherited_files_unchanged=len(before),candidates=candidates,
        CPU01_unchanged_and_UNKNOWN=True,selection_protocol_sha256=sha(PILOT/'SELECTION_PROTOCOL.json'),
        rank_sha256=sha(PILOT/'RANKED_POOL.json'),exclusion_ledger_sha256=sha(PILOT/'EXCLUSION_LEDGER_V02.json'),
        exclusion_count=79,rank_count=50,payload_sha256=spec['payload_sha256'],
        scope='Verify original frozen entries;new nested CPU02 namespace intentionally adds files without rewriting old seals')


def describe():
    h=history();assert json.loads((HERE/'HISTORY_AUDIT.json').read_bytes())==h
    assert not (HERE/'execution').exists() and not (HERE/'HTTP_RECEIPT.json').exists()
    assert not (HERE/'HTTP_METADATA.json').exists() and not (HERE/'collected').exists()
    assert json.loads((HERE/'CPU02_PRECHECK.json').read_bytes())['Gate_E']['status']=='NOT_AUTHORIZED'
    _,_,_,secrets=inventory();files={}
    for p in sorted(HERE.rglob('*')):
        if not p.is_file() or p==MANIFEST or {'__pycache__','_local','.pytest_cache'}&set(p.relative_to(HERE).parts):continue
        raw=p.read_bytes()
        for secret in secrets:
            if secret:assert secret.encode() not in raw,'Credential in new file;seal refused'
        files[p.relative_to(HERE).as_posix()]=hashlib.sha256(raw).hexdigest()
    nb=json.loads((HERE/'notebook/study.ipynb').read_bytes())
    line=next(s for s in nb['cells'][0]['source'].splitlines() if s.startswith("payload=__import__('base64').b64decode("))
    payload=base64.b64decode(ast.literal_eval(line[len("payload=__import__('base64').b64decode("):-1]))
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        for n in z.namelist():
            for secret in secrets:
                if secret:assert secret.encode() not in z.read(n),'Credential in upload payload'
    return dict(execution_id='U-RE-FASTAPI-PILOT-CPU02',state='CPU02_READY_FOR_AUTHORIZATION',
        base_commit='da207da901719285eb4c79508d2dff53187b314a',
        preparation_commit='4bf7918600cd92ec40ebeec0ee6ac0e3eb170e28',
        authorization_received=False,real_SaveKernel_dispatches=0,real_CPU02_native_checks=0,
        CPU01_actual_native_checks=None,GPU=0,Agent_runs=0,Gemma=0,formal_Submission=0,
        local_test_methods=20,tests_are_official_CPU_baselines=False,
        real_readonly_API_calls=3,HTTP_receipt_generated=False,accepted_version=None,
        inherited_files_verified=h['inherited_files_unchanged'],candidates=h['candidates'],
        credential_values_detected=False,upload_payload_credential_scan_passed=True,
        file_count=len(files),files=files,manifest_self_excluded=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--create',action='store_true');args=p.parse_args()
    if args.create:
        write(HERE/'HISTORY_AUDIT.json',history());write(MANIFEST,describe())
    else:assert json.loads(MANIFEST.read_bytes())==describe(),'CPU02 preparation seal mismatch'
    d=json.loads(MANIFEST.read_bytes())
    print(json.dumps(dict(manifest_sha256=sha(MANIFEST),state=d['state'],sealed_files=d['file_count'],
        inherited_files=d['inherited_files_verified'],authorized=False,new_SaveKernel=0)))


if __name__=='__main__':main()
