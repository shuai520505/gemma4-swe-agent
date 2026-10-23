"""Reuse accepted package/controller/collector; one new GPU authorization."""
import ast,base64,inspect,io,json,subprocess,types,zipfile
from pathlib import Path
from .common import HERE,ROOT,ID,PACKAGE,BASE,write,sha
from u_re.v02.experiments.env_recovery_admission_01 import production_notebook as accepted
from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import notebook as proven
from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import GPU_NOTEBOOK as control
SLUG='wudangdexiaodoashi/gemma4-u-re-v03-context01'
MODEL_SOURCE=control.MODEL_SOURCE

def registration():
    old=json.loads((accepted.PRODUCTION/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    lock=dict(old,experiment_id=ID,tasks=old['tasks'][:2],order=[dict(run=i+1,instance_id=t,arm=a) for i,(t,a) in enumerate([('fastapi_5077','A'),('fastapi_5077','B'),('fastapi_11355','B'),('fastapi_11355','A')])])
    lock['arms']={a:dict(old['arms']['B'],policy='P0' if a=='A' else 'P1',max_output_tokens=cap) for a,cap in [('A',16384),('B',8192)]}
    policy=dict(experiment_id=ID,primary='Native Resolved',sample='MECHANISM_PILOT_PREVIOUSLY_OBSERVED_TWO_FASTAPI_TASKS',single_factor='max_output_tokens',candidate_ZIP_sha256=old['arms']['B']['ZIP_sha256'],policies={'A':dict(name='P0',output=16384,input_cap=15360),'B':dict(name='P1',output=8192,input_cap=23552)},context=32768,safety=1024,thinking=4096,seed=17,agent_seconds=300,tools=60,command_seconds=120,order=lock['order'],P2='4096 offline sensitivity only; not an executable candidate',secondary=['Guard/time/input','Output length/finish/truncation','Actual HTTP and received usage','Production edits excluding diagnostics','Supported repair and explicit submit','Native TaskResult/JUnit','Time/tool/token cost including failures'],stop=['Identity/environment/isolation/native evidence inconsistency','Insufficient window or quota','Unresolved active-resource conflict'],ordinary_failure='Continue frozen order; no task/prompt/policy hotfix',GPU=dict(max_Notebooks=1,max_sessions=4,GPUs='4xL4',TP=4,window=10000,retry=False,formal_submission=False),history='PR27 Batch2 remains UNKNOWN; this is a distinct pilot, never its retry')
    write(HERE/'CONTEXT_POLICY_FREEZE.json',policy);write(HERE/'ABBA_EXPERIMENT_LOCK.json',lock)
    write(HERE/'ADMISSION_RECONCILIATION.json',dict(status='EVIDENCE_RECONCILED_TWO_TASKS_ADMITTED',tasks=[dict(instance_id=t['instance_id']) for t in lock['tasks']],source='Original CPU archive and frozen PR26 selected task identities; native baseline reconfirmed by shared production entry'))
    return lock

def build_payload():
    assert not (HERE/'payload.zip').exists(),'Changed production payload requires a new version and CPU acceptance'
    from u_re.v02.experiments.real_gemma_replication_01.notebook import verify_shared
    verify_shared();lock=registration()
    with zipfile.ZipFile(accepted.PRODUCTION/'payload.zip') as z:files={n:z.read(n) for n in z.namelist() if n!='gpu_registration.json'}
    for n in ['u_re/v03/__init__.py','u_re/v03/experiments/__init__.py']:
        files[n]=(ROOT/n).read_bytes()
    for name in ('__init__.py','common.py','policy.py','worker.py','session.py','CONTEXT_POLICY_FREEZE.json','ABBA_EXPERIMENT_LOCK.json','ADMISSION_RECONCILIATION.json'):
        files[(HERE/name).relative_to(ROOT).as_posix()]=(HERE/name).read_bytes()
    reg=dict(execution_id=ID,production_entry=PACKAGE+'.session.run',worker_entry=PACKAGE+'.worker',files={n:sha(b) for n,b in files.items()},wheel_hashes=lock['official_wheels'])
    files['gpu_registration.json']=(json.dumps(reg,indent=2)+'\n').encode()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,10,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    raw=stream.getvalue();(HERE/'payload.zip').write_bytes(raw)
    write(HERE/'GPU03_PAYLOAD_MANIFEST.json',dict(payload_sha256=sha(raw),bytes=len(raw),**reg,source_base=BASE,CPU_transport_in_payload=False))
    return sha(raw)

def make(mode,attempt='cpu-e2e01',quota=None):
    directory=HERE/attempt;assert not (directory/'BUILD.json').exists()
    source=inspect.getsource(proven.make_notebook)
    source=source.replace("run_name='u_re_actionfirst_abba03' if gpu else directory.name","run_name='v03-context-gpu01' if gpu else 'v03-'+directory.name")
    source=source.replace("'wudangdexiaodoashi/gemma4-u-re-abba03-'+directory.name","'wudangdexiaodoashi/gemma4-u-re-v03-'+directory.name")
    source=source.replace("aux=(HERE/'cpu_transport.py').read_bytes()","aux=CPU_TRANSPORT_FILE.read_bytes()")
    source=source.replace("mode='GPU',quota_at_dispatch={str(quota)!r})","mode='GPU',quota_at_dispatch={str(quota)!r},authorization={GRANT!r})")
    if mode!='GPU':
        raw=(HERE/'cpu_transport.py').read_bytes().replace(b'ORIGINAL_CPU_TRANSPORT_BASE64',base64.b64encode((proven.HERE/'cpu_transport.py').read_bytes()))
        auxpath=directory/'CPU_ONLY_TRANSPORT.py';auxpath.parent.mkdir(parents=True,exist_ok=True);auxpath.write_bytes(raw)
    else:auxpath=None
    ns=dict(proven.__dict__,HERE=HERE,ID=ID,PACKAGE=PACKAGE,SLUG=SLUG,CPU_TRANSPORT_FILE=auxpath,GRANT=authorization() if mode=='GPU' else None)
    exec(compile(source,'<Reused-sealed-GPU03-Notebook-builder>','exec'),ns)
    ns['make_notebook'](mode,directory,quota=quota)
    if mode!='GPU':
        b=json.loads((directory/'BUILD.json').read_bytes());b['configuration']['Agent_runs']=2;write(directory/'BUILD.json',b)
    validate(attempt)

def validate(attempt):
    d=HERE/attempt;b=json.loads((d/'BUILD.json').read_bytes());raw=(HERE/'payload.zip').read_bytes()
    assert sha(raw)==b['payload_sha256']==json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())['payload_sha256']
    nb=json.loads((d/'notebook/study.ipynb').read_bytes())
    assert sha((d/'notebook/study.ipynb').read_bytes())==b['Notebook_sha256'] and sha(json.dumps(nb).encode())==b['wire_sha256']
    line=next(x for x in nb['cells'][0]['source'].splitlines() if x.startswith("payload=__import__('base64').b64decode("))
    assert base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))==raw
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        for n,h in b['payload_members'].items():assert sha(z.read(n))==h
        assert not any(n.endswith('cpu_transport.py') for n in z.namelist())
    if b['configuration']['GPU']:
        assert 'cpu_transport=' not in nb['cells'][1]['source'] and 'CPU_SCRIPTED' not in nb['cells'][1]['source']
    return True

