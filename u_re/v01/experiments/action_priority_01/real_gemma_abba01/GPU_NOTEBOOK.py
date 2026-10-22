"""Seal exactly one private GPU build, reusing accepted CPU payload bytes."""
import ast
import base64
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import subprocess
import types
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];PRIOR=HERE.parent/'integrated_cpu_01'
SLUG='wudangdexiaodoashi/gemma4-u-re-actionfirst-abba01'
ID='U-RE-V01-ACTION-FIRST-01-GPU01'
MODEL_SOURCE='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw=value if isinstance(value,bytes) else (json.dumps(value,indent=2)+'\n').encode()
    if path.exists():assert path.read_bytes()==raw,'Never overwrite a sealed build';return
    path.write_bytes(raw)

def controller_module():
    path=ROOT/'u_re/v01/experiments/fastapi_pilot_01/attempts/cpu02/dispatch.py'
    source=path.read_text(encoding='utf-8')
    old="assert body.get('slug')==SLUG and body.get('enableGpu') is False and body.get('enableTpu') is False"
    new="assert body.get('slug')==SLUG and body.get('enableGpu') is True and body.get('enableTpu') is False"
    assert source.count(old)==1;source=source.replace(old,new)
    old="assert body.get('enableInternet') is False and not body.get('modelDataSources') and not body.get('machineShape')"
    new="assert body.get('enableInternet') is False and body.get('modelDataSources')==[MODEL_SOURCE] and body.get('machineShape')=='NvidiaL4'\n            assert body.get('sessionTimeoutSeconds')==10000"
    assert source.count(old)==1;source=source.replace(old,new)
    module=types.ModuleType('authorized_gpu_once');exec(compile(source,str(path),'exec'),module.__dict__)
    module.EXECUTION_ID=ID;module.SLUG=SLUG;module.MODEL_SOURCE=MODEL_SOURCE
    def config(spec):
        assert spec['execution_id']==ID and spec['slug']==SLUG and spec['max_dispatches']==1
        assert spec['configuration']==dict(GPU=True,TPU=False,internet=False,model_sources=[MODEL_SOURCE],Agent_runs=4,formal_submission=False,machine_shape='NvidiaL4',session_seconds=10000)
    def grant(value,spec):
        assert value and value.get('human_message_reference') and value.get('GPU_authorized') is True
        assert value['execution_id']==ID and value['slug']==SLUG and value['max_SaveKernel_dispatches']==1
        assert value['max_Agent_runs']==4 and value['Agent_seconds']==300 and value['platform_window_seconds']==10000
        assert value['model_source']==MODEL_SOURCE and value['GPU_type']=='NVIDIA L4' and value['GPU_count']==4 and value['TP']==4
        for k in ('Notebook_sha256','wire_sha256','payload_sha256'):assert value[k]==spec[k]
    module.checked_config=config;module.checked_authorization=grant
    return module

