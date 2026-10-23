"""Seal one shared production payload; use it for CPU and both fixed batches."""
import inspect,io,json,subprocess,types,zipfile
from pathlib import Path
from .selection import HERE,ROOT,ID,sha,write
from .cpu_control import inherited_files
from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import notebook as proven
from u_re.v01.experiments.action_priority_01.real_gemma_abba02 import import_closure

PACKAGE='u_re.v02.experiments.action_first_replication_01'
PRIOR=proven.PRIOR
MODEL_SOURCE=proven.MODEL_SOURCE

def seal(quota):
    assert not (HERE/'payload.zip').exists(),'Changed production payload requires new CPU acceptance'
    selected=json.loads((HERE/'SELECTED_TASKS.json').read_bytes());assert selected['status']=='FOUR_TASKS_ADMITTED'
    old=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    order=[dict(run=2*i+j+1,instance_id=t['instance_id'],arm=a,batch=1+i//2) for i,t in enumerate(selected['tasks']) for j,a in enumerate(('A','B') if i%2==0 else ('B','A'))]
    lock=dict(old,experiment_id=ID,status='FROZEN_BEFORE_GPU',tasks=selected['tasks'],order=order,execute=False,gpu_authorized=False)
    write(HERE/'EXPERIMENT_LOCK.json',lock)
    for batch in (1,2):
        grant=dict(json.loads((proven.HERE/'GPU_AUTHORIZATION.json').read_bytes()),experiment_id=ID,execution_id=ID+'-GPU-BATCH%02d'%batch,
            slug='wudangdexiaodoashi/gemma4-u-re-v02-batch%02d'%batch,order=[r for r in order if r['batch']==batch],quota_at_dispatch_report_seconds=str(quota),
            human_message_reference='Current explicit U-RE V0.2 replication task authorizes two distinct GPU batches, each one SaveKernel and four frozen sessions; 4xL4 TP4 Gemma31B QAT v2,10000s window,300s/60tools/120command. Batch2 is not a retry of Batch1. No formal Submission.',recorded_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat())
        write(HERE/('GPU_BATCH_%02d_AUTHORIZATION.json'%batch),grant)
    files=inherited_files()
    for parent in ('u_re/v02','u_re/v02/experiments'):files[parent+'/__init__.py']=b''
    for name in ('__init__.py','selection.py','session.py','worker.py','EXPERIMENT_LOCK.json','SELECTED_TASKS.json','REPLICATION_PROTOCOL.json','TASK_POOL_FREEZE.json','GPU_BATCH_01_AUTHORIZATION.json','GPU_BATCH_02_AUTHORIZATION.json'):
        p=HERE/name;files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    complete=types.FunctionType(import_closure.complete.__code__,dict(import_closure.complete.__globals__,ENTRYPOINTS=(PACKAGE+'.session',PACKAGE+'.worker')))
    files,graph=complete(files)
    assert not any(n.endswith(('cpu_transport.py','cpu_probe.py','cpu_probe_v2.py','repair_probe.py')) for n in files)
    for n,h in old['source_pins'].items():assert sha(files[(PRIOR/n).relative_to(ROOT).as_posix()])==h
    registration=dict(execution_id=ID,production_entry=PACKAGE+'.session.run',worker_entry=PACKAGE+'.worker',files={n:sha(b) for n,b in files.items()},wheel_hashes=old['official_wheels'])
    files['gpu_registration.json']=(json.dumps(registration,indent=2)+'\n').encode()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,10,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    proven.write(HERE/'payload.zip',stream.getvalue())
    write(HERE/'PAYLOAD_MANIFEST.json',dict(payload_sha256=sha(stream.getvalue()),bytes=len(stream.getvalue()),**registration,import_closure=graph,CPU_transport_in_payload=False,frozen_tasks=selected['tasks'],frozen_order=order,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()))

def make(mode,directory,quota=None,batch=1):
    assert batch in (1,2)
    source=inspect.getsource(proven.make_notebook)
    source=source.replace('GPU03_PAYLOAD_MANIFEST.json','PAYLOAD_MANIFEST.json')
    source=source.replace("run_name='u_re_actionfirst_abba03' if gpu else directory.name", "run_name='v02-batch%02d'%BATCH if gpu else 'v02-'+directory.name")
    source=source.replace("'wudangdexiaodoashi/gemma4-u-re-abba03-'", "'wudangdexiaodoashi/gemma4-u-re-v02-'")
    source=source.replace("(HERE/'cpu_transport.py')", "(LEGACY_HERE/'cpu_transport.py')")
    source=source.replace("mode='GPU',quota_at_dispatch={str(quota)!r}","mode='GPU',quota_at_dispatch={str(quota)!r},batch={BATCH}")
    source=source.replace("selection_protocol_sha256=sha((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())", "selection_protocol_sha256=sha((HERE/'REPLICATION_PROTOCOL.json').read_bytes())")
    m=types.ModuleType('v02_shared_notebook_builder')
    m.__dict__.update(proven.__dict__)
    m.HERE=HERE;m.ID=ID+'-GPU-BATCH%02d'%batch;m.SLUG='wudangdexiaodoashi/gemma4-u-re-v02-batch%02d'%batch;m.PACKAGE=PACKAGE;m.BATCH=batch;m.LEGACY_HERE=proven.HERE
    exec(compile(source,'<adapted-GPU03-builder>','exec'),m.__dict__)
    m.make_notebook(mode,directory,quota)

def launcher(batch):
    directory=HERE/('batch%02d'%batch);slug='wudangdexiaodoashi/gemma4-u-re-v02-batch%02d'%batch
    execution_id=ID+'-GPU-BATCH%02d'%batch
    # Proven durable GPU controller: exact identity, unique claim, Retry(0),
    # CPU02 HTTP metadata-first observer. No new SDK implementation.
    from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import GPU_NOTEBOOK
    m=types.ModuleType('v02_scoped_gpu_controller');m.__file__=GPU_NOTEBOOK.__file__
    exec(compile(Path(GPU_NOTEBOOK.__file__).read_bytes(),m.__file__,'exec'),m.__dict__)
    m.HERE=directory;m.SLUG=slug;m.ID=execution_id
    controller=m.controller_module
    path=Path(GPU_NOTEBOOK.__file__).parent/'launch.py'
    source=path.read_text(encoding='utf-8').replace('from .GPU_NOTEBOOK import HERE,ROOT,SLUG,ID,MODEL_SOURCE,controller_module,sha,write','')
    source=source.replace("directory=HERE/'preflight';directory.mkdir(exist_ok=True)","directory=HERE/'preflight'/('read-'+str(len(list((HERE/'preflight').glob('read-*')))+1));directory.mkdir(parents=True,exist_ok=False)")
    source=source.replace("(HERE.parent/'integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json')","(STUDY/'EXPERIMENT_LOCK.json')")
    source=source.replace("cached=HERE/'preflight/DYNAMIC_PRECHECK.json'","cached=sorted((HERE/'preflight').glob('read-*/DYNAMIC_PRECHECK.json'))[-1]")
    source=source.replace("assert gates['remaining_report_seconds']==grant['quota_at_dispatch_report_seconds'],'Refresh build if quota changed before dispatch'", "grant['quota_at_dispatch_report_seconds']=gates['remaining_report_seconds']\n    from u_re.v02.experiments.action_first_replication_01.acceptance import verify\n    assert verify()['payload_sha256']==spec['payload_sha256']")
    t=types.ModuleType('v02_existing_gpu_launch');t.__file__=str(path)
    exec(compile(source,str(path),'exec'),t.__dict__)
    for k,v in dict(HERE=directory,STUDY=HERE,ROOT=ROOT,SLUG=slug,ID=execution_id,MODEL_SOURCE=MODEL_SOURCE,controller_module=controller,sha=sha,write=proven.write).items():setattr(t,k,v)
    return t

def collect(batch,private_root):
    directory=HERE/('batch%02d'%batch);slug='wudangdexiaodoashi/gemma4-u-re-v02-batch%02d'%batch
    path=ROOT/'u_re/v01/experiments/action_priority_01/real_gemma_abba01/collect.py'
    source=path.read_text(encoding='utf-8').replace('from .GPU_NOTEBOOK import HERE,ROOT,SLUG','').replace('u_re_actionfirst_abba01.zip','v02-batch%02d.zip'%batch)
    m=types.ModuleType('v02_existing_gpu_read');m.__file__=str(path);exec(compile(source,str(path),'exec'),m.__dict__)
    m.HERE=directory;m.ROOT=ROOT;m.SLUG=slug;m.collect(private_root)
