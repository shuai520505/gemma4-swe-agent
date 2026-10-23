"""Two authorized GPU batches, exact CPU-accepted shared ZIP, reused controls."""
import ast,base64,inspect,io,json,subprocess,types,zipfile
from datetime import datetime,timezone
from pathlib import Path
from u_re.v02.experiments.env_recovery_admission_01 import production_notebook as accepted
from u_re.v02.experiments.env_recovery_admission_01.production_audit import audit as cpu_audit
from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import notebook as proven
from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import GPU_NOTEBOOK as control

HERE=Path(__file__).resolve().parent;ROOT=accepted.ROOT;PREP=accepted.HERE;PRODUCTION=accepted.PRODUCTION
ID='U-RE-V02B-REAL-GEMMA-REPLICATION'
sha=accepted.sha;write=control.write
PAYLOAD_SHA='815d51b0528934283823c7469f42503fb6f388fc406c9e0870a46276be398e63'
BASE='def9c7a46c95a852f48feeafeb7017a00fb8a489'
MODEL_SOURCE=control.MODEL_SOURCE

def location(batch):
    assert batch in (1,2)
    return HERE/f'batch{batch:02d}','wudangdexiaodoashi/gemma4-u-re-v02b-gemma-batch'+f'{batch:02d}',ID+f'-BATCH{batch:02d}'

