"""Build from accepted packaged code; durable validation inside every Save path."""
import ast,base64,inspect,io,json,types,zipfile,subprocess,importlib.metadata
from pathlib import Path
from .dependencies import HERE,ROOT,ID,ARTIFACTS,sha,write
from u_re.v02.experiments.action_first_replication_01 import cpu_control as prior
from u_re.v01.experiments.action_priority_01.real_gemma_abba02 import import_closure

PACKAGE='u_re.v02.experiments.env_recovery_admission_01'

def build(attempt,entry='recovery'):
    assert not (HERE/attempt/'execution/dispatch.claim').exists()
    with zipfile.ZipFile(prior.HERE/'screen04/screen_payload.zip') as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if n!='gpu_registration.json'}
    for p in HERE.glob('*.py'):
        if p.name not in ('notebook.py','release.py','test_local.py','audit.py'):files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for name in ('NEW_DEPENDENCIES.json','TASK_POOL_FREEZE.json','RECOVERY_PROTOCOL.json','APPROVED_INPUT_IDENTITIES.json','ORIGINAL_DIAGNOSTIC_REFERENCE.json','V02B_PROTOCOL_LOCK.json','V02B_ENVIRONMENT_LOCK.json'):
        p=HERE/name
        if p.exists():files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    extra=json.loads((HERE/'NEW_DEPENDENCIES.json').read_bytes())
    for r in extra['packages']:
        raw=(ARTIFACTS/r['filename']).read_bytes();assert sha(raw)==r['sha256']
        files[(HERE/'wheels'/r['filename']).relative_to(ROOT).as_posix()]=raw
    complete=types.FunctionType(import_closure.complete.__code__,dict(import_closure.complete.__globals__,ENTRYPOINTS=(PACKAGE+'.'+entry,)))
    files,graph=complete(files)
    old=json.loads((ROOT/'u_re/v01/experiments/action_priority_01/integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json').read_bytes())
    reg=dict(files={n:sha(raw) for n,raw in files.items()},wheel_hashes=old['official_wheels'],entry=PACKAGE+'.'+entry)
    files['gpu_registration.json']=(json.dumps(reg,indent=2)+'\n').encode()
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
        for n,raw in sorted(files.items()):z.writestr(n,raw)
    payload=buffer.getvalue();cpu=HERE/attempt;cpu.mkdir(parents=True,exist_ok=True);(cpu/'payload.zip').write_bytes(payload)
    from s1.prepare import INSTALL,IMAGE
    slug='wudangdexiaodoashi/gemma4-u-re-v02b-'+attempt;run_name='v02b-'+attempt
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
SESSION_STARTED=time.monotonic()
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
    result=subprocess.run([sys.executable,'-m',REG['entry'],str(RUN_DIR/'validation')],cwd=SOURCE,stdout=log,stderr=subprocess.STDOUT,timeout=6500)
