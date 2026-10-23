"""Reuse durable CPU dispatch and version-bound read-only collector."""
import ast,base64,io,json,types,zipfile,importlib.metadata
from pathlib import Path
from .selection import HERE,ROOT,ID,sha,write
from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import notebook as proven

def inherited_files():
    old=json.loads((proven.HERE/'notebook/study.ipynb').read_bytes())
    line=next(x for x in old['cells'][0]['source'].splitlines() if x.startswith("payload=__import__('base64').b64decode("))
    raw=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if n!='gpu_registration.json'}
    return files

def build_screen(attempt='screen01'):
    files=inherited_files()
    for parent in ('u_re/v02','u_re/v02/experiments'):files[parent+'/__init__.py']=b''
    for name in ('__init__.py','selection.py','screen.py','REPLICATION_PROTOCOL.json','TASK_POOL_FREEZE.json'):
        p=HERE/name;files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    lock=json.loads((proven.PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    reg=dict(files={n:sha(b) for n,b in files.items()},wheel_hashes=lock['official_wheels'])
    files['gpu_registration.json']=(json.dumps(reg,indent=2)+'\n').encode()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):z.writestr(n,b)
    payload=stream.getvalue();write_bytes(HERE/attempt/'screen_payload.zip',payload)
    from s1.prepare import INSTALL,IMAGE
    run_name='v02-'+attempt;slug='wudangdexiaodoashi/gemma4-u-re-v02-'+attempt
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
RUN_DIR=Path('/kaggle/working/{run_name}');RUN_DIR.mkdir(parents=True,exist_ok=False)
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
assert {{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}==REG['wheel_hashes']
'''
    execute=INSTALL+f'''from s1.task_identity import find_data
data=find_data()
LOCK=json.loads((SOURCE/'u_re/v01/experiments/action_priority_01/integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json').read_bytes())
assert {{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (data/'wheels').glob('*.whl')}}=={{n:v['sha256'] for n,v in LOCK['task_wheels'].items()}}
with (RUN_DIR/'cpu.log').open('x') as log:
    r=subprocess.run([sys.executable,'-m','u_re.v02.experiments.action_first_replication_01.screen',str(RUN_DIR/'validation')],cwd=SOURCE,stdout=log,stderr=subprocess.STDOUT,timeout=6500)
assert r.returncode==0,'Screening execution failed; preserve raw output'
'''
    code="from harness_v2.evidence import bundle\ntry:\n"+''.join('    '+s+'\n' for s in execute.splitlines())+"finally:print('V02_SCREEN_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for source in (setup,code):
        compile(source,'<V02-screen>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',source=source,id=sha(source.encode())[:12],metadata={},outputs=[],execution_count=None))
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=cells)
    raw=(json.dumps(nb,indent=1)+'\n').encode();cpu=HERE/attempt
    meta=dict(id=slug,title=slug.split('/')[1],code_file='study.ipynb',language='python',kernel_type='notebook',is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],model_sources=[],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    write_bytes(cpu/'notebook/study.ipynb',raw);write(cpu/'notebook/kernel-metadata.json',meta)
    write(cpu/'BUILD.json',dict(execution_id=ID+'-'+attempt,slug=slug,max_dispatches=1,Notebook_sha256=sha(raw),wire_sha256=sha(json.dumps(nb).encode()),payload_sha256=sha(payload),selection_protocol_sha256=sha((HERE/'REPLICATION_PROTOCOL.json').read_bytes()),configuration=dict(GPU=False,TPU=False,internet=False,model_sources=[],Agent_runs=0,Gemma_calls=0,formal_submission=False),expected_candidates_in_order=[],sdk_versions={n:importlib.metadata.version(n) for n in ('kaggle','kagglesdk')},payload_members=reg['files']))

def write_bytes(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)

def factory(attempt='screen01',agent_runs=0):
    cpu=HERE/attempt;slug='wudangdexiaodoashi/gemma4-u-re-v02-'+attempt;execution_id=ID+'-'+attempt
    from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import repair
    # Accepted CPU controller already checks GPU/TPU/Internet, exact payload,
    # identity, authorization, SDK retries=0 and exclusive durable dispatch.
    source=Path(repair.__file__).read_text(encoding='utf-8')
    source=source.replace('from .GPU_NOTEBOOK import HERE,ROOT,PRIOR,sha,write','')
    m=types.ModuleType('v02_cpu_controller');m.__file__=repair.__file__;m.HERE=HERE
    exec(compile(source,m.__file__,'exec'),m.__dict__)
    m.HERE=HERE;m.ROOT=ROOT;m.PRIOR=proven.PRIOR;m.CPU=cpu;m.ID=execution_id;m.SLUG=slug;m.sha=sha;m.write=proven.write
    if agent_runs:
        original=m.controller_module
        def controller_module():
            c=original();check=c.checked_config
            def checked(spec):
                assert spec['configuration']['Agent_runs']==agent_runs==1
                check(dict(spec,configuration=dict(spec['configuration'],Agent_runs=0)))
            c.checked_config=checked;return c
        m.controller_module=controller_module
    def launch():
        from u_re.v01.experiments.fastapi_pilot_01 import auth_diagnose
        (cpu/'preflight').mkdir(parents=True,exist_ok=True);auth_diagnose.HERE=cpu/'preflight';auth_diagnose.diagnose()
        p=ROOT/'u_re/v01/experiments/gemma_smoke_01/cpu_launch_once.py'
        text=p.read_text(encoding='utf-8').replace('from .cpu_notebook import CPU,HERE,ROOT,SLUG,EXECUTION_ID,controller_module,sha,write','')
        text=text.replace("timeout='3600'","timeout='7200'")
        text=text.replace('Current human instruction: 你可以使用kaggle的notebook来完成这个任务; interpreted CPU-only official interface validation, no GPU/Gemma authorization.','Current V02 replication human task explicitly authorizes CPU native screening max16 first4 and final production-payload CPU acceptance. No Gemma/GPU/formal Submission in this CPU dispatch.')
        t=types.ModuleType('v02_cpu_launch');t.__file__=str(p)
        exec(compile(text,str(p),'exec'),t.__dict__)
        for k,v in dict(CPU=cpu,HERE=HERE,ROOT=ROOT,SLUG=slug,EXECUTION_ID=execution_id,controller_module=m.controller_module,sha=sha,write=proven.write).items():setattr(t,k,v)
        t.launch()
    def collect(private_root):
        p=ROOT/'u_re/v01/experiments/action_priority_01/gpu_readiness_01/collect_capabilities.py'
        text=p.read_text(encoding='utf-8').replace('from .cpu_probe_notebook import CPU,ROOT,SLUG','CPU=None;ROOT=None;SLUG=None').replace("('u_re_isolation_cap01.zip','u_re_isolation_canary01.zip')",repr(('v02-'+attempt+'.zip',)))
        t=types.ModuleType('v02_cpu_read');t.__file__=str(p);exec(compile(text,str(p),'exec'),t.__dict__);t.ROOT=ROOT
        t.collect(private_root,cpu=cpu,slug=slug,archive='v02-'+attempt+'.zip')
    m.launch=launch;m.collect=collect;return m

if __name__=='__main__':
    import sys
    command=sys.argv[1];attempt=sys.argv[2] if len(sys.argv)>2 else 'screen01'
    if command=='build':build_screen(attempt)
    elif command=='launch':factory(attempt).launch()
    elif command=='collect':factory(attempt).collect(sys.argv[3])
