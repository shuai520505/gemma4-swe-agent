"""One CPU-only interface check. Reuses CPU02 controller; never authorizes GPU."""
import ast
import base64
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import types
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
CPU=HERE/'cpu01'
EXECUTION_ID='U-RE-GEMMA-SMOKE-CPU01'
SLUG='wudangdexiaodoashi/gemma4-u-re-smoke01-cpu01'
ORIGINAL=ROOT/'u_re/v01/experiments/fastapi_pilot_01/attempts/cpu02/dispatch.py'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=obj if isinstance(obj,bytes) else (json.dumps(obj,indent=2)+'\n').encode()
    if path.exists():
        assert path.read_bytes()==raw,'Never overwrite a frozen CPU build';return
    path.write_bytes(raw)

def controller_module():
    # The tested HTTP/journal/no-retry implementation remains byte-for-byte unchanged.
    m=types.ModuleType('smoke_cpu_dispatch');exec(compile(ORIGINAL.read_bytes(),str(ORIGINAL),'exec'),m.__dict__)
    m.EXECUTION_ID=EXECUTION_ID;m.SLUG=SLUG
    def config(spec):
        assert spec['execution_id']==EXECUTION_ID and spec['slug']==SLUG and spec['max_dispatches']==1
        assert spec['configuration']==dict(GPU=False,TPU=False,internet=False,model_sources=[],
            Agent_runs=6,Gemma_calls=0,formal_submission=False)
    def auth(grant,spec):
        if not grant or grant.get('execution_id')!=EXECUTION_ID or grant.get('slug')!=SLUG:
            raise PermissionError('Independent CPU interface authorization required')
        if grant.get('max_SaveKernel_dispatches')!=1 or not grant.get('human_message_reference'):
            raise PermissionError('CPU scope missing')
        for k in ('Notebook_sha256','wire_sha256','payload_sha256'):
            if grant.get(k)!=spec[k]:raise PermissionError('CPU build identity mismatch')
    m.checked_config=config;m.checked_authorization=auth
    return m

def build():
    files={}
    # Code only: no snapshots, old results, evaluator overlays, reports, Issue/repair text or credentials.
    for parent in ('harness_v2','s1'):
        for p in (ROOT/parent).rglob('*.py'):
            rel=p.relative_to(ROOT)
            if {'tests','results','notebooks','__pycache__','experiments','_local'}.intersection(rel.parts):continue
            if p.name.startswith('test_'):continue
            files[rel.as_posix()]=p.read_bytes()
    for n in ('u_re/__init__.py','u_re/v01/__init__.py','u_re/v01/runner_cases.py',
              'u_re/v01/experiments/gemma_smoke_01/cpu_interfaces.py','u_re/v01/experiments/gemma_smoke_01/inputs.py'):
        files[n]=(ROOT/n).read_bytes()
    for p in (ROOT/'u_re/v01/candidate_noegv').rglob('*'):
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    files['u_re/v01/submission_noegv.zip']=(ROOT/'u_re/v01/submission_noegv.zip').read_bytes()
    # Avoid namespace-package ambiguity in frozen host Python.
    files['u_re/v01/experiments/__init__.py']=b''
    files['u_re/v01/experiments/gemma_smoke_01/__init__.py']=b''
    plan=json.loads((HERE/'SMOKE_PLAN.json').read_text(encoding='utf-8'))
    reg=dict(execution_id=EXECUTION_ID,GPU=False,Gemma_inference=False,
        files={n:sha(b) for n,b in files.items()},wheel_hashes=plan['official_wheels'])
    files['cpu_registration.json']=(json.dumps(reg,indent=2)+'\n').encode()
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,10,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    payload=out.getvalue()
    from s1.prepare import INSTALL,IMAGE
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
RUN_DIR=Path('/kaggle/working/u_re_smoke_cpu01')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(payload).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'cpu_registration.json').read_text(encoding='utf-8'))
for n,h in REG['files'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==REG['wheel_hashes'],'Approved wheel drift'
(RUN_DIR/'wheel_hashes.json').write_text(json.dumps(actual,indent=2))
'''
    execute=INSTALL+'''\nimport torch
assert torch.cuda.device_count()==0,'CPU-only: refuse unexpected GPU'
with (RUN_DIR/'cpu.log').open('x') as log:
    result=subprocess.run([sys.executable,'-m','u_re.v01.experiments.gemma_smoke_01.cpu_interfaces',str(RUN_DIR/'validation')],cwd=SOURCE,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
print('SMOKE_INTERFACE_CPU_EXIT',result.returncode,flush=True)
assert result.returncode==0,'CPU interfaces failed; preserve failure, never auto rerun'
'''
    code="from harness_v2.evidence import bundle\ntry:\n"+''.join('    '+l+'\n' for l in execute.splitlines())+"finally:print('SMOKE_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for source in (setup,code):
        compile(source,'<cpu-interface-notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',source=source,id=sha(source.encode())[:12],metadata={},outputs=[],execution_count=None))
    nb=dict(nbformat=4,nbformat_minor=5,metadata={'kernelspec':{'name':'python3','language':'python','display_name':'Python 3'}},cells=cells)
    raw=(json.dumps(nb,indent=1)+'\n').encode()
    meta=dict(id=SLUG,title=SLUG.split('/')[1],code_file='study.ipynb',language='python',kernel_type='notebook',
        is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,
        competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],
        model_sources=[],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    write(CPU/'notebook/study.ipynb',raw);write(CPU/'notebook/kernel-metadata.json',meta)
    write(CPU/'BUILD.json',dict(execution_id=EXECUTION_ID,slug=SLUG,max_dispatches=1,
        Notebook_sha256=sha(raw),wire_sha256=sha(json.dumps(nb).encode()),payload_sha256=sha(payload),
        selection_protocol_sha256=sha((HERE/'SMOKE_PLAN.json').read_bytes()),
        configuration=dict(GPU=False,TPU=False,internet=False,model_sources=[],Agent_runs=6,Gemma_calls=0,formal_submission=False),
        expected_candidates_in_order=['noegv_synthetic_interfaces_only'],sdk_versions={n:importlib.metadata.version(n) for n in ('kaggle','kagglesdk')},
        payload_members=reg['files'],dispatch_controller_sha256=sha(ORIGINAL.read_bytes())))
    print(json.dumps(dict(slug=SLUG,payload_members=len(files),Notebook_sha256=sha(raw),GPU=False)))

if __name__=='__main__':build()
