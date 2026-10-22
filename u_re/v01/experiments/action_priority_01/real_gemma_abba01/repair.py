"""Versioned CPU-only repair;original failed GPU build/dispatch stay immutable."""
import ast
import base64
import io
import importlib.metadata
import json
from pathlib import Path
import types
import zipfile
from .GPU_NOTEBOOK import HERE,ROOT,PRIOR,sha,write

CPU=HERE/'repair_cpu01';ID='U-RE-ACTION-FIRST-ABBA-PREFLIGHT-REPAIR01'
SLUG='wudangdexiaodoashi/gemma4-u-re-abba-preflight-repair01'

def corrected_files():
    nb=json.loads((HERE/'notebook/study.ipynb').read_bytes())
    line=next(l for l in nb['cells'][0]['source'].splitlines() if l.startswith("payload=__import__('base64').b64decode("))
    payload=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
    with zipfile.ZipFile(io.BytesIO(payload)) as z:files={n:z.read(n) for n in z.namelist() if n!='gpu_registration.json'}
    lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    # Complete the declared closure algorithmically,not another manual file list.
    for name,h in lock['source_pins'].items():
        p=PRIOR/name;raw=p.read_bytes();assert sha(raw)==h;files[p.relative_to(ROOT).as_posix()]=raw
    for name,h in lock['source_pins'].items():assert sha(files[(PRIOR/name).relative_to(ROOT).as_posix()])==h
    return files

def build():
    assert not (CPU/'execution/dispatch.claim').exists()
    files=corrected_files()
    prefix='u_re/v01/experiments/action_priority_01/real_gemma_abba01/'
    for name in ('repair_probe.py','GPU_NOTEBOOK.py'):files[prefix+name]=(HERE/name).read_bytes()
    files[prefix+'GPU_AUTHORIZATION.json']=b'{"GPU_authorized":false,"scope":"CPU_REPAIR_ONLY"}\n'
    reg=dict(files={n:sha(b) for n,b in files.items()});files['repair_registration.json']=(json.dumps(reg,indent=2)+'\n').encode()
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,10,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    payload=buf.getvalue();from s1.prepare import INSTALL,IMAGE
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
RUN_DIR=Path('/kaggle/working/u_re_abba_repair_cpu01')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(payload).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None and all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'repair_registration.json').read_bytes())
for n,h in REG['files'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
LOCK=json.loads((SOURCE/'u_re/v01/experiments/action_priority_01/integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json').read_bytes())
assert {{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}==LOCK['official_wheels']
'''
    execute=INSTALL+'''from s1.task_identity import find_data
data=find_data()
assert {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (data/'wheels').glob('*.whl')}=={n:v['sha256'] for n,v in LOCK['task_wheels'].items()}
with (RUN_DIR/'cpu.log').open('x') as log:
    r=subprocess.run([sys.executable,'-m','u_re.v01.experiments.action_priority_01.real_gemma_abba01.repair_probe',str(RUN_DIR/'validation')],cwd=SOURCE,stdout=log,stderr=subprocess.STDOUT,timeout=900)
assert r.returncode==0,'CPU repair failed;preserve original output'
'''
    code="from harness_v2.evidence import bundle\ntry:\n"+''.join('    '+l+'\n' for l in execute.splitlines())+"finally:print('CPU_REPAIR_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for source in (setup,code):
        compile(source,'<CPU-repair>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',source=source,id=sha(source.encode())[:12],metadata={},outputs=[],execution_count=None))
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=cells)
    raw=(json.dumps(nb,indent=1)+'\n').encode()
    meta=dict(id=SLUG,title=SLUG.split('/')[1],code_file='study.ipynb',language='python',kernel_type='notebook',is_private=True,
        enable_gpu=False,enable_tpu=False,enable_internet=False,competition_sources=['gemma-4-developer-agent'],
        dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],model_sources=[],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    write(CPU/'notebook/study.ipynb',raw);write(CPU/'notebook/kernel-metadata.json',meta)
    write(CPU/'BUILD.json',dict(execution_id=ID,slug=SLUG,max_dispatches=1,Notebook_sha256=sha(raw),wire_sha256=sha(json.dumps(nb).encode()),payload_sha256=sha(payload),
        selection_protocol_sha256=sha((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes()),configuration=dict(GPU=False,TPU=False,internet=False,model_sources=[],Agent_runs=0,Gemma_calls=0,formal_submission=False),
        expected_candidates_in_order=[],sdk_versions={n:importlib.metadata.version(n) for n in ('kaggle','kagglesdk')},payload_members=reg['files']))

def controller_module():
    path=ROOT/'u_re/v01/experiments/fastapi_pilot_01/attempts/cpu02/dispatch.py'
    m=types.ModuleType('cpu_repair_once');exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__)
    m.EXECUTION_ID=ID;m.SLUG=SLUG
    def grant(value,spec):
        assert value and value['execution_id']==ID and value['slug']==SLUG and value['max_SaveKernel_dispatches']==1 and value.get('human_message_reference')
        for k in ('Notebook_sha256','wire_sha256','payload_sha256'):assert value[k]==spec[k]
    m.checked_authorization=grant
    return m

def launch():
    from u_re.v01.experiments.fastapi_pilot_01 import auth_diagnose
    (CPU/'preflight').mkdir(parents=True,exist_ok=True);auth_diagnose.HERE=CPU/'preflight';auth_diagnose.diagnose()
    path=ROOT/'u_re/v01/experiments/gemma_smoke_01/cpu_launch_once.py';source=path.read_text(encoding='utf-8')
    source=source.replace('Current human instruction: 你可以使用kaggle的notebook来完成这个任务; interpreted CPU-only official interface validation, no GPU/Gemma authorization.',
        'Current human ABBA task Section8 explicitly permits CPU-only engineering repair after GPU startup failure. One targeted package/Compiler/boundary CPU probe;zero Agent,Gemma,GPU or task baseline. Original failed GPU preserved;no GPU retry authorized.')
    m=types.ModuleType('cpu_repair_launch');m.__file__=str(path);m.__package__='u_re.v01.experiments.gemma_smoke_01';exec(compile(source,str(path),'exec'),m.__dict__)
    for k,v in dict(CPU=CPU,EXECUTION_ID=ID,SLUG=SLUG,controller_module=controller_module).items():setattr(m,k,v)
    m.launch()

def collect(private_root):
    source=(ROOT/'u_re/v01/experiments/action_priority_01/gpu_readiness_01/collect_capabilities.py').read_text(encoding='utf-8')
    source=source.replace('from .cpu_probe_notebook import CPU,ROOT,SLUG','CPU=None;ROOT=None;SLUG=None')
    source=source.replace("('u_re_isolation_cap01.zip','u_re_isolation_canary01.zip')","('u_re_abba_repair_cpu01.zip',)")
    m=types.ModuleType('cpu_repair_read');m.__file__=__file__;exec(compile(source,__file__,'exec'),m.__dict__);m.ROOT=ROOT
    m.collect(private_root,cpu=CPU,slug=SLUG,archive='u_re_abba_repair_cpu01.zip')

if __name__=='__main__':
    import sys
    if sys.argv[1]=='build':build()
    elif sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='collect':collect(sys.argv[2])