def build():
    assert not (HERE/'execution/dispatch.claim').exists()
    old=json.loads((PRIOR/'taskruntime01/notebook/study.ipynb').read_bytes())
    line=next(l for l in old['cells'][0]['source'].splitlines() if l.startswith("payload=__import__('base64').b64decode("))
    raw=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
    assert sha(raw)==json.loads((PRIOR/'taskruntime01/BUILD.json').read_bytes())['payload_sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:files={n:z.read(n) for n in z.namelist()}
    # Preserve accepted shared code;remove CPU scripted response/test entrypoints.
    for name in list(files):
        if name.endswith(('taskruntime_probe.py','acceptance.py','runner_cases.py','cpu_interfaces.py')) or name=='cpu_registration.json':del files[name]
    prefix='u_re/v01/experiments/action_priority_01/real_gemma_abba01/'
    for name in ('__init__.py','worker.py','session.py','ISOLATION_CANARY.py','ADMISSION_RECONCILIATION.json','GPU_AUTHORIZATION.json'):
        files[prefix+name]=(HERE/name).read_bytes()
    previous='u_re/v01/experiments/action_priority_01/integrated_cpu_01/'
    for name in ('ABBA_EXPERIMENT_LOCK.json','SELECTED_TASKS.json','APPROVED_RUNTIME_FINGERPRINT.json'):
        files[previous+name]=(PRIOR/name).read_bytes()
    for name in ('s1/experiments/__init__.py','s1/experiments/e3_localize_smoke_03/__init__.py'):files[name]=b''
    name='s1/experiments/e3_localize_smoke_03/idle.py';files[name]=(ROOT/name).read_bytes()
    for name in ('MODEL_RUNTIME_CONFIG.json',):files['u_re/v01/experiments/gemma_smoke_01/'+name]=(ROOT/'u_re/v01/experiments/gemma_smoke_01'/name).read_bytes()
    action=ROOT/'u_re/v01/experiments/action_priority_01/candidate_action_v01'
    for p in action.rglob('*'):
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    files['u_re/v01/experiments/action_priority_01/submission_action_v01.zip']=(action.parent/'submission_action_v01.zip').read_bytes()
    lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    for arm,name in (('A','u_re/v01/submission_noegv.zip'),('B','u_re/v01/experiments/action_priority_01/submission_action_v01.zip')):
        assert sha(files[name])==lock['arms'][arm]['ZIP_sha256']
    reg=dict(execution_id=ID,files={n:sha(b) for n,b in files.items()},wheel_hashes=lock['official_wheels'])
    files['gpu_registration.json']=(json.dumps(reg,indent=2)+'\n').encode()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,10,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    payload=stream.getvalue()
    from s1.prepare import INSTALL,IMAGE
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
SESSION_STARTED=time.monotonic()
from pathlib import Path
RUN_DIR=Path('/kaggle/working/u_re_actionfirst_abba01')
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
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==REG['wheel_hashes']
(RUN_DIR/'official_wheel_hashes.json').write_text(json.dumps(actual,indent=2))
'''
    check='''from s1.task_identity import find_data
data=find_data()
lock=json.loads((SOURCE/'u_re/v01/experiments/action_priority_01/integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json').read_bytes())
actual={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (data/'wheels').glob('*.whl')}
assert actual=={n:v['sha256'] for n,v in lock['task_wheels'].items()},'Task wheels drift'
(RUN_DIR/'task_wheel_hashes.json').write_text(json.dumps(actual,indent=2))
'''
    execute=INSTALL+check+'''
from u_re.v01.experiments.action_priority_01.real_gemma_abba01.session import run
with (RUN_DIR/'execution.log').open('x') as log:
    import contextlib
    with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        await run(RUN_DIR/'results',SESSION_STARTED)
'''
    code="from harness_v2.evidence import bundle\ntry:\n"+''.join('    '+l+'\n' for l in execute.splitlines())+"finally:print('ACTION_FIRST_GPU_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for codecell in (setup,code):
        compile(codecell,'<authorized-gpu-abba>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',source=codecell,id=sha(codecell.encode())[:12],metadata={},outputs=[],execution_count=None))
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=cells)
    raw=(json.dumps(nb,indent=1)+'\n').encode()
    meta=dict(id=SLUG,title=SLUG.split('/')[1],code_file='study.ipynb',language='python',kernel_type='notebook',is_private=True,
        enable_gpu=True,enable_tpu=False,enable_internet=False,machine_shape='NvidiaL4',competition_sources=['gemma-4-developer-agent'],
        dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],model_sources=[MODEL_SOURCE],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    write(HERE/'notebook/study.ipynb',raw);write(HERE/'notebook/kernel-metadata.json',meta)
    write(HERE/'BUILD.json',dict(execution_id=ID,slug=SLUG,max_dispatches=1,Notebook_sha256=sha(raw),wire_sha256=sha(json.dumps(nb).encode()),payload_sha256=sha(payload),
        selection_protocol_sha256=sha((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes()),
        configuration=dict(GPU=True,TPU=False,internet=False,model_sources=[MODEL_SOURCE],Agent_runs=4,formal_submission=False,machine_shape='NvidiaL4',session_seconds=10000),
        expected_candidates_in_order=['A','B','B','A'],sdk_versions={n:importlib.metadata.version(n) for n in ('kaggle','kagglesdk')},payload_members=reg['files']))
    print('SEALED_GPU_BUILD',sha(raw),sha(payload))

if __name__=='__main__':build()
