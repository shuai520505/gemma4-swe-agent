"""One frozen production ZIP for CPU entrypoint acceptance and authorized GPU03."""
import ast,base64,io,json,subprocess,types,zipfile,importlib.metadata
from pathlib import Path
from ..real_gemma_abba01.GPU_NOTEBOOK import ROOT,PRIOR,MODEL_SOURCE,sha,write
from ..real_gemma_abba01.repair import corrected_files
from ..real_gemma_abba02 import import_closure

HERE=Path(__file__).resolve().parent
ID='U-RE-V01-ACTION-FIRST-01-GPU03'
SLUG='wudangdexiaodoashi/gemma4-u-re-actionfirst-abba03'
PACKAGE='u_re.v01.experiments.action_priority_01.real_gemma_abba03'

def controller_module():
    from ..real_gemma_abba01 import GPU_NOTEBOOK
    source=Path(GPU_NOTEBOOK.__file__).read_text(encoding='utf-8')
    m=types.ModuleType('gpu03_once');m.__file__=GPU_NOTEBOOK.__file__
    exec(compile(source,m.__file__,'exec'),m.__dict__)
    m.HERE=HERE;m.ID=ID;m.SLUG=SLUG
    return m.controller_module()

def launcher():
    old=HERE.parent/'real_gemma_abba01/launch.py';source=old.read_text(encoding='utf-8')
    source=source.replace('from .GPU_NOTEBOOK import HERE,ROOT,SLUG,ID,MODEL_SOURCE,controller_module,sha,write','')
    source=source.replace("directory=HERE/'preflight';directory.mkdir(exist_ok=True)","directory=HERE/'preflight'/('read-'+str(len(list((HERE/'preflight').glob('read-*')))+1));directory.mkdir(parents=True,exist_ok=False)")
    a=source.index("    cached=HERE/'preflight/DYNAMIC_PRECHECK.json'");b=source.index("    gates['source_commit']",a)
    source=source[:a]+"    cached=sorted((HERE/'preflight').glob('read-*/DYNAMIC_PRECHECK.json'))[-1]\n    gates=json.loads(cached.read_bytes())\n    assert (datetime.now(timezone.utc)-datetime.fromisoformat(gates['HTTP'][-1]['utc'])).total_seconds()<600,'Refresh dynamic check and seal the Notebook before dispatch'\n"+source[b:]
    source=source.replace("    assert gates['remaining_report_seconds']==grant['quota_at_dispatch_report_seconds'],'Refresh build if quota changed before dispatch'", "    grant['quota_at_dispatch_report_seconds']=gates['remaining_report_seconds']\n    from u_re.v01.experiments.action_priority_01.real_gemma_abba03.cpu_acceptance import verify\n    acceptance=verify()\n    assert acceptance['payload_sha256']==spec['payload_sha256']")
    m=types.ModuleType('gpu03_existing_launcher');m.__file__=str(old);exec(compile(source,str(old),'exec'),m.__dict__)
    for k,v in dict(HERE=HERE,ROOT=ROOT,SLUG=SLUG,ID=ID,MODEL_SOURCE=MODEL_SOURCE,controller_module=controller_module,sha=sha,write=write,make_notebook=make_notebook).items():setattr(m,k,v)
    return m

def build_payload():
    assert not (HERE/'payload.zip').exists(),'A changed production payload needs a new CPU acceptance version'
    files=corrected_files()
    files['u_re/v01/experiments/action_priority_01/real_gemma_abba01/GPU_AUTHORIZATION.json']=b'{"GPU_authorized":false,"scope":"LIBRARY_ONLY"}\n'
    for name in ('__init__.py','session.py','worker.py','ISOLATION_CANARY.py','ADMISSION_RECONCILIATION.json','GPU_AUTHORIZATION.json'):
        p=HERE/name;files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    complete=types.FunctionType(import_closure.complete.__code__,dict(import_closure.complete.__globals__,ENTRYPOINTS=(PACKAGE+'.session',PACKAGE+'.worker')))
    files,graph=complete(files)
    assert not any(n.endswith(('cpu_transport.py','cpu_probe.py','cpu_probe_v2.py','repair_probe.py')) for n in files)
    lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    for name,h in lock['source_pins'].items():assert sha(files[(PRIOR/name).relative_to(ROOT).as_posix()])==h
    for arm,path in [('A','u_re/v01/submission_noegv.zip'),('B','u_re/v01/experiments/action_priority_01/submission_action_v01.zip')]:
        assert sha(files[path])==lock['arms'][arm]['ZIP_sha256']
    registration=dict(execution_id=ID,production_entry=PACKAGE+'.session.run',worker_entry=PACKAGE+'.worker',files={n:sha(b) for n,b in files.items()},wheel_hashes=lock['official_wheels'])
    files['gpu_registration.json']=(json.dumps(registration,indent=2)+'\n').encode()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,10,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    payload=stream.getvalue();write(HERE/'payload.zip',payload)
    write(HERE/'GPU03_PAYLOAD_MANIFEST.json',dict(payload_sha256=sha(payload),bytes=len(payload),**registration,import_closure=graph,CPU_transport_in_payload=False,
        frozen_tasks=lock['tasks'],frozen_order=lock['order'],source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()))