def cpu_factory(attempt):
    from u_re.v02.experiments.action_first_replication_01 import cpu_control as prior
    source=inspect.getsource(prior.factory).replace("gemma4-u-re-v02-","gemma4-u-re-v03-").replace("'v02-'+attempt","'v03-'+attempt").replace('agent_runs==1','agent_runs==2')
    source=source.replace("if attempt.startswith('screen'):validate_screen(attempt)","validate(attempt)")
    source=source.replace('Current V02 replication human task explicitly authorizes CPU native screening max16 first4 and final production-payload CPU acceptance. No Gemma/GPU/formal Submission in this CPU dispatch.','Current V03 instruction explicitly authorizes packaged CPU production acceptance of both context policies using two owned scripted sessions and two frozen native baselines. No GPU or Gemma or Submission.')
    ns=dict(prior.__dict__,HERE=HERE,ROOT=ROOT,ID=ID,validate=validate)
    exec(compile(source,'<Reused-durable-V03-CPU-controller>','exec'),ns)
    return ns['factory'](attempt,agent_runs=2)

def authorization():
    lock=json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    return dict(experiment_id=ID,GPU_authorized=True,evidence_source='human_user_message',human_message_reference='Current V03 explicit authorization: one private GPU Notebook,4xL4 TP4 Gemma4 QATv2,exact P0/P1 four sessions,max10000seconds; no retries or Submission',max_SaveKernel_dispatches=1,max_Agent_runs=4,Agent_seconds=300,platform_window_seconds=10000,GPU_type='NVIDIA L4',GPU_count=4,TP=4,model_source=MODEL_SOURCE,order=lock['order'],policy_freeze_sha256=sha((HERE/'CONTEXT_POLICY_FREEZE.json').read_bytes()),payload_sha256=sha((HERE/'payload.zip').read_bytes()),environment_lock_sha256=lock['environment_lock_sha256'],model_files=lock['model']['files'],task_identities=lock['tasks'],retries_authorized=False,formal_submission=False)

