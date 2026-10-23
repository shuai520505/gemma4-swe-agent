"""Reuse GPU03 packaged-payload E2E builder and durable CPU dispatch, no GPU path."""
import ast,base64,inspect,io,json,subprocess,types,zipfile
from pathlib import Path
from .dependencies import HERE,ROOT,ID,sha,write
from . import notebook as screening
from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import notebook as proven
from u_re.v02.experiments.action_first_replication_01 import cpu_control as prior

PRODUCTION=HERE/'production'
PACKAGE='u_re.v02.experiments.env_recovery_admission_01.production'

def registration():
    selected=json.loads((HERE/'SELECTED_TASKS.json').read_bytes())
    assert selected['status']=='FOUR_TASKS_FORMALLY_ADMITTED' and len(selected['tasks'])==4
    lock=json.loads((proven.PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    lock.update(experiment_id=ID,status='FOUR_TASKS_CPU_ADMITTED_GPU_NOT_AUTHORIZED',execute=False,gpu_authorized=False,tasks=[],order=[],environment_lock_sha256=sha((HERE/'V02B_ENVIRONMENT_LOCK.json').read_bytes()),selection_protocol_sha256=sha((HERE/'V02B_PROTOCOL_LOCK.json').read_bytes()))
    for i,row in enumerate(selected['tasks']):
        task=dict(row['identity'],native_baseline_counts=row['native_baseline_counts'],native_baseline_exit_code=1,role=row['role'],JUnit_sha256=row['JUnit_sha256'],native_TaskResult_sha256=row['TaskResult_sha256'])
        lock['tasks'].append(task)
        for arm in (('A','B') if i%2==0 else ('B','A')):lock['order'].append(dict(run=len(lock['order'])+1,instance_id=row['instance_id'],arm=arm,batch=i//2+1))
    write(PRODUCTION/'ABBA_EXPERIMENT_LOCK.json',lock)
    write(PRODUCTION/'ADMISSION_RECONCILIATION.json',dict(status='EVIDENCE_RECONCILED_FOUR_TASKS_ADMITTED',tasks=selected['tasks'],selected_manifest_sha256=sha((HERE/'SELECTED_TASKS.json').read_bytes())))
    write(PRODUCTION/'GPU_AUTHORIZATION.json',dict(GPU_authorized=False,order=lock['order'],Agent_seconds=300,platform_window_seconds=10000,reason='CPU-only current authorization. Old unused V02 GPU authorization is not reused.'))

def build(attempt='e2e01'):
    assert not (HERE/attempt/'execution/dispatch.claim').exists()
    assert not (PRODUCTION/'payload.zip').exists(),'Version changed production bytes explicitly; never overwrite an accepted payload'
    registration()
    with zipfile.ZipFile(HERE/'screen01/payload.zip') as z:files={n:z.read(n) for n in z.namelist() if n!='gpu_registration.json'}
    for p in PRODUCTION.iterdir():
        if p.is_file() and p.suffix in ('.py','.json'):files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    # Old GPU03 CPU transport remains external; production contains no scripted backend.
    assert not any(n.endswith('cpu_transport.py') for n in files)
    lock=json.loads((PRODUCTION/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    registration_data=dict(execution_id=ID,production_entry=PACKAGE+'.session.run',worker_entry='u_re.v01.experiments.action_priority_01.real_gemma_abba03.worker',files={n:sha(v) for n,v in files.items()},wheel_hashes=lock['official_wheels'])
    files['gpu_registration.json']=(json.dumps(registration_data,indent=2)+'\n').encode()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,10,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,v)
    payload=stream.getvalue();(PRODUCTION/'payload.zip').write_bytes(payload)
    write(PRODUCTION/'GPU03_PAYLOAD_MANIFEST.json',dict(payload_sha256=sha(payload),bytes=len(payload),**registration_data,CPU_transport_in_payload=False,frozen_tasks=lock['tasks'],frozen_order=lock['order'],source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()))
    build_cpu_notebook(attempt)

def build_cpu_notebook(attempt):
    assert not (HERE/attempt/'execution/dispatch.claim').exists()
    assert not (HERE/attempt/'BUILD.json').exists(),'Use a new CPU attempt identity instead of overwriting a sealed Notebook'
    make=inspect.getsource(proven.make_notebook)
    make=make.replace("else directory.name","else 'v02b-'+directory.name").replace("gemma4-u-re-abba03-","gemma4-u-re-v02b-")
    make=make.replace("aux=(HERE/'cpu_transport.py').read_bytes()","aux=CPU_TRANSPORT_FILE.read_bytes()")
    namespace=dict(proven.__dict__,HERE=PRODUCTION,ID=ID,PACKAGE=PACKAGE,CPU_TRANSPORT_FILE=proven.HERE/'cpu_transport.py')
    exec(compile(make,'<Reused-GPU03-CPU-Notebook-builder>','exec'),namespace)
    namespace['make_notebook']('CPU_DRY_RUN',HERE/attempt)
    write(HERE/attempt/'SOURCE_COMMIT.json',dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()))
    validate(attempt)

def validate(attempt):
    b=json.loads((HERE/attempt/'BUILD.json').read_bytes());manifest=json.loads((PRODUCTION/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())
    raw=(PRODUCTION/'payload.zip').read_bytes();assert sha(raw)==b['payload_sha256']==manifest['payload_sha256']
    nb=json.loads((HERE/attempt/'notebook/study.ipynb').read_bytes());assert sha((HERE/attempt/'notebook/study.ipynb').read_bytes())==b['Notebook_sha256']
    assert b['configuration']['GPU'] is False and b['configuration']['Agent_runs']==1 and b['configuration']['Gemma_calls']==0
    line=next(s for s in nb['cells'][0]['source'].splitlines() if s.startswith("payload=__import__('base64').b64decode("))
    assert base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))==raw
    assert 'shutil' in nb['cells'][0]['source'].splitlines()[0]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        for n,h in manifest['files'].items():assert sha(z.read(n))==h,n
        for n in ('session.py','ABBA_EXPERIMENT_LOCK.json','ADMISSION_RECONCILIATION.json','GPU_AUTHORIZATION.json'):assert PRODUCTION.relative_to(ROOT).as_posix()+'/'+n in z.namelist()
        assert not any(n.endswith('cpu_transport.py') for n in z.namelist())
        for name,h in json.loads((HERE/'V02B_PROTOCOL_LOCK.json').read_bytes())['execution_sources'].items():assert sha(z.read((HERE/name).relative_to(ROOT).as_posix()))==h
        assert not json.loads(z.read((PRODUCTION/'GPU_AUTHORIZATION.json').relative_to(ROOT).as_posix()))['GPU_authorized']
    return True

def factory(attempt='e2e01'):
    source=inspect.getsource(prior.factory).replace("gemma4-u-re-v02-","gemma4-u-re-v02b-").replace("'v02-'+attempt","'v02b-'+attempt")
    source=source.replace("if attempt.startswith('screen'):validate_screen(attempt)","validate(attempt)")
    source=source.replace('Current V02 replication human task explicitly authorizes CPU native screening max16 first4 and final production-payload CPU acceptance. No Gemma/GPU/formal Submission in this CPU dispatch.','Current V02b task authorizes final packaged production CPU acceptance: four frozen native baselines and one owned synthetic scripted Agent. No real Gemma, GPU or formal Submission.')
    namespace=dict(prior.__dict__,HERE=HERE,ROOT=ROOT,ID=ID,validate=validate)
    exec(compile(source,'<Reused-durable-V02b-E2E-controller>','exec'),namespace)
    return namespace['factory'](attempt,agent_runs=1)

if __name__=='__main__':
    import sys
    cmd=sys.argv[1];attempt=sys.argv[2] if len(sys.argv)>2 else 'e2e01'
    if cmd=='build':build(attempt)
    elif cmd=='build-cpu':build_cpu_notebook(attempt)
    elif cmd=='launch':factory(attempt).launch()
    elif cmd=='collect':factory(attempt).collect(sys.argv[3])
