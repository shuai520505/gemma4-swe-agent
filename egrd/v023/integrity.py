"""Recheck private provenance and freeze public CPU/source research integrity."""
import json
from pathlib import Path
import subprocess

from .cli_recovery import HERE, ROOT, PRIVATE, sha

BASE='e11b28c99bec91049aec68119fead5e13fa68373'


def record(raw):
    return dict(sha256=sha(raw),bytes=len(raw))


def manifest():
    excluded={'payload.zip','study.ipynb','INTEGRITY_MANIFEST.json'}
    files={p.relative_to(HERE).as_posix():record(p.read_bytes()) for p in sorted(HERE.rglob('*'))
        if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded}
    references={}
    for name in ('egrd/v022/submission_N.zip','egrd/v022/submission_D.zip',
        'egrd/v022/CANDIDATE_MANIFEST.json','egrd/v022/TASK_POOL_LOCK.json',
        'egrd/v022/GPU_EXECUTION_LOCK.json','egrd/v022/INTEGRITY_MANIFEST.json',
        'meer/v01/OFFICIAL_SOURCE_PINS.json','meer/v01/cpu03/BUILD.json',
        'meer/v01/cpu03/payload.zip','meer/v01/cpu_acceptance.py','meer/v01/verify.py','s1/prepare.py',
        'submission.zip','meer/v01/submission_A.zip','meer/v01/submission_B.zip','meer/v01/submission_C.zip'):
        raw=(ROOT/name).read_bytes()
        assert raw==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
        references[name]=record(raw)
    build=json.loads((HERE/'cpu-v1/BUILD.json').read_bytes())
    assert build['payload_members']['egrd/v023/cpu_acceptance.py']==sha((HERE/'cpu_acceptance.py').read_bytes())
    private=[]
    # Only path/hash/size exported: no token, private data or signed URL content.
    for p in sorted(PRIVATE.rglob('*')):
        if p.is_file():
            private.append(dict(path_relative_to_workspace=p.relative_to(ROOT.parent).as_posix(),**record(p.read_bytes())))
    return dict(schema='EGRD_V023_INTEGRITY_V1',source_base_PR36=BASE,
        source_parent='765530b39a7666a78ece099756fac925a932c617',
        files=files,historical_read_only_references=references,private_artifact_index=private,
        excludes=['manifest self hash','__pycache__','upload payload.zip and study.ipynb (private/ignored; BUILD and raw index bind their identities)'],
        scope='CPU-only engineering recovery and external source feasibility; zero real-model inference or new task admission')


if __name__=='__main__':
    result=manifest()
    path=HERE/'INTEGRITY_MANIFEST.json'
    if path.exists():assert json.loads(path.read_bytes())==result,'Frozen integrity record differs'
    else:path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8',newline='\n')
    print('Public and historical/private provenance verified:',len(result['files']),'public files')
