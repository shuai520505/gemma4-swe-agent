"""Offline CPU02 packaging; exact CPU01 evaluator payload, independent paths."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
PILOT=HERE.parents[1]
ROOT=PILOT.parents[3]
BASE='da207da901719285eb4c79508d2dff53187b314a'


def sha(data):return hashlib.sha256(data).hexdigest()


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=data if isinstance(data,bytes) else (json.dumps(data,indent=2)+'\n').encode() if not isinstance(data,str) else data.encode()
    with path.open('xb') as f:f.write(raw)


def build():
    from .dispatch import EXECUTION_ID,SLUG
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    nb=json.loads((PILOT/'notebooks/cpu01/study.ipynb').read_bytes())
    original=json.loads((PILOT/'registrations/cpu01_build.json').read_bytes())
    assert sha((PILOT/'notebooks/cpu01/study.ipynb').read_bytes())==original['notebook_sha256']
    line=next(l for l in nb['cells'][0]['source'].splitlines() if l.startswith("payload=__import__('base64').b64decode("))
    payload=base64.b64decode(ast.literal_eval(line[len("payload=__import__('base64').b64decode("):-1]))
    assert sha(payload)==original['payload_sha256']
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        assert z.testzip() is None
        for n in ('SELECTION_PROTOCOL.json','RANKED_POOL.json','EXCLUSION_LEDGER_V02.json','TASK_POOL_METADATA.json','screen.py'):
            path=PILOT/n;assert z.read(path.relative_to(ROOT).as_posix())==path.read_bytes()
        count=len(z.namelist())
    rows=json.loads((PILOT/'RANKED_POOL.json').read_bytes())['rows']
    protocol=json.loads((PILOT/'SELECTION_PROTOCOL.json').read_bytes())
    assert len(rows)==50 and protocol['selection_algorithm']['max_cpu_checks']==8
    assert len(json.loads((PILOT/'EXCLUSION_AUDIT.json').read_bytes())['excluded_task_ids'])==79
    before=nb['cells'][0]['source']
    after=before.replace("Path('/kaggle/working/u_re_fastapi_pilot01')/'cpu01'/","Path('/kaggle/working/u_re_fastapi_pilot01')/'cpu02'/")
    assert before!=after and "Path('/kaggle/working/u_re_fastapi_pilot01')/'cpu01'/" not in after
    after+="\nimport torch\nassert torch.cuda.device_count()==0,'CPU02 requires zero GPU'\nprint('CPU02_EXECUTION_ID','U-RE-FASTAPI-PILOT-CPU02',flush=True)\n"
    nb['cells'][0]['source']=after
    for c in nb['cells']:
        compile(c['source'],'<CPU02>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        c['id']=sha(c['source'].encode())[:12]
    raw=(json.dumps(nb,indent=1)+'\n').encode()
    metadata=json.loads((PILOT/'notebooks/cpu01/kernel-metadata.json').read_bytes())
    metadata.update(id=SLUG,title=SLUG.split('/')[1])
    write(HERE/'notebook/study.ipynb',raw)
    write(HERE/'notebook/kernel-metadata.json',metadata)
    spec=dict(execution_id=EXECUTION_ID,slug=SLUG,base_commit=BASE,max_dispatches=1,
        Notebook_sha256=sha(raw),wire_sha256=sha(json.dumps(nb).encode()),payload_sha256=sha(payload),
        selection_protocol_sha256=sha((PILOT/'SELECTION_PROTOCOL.json').read_bytes()),
        metadata_sha256=sha((HERE/'notebook/kernel-metadata.json').read_bytes()),
        configuration=dict(GPU=False,TPU=False,internet=False,model_sources=[],Agent_runs=0,Gemma_calls=0,formal_submission=False),
        expected_candidates_in_order=[r['instance_id'] for r in rows[:8]],
        max_native_checks=8,select='first two baseline-eligible distinctIDs; skip none by repository',
        sdk_versions=dict(kaggle='2.2.2',kagglesdk='0.1.35'),payload_member_count=count,
        requested_CPU_window_seconds=7200,worker_deadline_seconds=6000,native_verification_seconds=300,
        payload_identical_to_CPU01=True,CPU01_save_status='SAVE_STATUS_UNKNOWN',
        authorization_received=False,save_dispatches_actual=0)
    write(HERE/'BUILD_FREEZE.json',spec)
    paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().strip('\0').split('\0')
    write(HERE/'evidence/INITIAL_HISTORY.json',{n:sha((ROOT/n).read_bytes()) for n in paths})
    write(HERE/'.gitignore','__pycache__/\n_local/\n')
    print(json.dumps(spec,indent=2))


if __name__=='__main__':build()