def verify_shared():
    proof=json.loads((PREP/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
    assert cpu_audit(proof['raw_archive_path'],proof['attempt'])==proof
    assert proof['payload_sha256']==sha((PRODUCTION/'payload.zip').read_bytes())==PAYLOAD_SHA
    lock=json.loads((PRODUCTION/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    assert [t['instance_id'] for t in lock['tasks']]==['fastapi_5077','fastapi_11355','fastapi_14463','fastapi_9555']
    assert [r['arm'] for r in lock['order']]==list('ABBAABBA')
    with zipfile.ZipFile(PRODUCTION/'payload.zip') as z:
        assert z.testzip() is None
        for n,h in json.loads((PRODUCTION/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())['files'].items():assert sha(z.read(n))==h,n
        for name,expected in [('u_re/v01/submission_noegv.zip',lock['arms']['A']['ZIP_sha256']),('u_re/v01/experiments/action_priority_01/submission_action_v01.zip',lock['arms']['B']['ZIP_sha256'])]:assert sha(z.read(name))==sha((ROOT/name).read_bytes())==expected
        assert not any(n.endswith('cpu_transport.py') for n in z.namelist())
    assert sha((PREP/'V02B_ENVIRONMENT_LOCK.json').read_bytes())==lock['environment_lock_sha256']
    return lock,proof

def authorize():
    lock,proof=verify_shared()
    # The accepted adapter's experiment_id binds its preparation lock. The
    # independent execution ID below names this newly authorized study.
    record=dict(execution_experiment_id=ID,experiment_id=lock['experiment_id'],GPU_authorized=True,evidence_source='human_user_message',human_message_reference='Current explicit V02b two-batch GPU instruction: max2 new private GPU Notebooks,8 total genuine Agent Sessions; exact four tasks and ABBAABBA order; no GPU retry or Competition Submission.',source_base=BASE,environment_lock_sha256=lock['environment_lock_sha256'],production_payload_sha256=PAYLOAD_SHA,CPU_acceptance_raw_sha256=proof['raw_archive_sha256'],task_lock_sha256=sha((PRODUCTION/'ABBA_EXPERIMENT_LOCK.json').read_bytes()),selected_tasks_sha256=sha((PREP/'SELECTED_TASKS.json').read_bytes()),frozen_order=lock['order'],arms=lock['arms'],model_files=lock['model']['files'],model_source=MODEL_SOURCE,GPU='4xNVIDIA L4',GPU_type='NVIDIA L4',GPU_count=4,TP=4,Agent_seconds=300,max_batches=2,max_sessions_per_batch=4,max_Agent_sessions=8,platform_window_seconds=10000,charged_tools=60,command_seconds=120,context=32768,max_output_tokens=16384,thinking=4096,safety=1024,input_cap=15360,seed=17,retries_authorized=False,formal_submission=False)
    write(HERE/'GPU_AUTHORIZATION_RECORD.json',record)
    return record

def controller(batch):
    directory,slug,execution_id=location(batch)
    m=types.ModuleType('v02b_reused_GPU_controller');m.__dict__.update(control.__dict__)
    m.HERE=directory;m.ID=execution_id;m.SLUG=slug
    return types.FunctionType(control.controller_module.__code__,m.__dict__)()

def preflight(batch):
    verify_shared();directory,slug,execution_id=location(batch);directory.mkdir(parents=True,exist_ok=True)
    if batch==2:
        proof=json.loads((HERE/'BATCH_01_EXECUTION.json').read_bytes())
        assert proof['integrity_complete'] and proof['completed_sessions']==4,'Batch1 integrity gate; Batch2 is never its retry'
    path=ROOT/'u_re/v01/experiments/action_priority_01/real_gemma_abba01/launch.py'
    source=inspect.getsource(__import__('u_re.v01.experiments.action_priority_01.real_gemma_abba01.launch',fromlist=['preflight']).preflight)
    source=source.replace("directory=HERE/'preflight';directory.mkdir(exist_ok=True)","directory=HERE/'preflight'/('read-'+str(len(list((HERE/'preflight').glob('read-*')))+1));directory.mkdir(parents=True,exist_ok=False)")
    source=source.replace("HERE.parent/'integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json'","PRODUCTION/'ABBA_EXPERIMENT_LOCK.json'")
    if batch==1:source=source.replace('assert remaining>=20600','assert remaining>=41200')
    original=__import__('u_re.v01.experiments.action_priority_01.real_gemma_abba01.launch',fromlist=['preflight'])
    namespace=dict(original.__dict__,HERE=directory,ROOT=ROOT,SLUG=slug,PRODUCTION=PRODUCTION)
    exec(compile(source,str(path),'exec'),namespace)
    return namespace['preflight']()

def build(batch):
    directory,slug,execution_id=location(batch);assert not (directory/'execution/dispatch.claim').exists()
    lock,proof=verify_shared();grant=json.loads((HERE/'GPU_AUTHORIZATION_RECORD.json').read_bytes())
    gates=json.loads(sorted((directory/'preflight').glob('read-*/DYNAMIC_PRECHECK.json'))[-1].read_bytes())
    assert (datetime.now(timezone.utc)-datetime.fromisoformat(gates['HTTP'][-1]['utc'])).total_seconds()<600
    source=inspect.getsource(proven.make_notebook)
    source=source.replace("run_name='u_re_actionfirst_abba03' if gpu else directory.name", "run_name='v02b-gemma-batch'+str(BATCH).zfill(2) if gpu else directory.name")
    needle="mode='GPU',quota_at_dispatch={str(quota)!r})"
    assert source.count(needle)==1
    source=source.replace(needle,"mode='GPU',quota_at_dispatch={str(quota)!r},authorization={GRANT!r},batch={BATCH})")
    namespace=dict(proven.__dict__,HERE=PRODUCTION,ID=execution_id,SLUG=slug,PACKAGE='u_re.v02.experiments.env_recovery_admission_01.production',GRANT=grant,BATCH=batch)
    exec(compile(source,'<Reused-GPU03-builder-external-V02b-authorization>','exec'),namespace)
    namespace['make_notebook']('GPU',directory,quota=gates['remaining_report_seconds'])
    write(directory/'SOURCE_BINDING.json',dict(execution_experiment_id=ID,batch=batch,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),shared_payload_sha256=PAYLOAD_SHA,external_authorization_sha256=sha((HERE/'GPU_AUTHORIZATION_RECORD.json').read_bytes()),order=[r for r in lock['order'] if r['batch']==batch],preflight_snapshot=gates))
    validate(batch)

def validate(batch):
    lock,proof=verify_shared();directory,slug,execution_id=location(batch)
    b=json.loads((directory/'BUILD.json').read_bytes());nb=json.loads((directory/'notebook/study.ipynb').read_bytes())
    assert b['payload_sha256']==PAYLOAD_SHA and sha((directory/'notebook/study.ipynb').read_bytes())==b['Notebook_sha256']
    assert sha(json.dumps(nb).encode())==b['wire_sha256']
    line=next(x for x in nb['cells'][0]['source'].splitlines() if x.startswith("payload=__import__('base64').b64decode("))
    assert sha(base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1])))==PAYLOAD_SHA
    assert 'CPU_SCRIPTED' not in nb['cells'][1]['source'] and 'cpu_transport=' not in nb['cells'][1]['source']
    call=next(n for n in ast.walk(ast.parse(nb['cells'][1]['source'])) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='run')
    args={k.arg:ast.literal_eval(k.value) for k in call.keywords}
    assert args['mode']=='GPU' and args['batch']==batch and args['authorization']==json.loads((HERE/'GPU_AUTHORIZATION_RECORD.json').read_bytes())
    controller(batch).checked_config(b)
    return True

def launch(batch):
    validate(batch);directory,slug,execution_id=location(batch)
    assert not (directory/'execution/dispatch.claim').exists(),'Never resend an existing dispatch'
    gates=json.loads(sorted((directory/'preflight').glob('read-*/DYNAMIC_PRECHECK.json'))[-1].read_bytes())
    assert (datetime.now(timezone.utc)-datetime.fromisoformat(gates['HTTP'][-1]['utc'])).total_seconds()<600
    b=json.loads((directory/'BUILD.json').read_bytes());grant=json.loads((HERE/'GPU_AUTHORIZATION_RECORD.json').read_bytes())
    grant.update(execution_id=execution_id,slug=slug,max_SaveKernel_dispatches=1,max_Agent_runs=4,quota_at_dispatch_report_seconds=gates['remaining_report_seconds'],**{k:b[k] for k in ('Notebook_sha256','wire_sha256','payload_sha256')})
    write(directory/'DISPATCH_AUTHORIZATION.json',grant)
    c=controller(batch).Controller(directory/'execution',b)
    from kaggle import api
    try:
        value=c.execute(grant,gates,lambda:api.kernels_push(str(directory/'notebook'),timeout='10000',acc='NvidiaL4'))
        write(directory/'SDK_SAFE_RESULT.json',dict(Notebook_id=getattr(value,'kernel_id',None),version=getattr(value,'version_number',None),ref=getattr(value,'ref',None)))
    finally:write(directory/'DISPATCH_SUMMARY.json',dict(dispatches=c.dispatches,states=c.journal.states(),GPU=True,formal_submission=False,batch=batch))

def collect(batch,private_root):
    directory,slug,_=location(batch)
    old=ROOT/'u_re/v01/experiments/action_priority_01/gpu_readiness_01/collect_capabilities.py'
    source=old.read_text(encoding='utf8').replace('from .cpu_probe_notebook import CPU,ROOT,SLUG','CPU=None;ROOT=None;SLUG=None')
    archive='v02b-gemma-batch'+f'{batch:02d}'+'.zip'
    source=source.replace("('u_re_isolation_cap01.zip','u_re_isolation_canary01.zip')",repr((archive,)))
    m=types.ModuleType('V02b_version_bound_readonly');m.__file__=str(old);exec(compile(source,str(old),'exec'),m.__dict__);m.ROOT=ROOT
    m.collect(private_root,cpu=directory,slug=slug,archive=archive)

if __name__=='__main__':
    import sys
    cmd=sys.argv[1]
    if cmd=='authorize':authorize()
    else:
        batch=int(sys.argv[2])
        if cmd=='preflight':print(json.dumps(preflight(batch)))
        elif cmd=='build':build(batch)
        elif cmd=='validate':print(validate(batch))
        elif cmd=='launch':launch(batch)
        elif cmd=='collect':collect(batch,sys.argv[3])