def gpu_controller():
    ns=dict(control.__dict__,HERE=HERE/'gpu01',ID=ID,SLUG=SLUG)
    return types.FunctionType(control.controller_module.__code__,ns)()

def preflight():
    from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import launch as prior
    d=HERE/'gpu01';d.mkdir(exist_ok=True)
    source=inspect.getsource(prior.preflight)
    source=source.replace("directory=HERE/'preflight';directory.mkdir(exist_ok=True)","directory=HERE/'preflight'/('read-'+str(len(list((HERE/'preflight').glob('read-*')))+1));directory.mkdir(parents=True,exist_ok=False)")
    source=source.replace("HERE.parent/'integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json'","STUDY/'ABBA_EXPERIMENT_LOCK.json'")
    source=source.replace("remaining=Decimal(quota['totalTimeAllowed']", "assert quota.get('timeReserved')=='0s','Unresolved active resource reservation; no GPU dispatch'\n        remaining=Decimal(quota['totalTimeAllowed']")
    ns=dict(prior.__dict__,HERE=d,STUDY=HERE,ROOT=ROOT,SLUG=SLUG,write=write)
    exec(compile(source,'<Reused-V03-GPU-dynamic-preflight>','exec'),ns)
    result=ns['preflight']()
    write(d/'UNKNOWN_CARRYOVER_CHECK.json',dict(original_status='SAVE_STATUS_UNKNOWN',unknown_slug='wudangdexiaodoashi/gemma4-u-re-v02b-gemma-batch02',current_resource_conflict=False,evidence='Complete owned resource listing and recent GPU status checks; current platform timeReserved=0s. Does not establish prior rejection or absence of completed execution.',preflight_sha256=sha(json.dumps(result,sort_keys=True).encode())))
    return result

def gpu_launch():
    from datetime import datetime,timezone
    validate('gpu01');verify_cpu()
    d=HERE/'gpu01';assert not (d/'execution/dispatch.claim').exists()
    gates=json.loads(sorted((d/'preflight').glob('read-*/DYNAMIC_PRECHECK.json'))[-1].read_bytes())
    assert (datetime.now(timezone.utc)-datetime.fromisoformat(gates['HTTP'][-1]['utc'])).total_seconds()<600
    grant=authorization();b=json.loads((d/'BUILD.json').read_bytes())
    grant.update(execution_id=ID,slug=SLUG,**{k:b[k] for k in ('Notebook_sha256','wire_sha256','payload_sha256')})
    write(d/'DISPATCH_AUTHORIZATION.json',grant)
    c=gpu_controller().Controller(d/'execution',b)
    from kaggle import api
    try:c.execute(grant,gates,lambda:api.kernels_push(str(d/'notebook'),timeout='10000',acc='NvidiaL4'))
    finally:write(d/'DISPATCH_SUMMARY.json',dict(dispatches=c.dispatches,states=c.journal.states(),GPU=True,formal_submission=False))

def collect_gpu(private):
    old=ROOT/'u_re/v01/experiments/action_priority_01/real_gemma_abba01/collect.py'
    code=old.read_text(encoding='utf8').replace('from .GPU_NOTEBOOK import HERE,ROOT,SLUG','').replace('u_re_actionfirst_abba01.zip','v03-context-gpu01.zip')
    code=code.replace("len(meta['model_data_sources'] or []) == 1",repr(MODEL_SOURCE)+" in (meta['model_data_sources'] or []) and len(meta['model_data_sources'] or []) == 1")
    ns=dict(HERE=HERE/'gpu01',ROOT=ROOT,SLUG=SLUG,__name__='v03_readonly',__file__=str(old));exec(compile(code,str(old),'exec'),ns)
    ns['collect'](private)

def verify_cpu():
    from .audit import audit_cpu
    proof=json.loads((HERE/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
    assert audit_cpu(proof['raw_archive_path'],proof['attempt'])==proof
    return proof

if __name__=='__main__':
    import sys
    cmd=sys.argv[1];attempt=sys.argv[2] if len(sys.argv)>2 else 'cpu-e2e01'
    if cmd=='payload':print(build_payload())
    elif cmd=='cpu-build':make('CPU_DRY_RUN',attempt)
    elif cmd=='cpu-launch':cpu_factory(attempt).launch()
    elif cmd=='cpu-collect':cpu_factory(attempt).collect(sys.argv[3])
    elif cmd=='preflight':print(json.dumps(preflight()))
    elif cmd=='gpu-build':make('GPU','gpu01',json.loads(sorted((HERE/'gpu01/preflight').glob('read-*/DYNAMIC_PRECHECK.json'))[-1].read_bytes())['remaining_report_seconds'])
    elif cmd=='gpu-launch':gpu_launch()
    elif cmd=='gpu-collect':collect_gpu(sys.argv[2])