def make_notebook(mode,directory,quota=None):
    from s1.prepare import INSTALL,IMAGE
    directory=Path(directory);assert mode in ('GPU','CPU_DRY_RUN')
    manifest=json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes());payload=(HERE/'payload.zip').read_bytes()
    assert sha(payload)==manifest['payload_sha256']
    gpu=mode=='GPU';run_name='u_re_actionfirst_abba03' if gpu else directory.name
    slug=SLUG if gpu else 'wudangdexiaodoashi/gemma4-u-re-abba03-'+directory.name
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
SESSION_STARTED=time.monotonic()
from pathlib import Path
RUN_DIR=Path('/kaggle/working/{run_name}')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(payload).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None and all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'gpu_registration.json').read_bytes())
for n,h in REG['files'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n
(RUN_DIR/'PAYLOAD_IDENTITY.json').write_text(json.dumps(dict(payload_sha256={sha(payload)!r},production_entry=REG['production_entry'],verified_files=len(REG['files']),mode={mode!r},source=str(SOURCE))))
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==REG['wheel_hashes']
'''
    execute=INSTALL+f'''from s1.task_identity import find_data
data=find_data()
lock=json.loads((SOURCE/'u_re/v01/experiments/action_priority_01/integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json').read_bytes())
assert {{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (data/'wheels').glob('*.whl')}}=={{n:v['sha256'] for n,v in lock['task_wheels'].items()}}
from {PACKAGE}.session import run
'''
    if gpu:
        assert quota is not None
        execute+=f"with (RUN_DIR/'execution.log').open('x') as log:\n    import contextlib\n    with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):await run(RUN_DIR/'results',SESSION_STARTED,mode='GPU',quota_at_dispatch={str(quota)!r})\n"
    else:
        aux=(HERE/'cpu_transport.py').read_bytes()
        execute+=f'''aux=__import__('base64').b64decode({base64.b64encode(aux).decode()!r})
assert hashlib.sha256(aux).hexdigest()=={sha(aux)!r}
auxfile=RUN_DIR/'cpu_transport.py';auxfile.write_bytes(aux)
import importlib.util,contextlib
module_spec=importlib.util.spec_from_file_location('cpu_only_transport',auxfile)
module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
with (RUN_DIR/'execution.log').open('x') as log:
    with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):await run(RUN_DIR/'results',SESSION_STARTED,mode='CPU_DRY_RUN',cpu_transport=module.CPUTransport())
'''
    code="from harness_v2.evidence import bundle\ntry:\n"+''.join('    '+line+'\n' for line in execute.splitlines())+"finally:print('GPU03_ENTRYPOINT_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for source in (setup,code):
        compile(source,'<GPU03-shared-payload>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',source=source,id=sha(source.encode())[:12],metadata={},outputs=[],execution_count=None))
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=cells)
    raw=(json.dumps(nb,indent=1)+'\n').encode()
    meta=dict(id=slug,title=slug.split('/')[1],code_file='study.ipynb',language='python',kernel_type='notebook',is_private=True,enable_gpu=gpu,enable_tpu=False,enable_internet=False,
        competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],model_sources=[MODEL_SOURCE] if gpu else [],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    if gpu:meta['machine_shape']='NvidiaL4'
    configuration=dict(GPU=True,TPU=False,internet=False,model_sources=[MODEL_SOURCE],Agent_runs=4,formal_submission=False,machine_shape='NvidiaL4',session_seconds=10000) if gpu else dict(GPU=False,TPU=False,internet=False,model_sources=[],Agent_runs=1,Gemma_calls=0,formal_submission=False)
    write(directory/'notebook/study.ipynb',raw);write(directory/'notebook/kernel-metadata.json',meta)
    write(directory/'BUILD.json',dict(execution_id=ID if gpu else ID+'-'+directory.name,slug=slug,max_dispatches=1,Notebook_sha256=sha(raw),wire_sha256=sha(json.dumps(nb).encode()),payload_sha256=sha(payload),
        selection_protocol_sha256=sha((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes()),configuration=configuration,expected_candidates_in_order=['A','B','B','A'] if gpu else [],
        sdk_versions={n:importlib.metadata.version(n) for n in ('kaggle','kagglesdk')},payload_members=manifest['files'],CPU_aux_sha256=None if gpu else sha(aux)))