assert result.returncode==0,'CPU execution failed; preserve immutable raw evidence'
'''
    code="from harness_v2.evidence import bundle\ntry:\n"+''.join('    '+line+'\n' for line in execute.splitlines())+"finally:print('V02B_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for source in (setup,code):
        compile(source,'<V02b-final-packaged-CPU>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',source=source,id=sha(source.encode())[:12],metadata={},outputs=[],execution_count=None))
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=cells)
    raw=(json.dumps(nb,indent=1)+'\n').encode();(cpu/'notebook').mkdir(exist_ok=True);(cpu/'notebook/study.ipynb').write_bytes(raw)
    meta=dict(id=slug,title=slug.split('/')[1],code_file='study.ipynb',language='python',kernel_type='notebook',is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],model_sources=[],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    write(cpu/'notebook/kernel-metadata.json',meta)
    write(cpu/'BUILD.json',dict(execution_id=ID+'-'+attempt,slug=slug,max_dispatches=1,Notebook_sha256=sha(raw),wire_sha256=sha(json.dumps(nb).encode()),payload_sha256=sha(payload),selection_protocol_sha256=sha((HERE/('V02B_PROTOCOL_LOCK.json' if entry=='screen' else 'RECOVERY_PROTOCOL.json')).read_bytes()),configuration=dict(GPU=False,TPU=False,internet=False,model_sources=[],Agent_runs=0,Gemma_calls=0,formal_submission=False),expected_candidates_in_order=[],sdk_versions={n:importlib.metadata.version(n) for n in ('kaggle','kagglesdk')},payload_members=reg['files'],entry=reg['entry'],source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),import_closure=graph))
    validate_attempt(attempt)

def validate_attempt(attempt):
    cpu=HERE/attempt;b=json.loads((cpu/'BUILD.json').read_bytes());raw=(cpu/'payload.zip').read_bytes();assert sha(raw)==b['payload_sha256']
    nb=json.loads((cpu/'notebook/study.ipynb').read_bytes());assert sha((cpu/'notebook/study.ipynb').read_bytes())==b['Notebook_sha256']
    line=next(s for s in nb['cells'][0]['source'].splitlines() if s.startswith("payload=__import__('base64').b64decode("))
    assert base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))==raw
    assert 'shutil' in nb['cells'][0]['source'].splitlines()[0]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        for n,h in b['payload_members'].items():assert sha(z.read(n))==h,n
        prefix=HERE.relative_to(ROOT).as_posix()+'/'
        required=['NEW_DEPENDENCIES.json','RECOVERY_PROTOCOL.json','APPROVED_INPUT_IDENTITIES.json','TASK_POOL_FREEZE.json','runtime.py',b['entry'].rsplit('.',1)[-1]+'.py']
        if b['entry'].endswith('.screen'):required+=['V02B_PROTOCOL_LOCK.json','V02B_ENVIRONMENT_LOCK.json']
        for n in required:assert prefix+n in z.namelist(),n
        for r in json.loads(z.read(prefix+'NEW_DEPENDENCIES.json'))['packages']:assert sha(z.read(prefix+'wheels/'+r['filename']))==r['sha256']
        name='V02B_PROTOCOL_LOCK.json' if b['entry'].endswith('.screen') else 'RECOVERY_PROTOCOL.json'
        assert sha(z.read(prefix+name))==b['selection_protocol_sha256']
        if name=='V02B_PROTOCOL_LOCK.json':
            protocol=json.loads(z.read(prefix+name))
            assert sha(z.read(prefix+'V02B_ENVIRONMENT_LOCK.json'))==protocol['environment_lock_sha256']
            assert sha(z.read(prefix+'TASK_POOL_FREEZE.json'))==protocol['pool_sha256']
            for n,h in protocol['execution_sources'].items():assert sha(z.read(prefix+n))==h,n
    return True

def factory(attempt):
    source=inspect.getsource(prior.factory).replace("'gemma4-u-re-v02-'","'gemma4-u-re-v02b-'").replace("'wudangdexiaodoashi/gemma4-u-re-v02-'","'wudangdexiaodoashi/gemma4-u-re-v02b-'").replace("'v02-'+attempt", "'v02b-'+attempt")
    source=source.replace("if attempt.startswith('screen'):validate_screen(attempt)","validate_attempt(attempt)")
    source=source.replace('Current V02 replication human task explicitly authorizes CPU native screening max16 first4 and final production-payload CPU acceptance. No Gemma/GPU/formal Submission in this CPU dispatch.','Current attached V02b task explicitly authorizes CPU verified dependency recovery,diagnostic reevaluation,max24 new native screens and final CPU acceptance. No GPU,Gemma or formal Submission authorized by this CPU dispatch.')
    module=types.ModuleType('v02b_proven_CPU_control');module.__dict__.update(prior.__dict__);module.HERE=HERE;module.ID=ID;module.ROOT=ROOT;module.validate_attempt=validate_attempt
    exec(compile(source,'<V02b-durable-controller>','exec'),module.__dict__)
    return module.factory(attempt)

if __name__=='__main__':
    import sys
    command,attempt=sys.argv[1:3]
    if command=='build':build(attempt,sys.argv[3] if len(sys.argv)>3 else 'recovery')
    elif command=='launch':factory(attempt).launch()
    elif command=='collect':factory(attempt).collect(sys.argv[3])
