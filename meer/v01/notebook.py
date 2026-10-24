"""CPU-only sealed payload; reuse durable once-only SaveKernel/readonly recovery."""
import base64
import importlib.metadata
import io
import inspect
import json
from pathlib import Path
import types
import zipfile
from .build import HERE,ROOT,sha,archive

ID='MEER-V01-CPU'


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw=value if isinstance(value,bytes) else (json.dumps(value,indent=2)+'\n').encode()
    with path.open('xb') as f:f.write(raw)


def build(attempt):
    from s1.prepare import INSTALL,IMAGE
    source=ROOT/'u_re/v04/experiments/evidence_guided_repair_01'
    acceptance=json.loads((source/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
    inherited=(source/'payload.zip').read_bytes()
    assert sha(inherited)==acceptance['payload_sha256']
    raw=Path(acceptance['raw_archive_path']).read_bytes()
    assert sha(raw)==acceptance['raw_archive_sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:assert z.testzip() is None
    with zipfile.ZipFile(io.BytesIO(inherited)) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if n!='gpu_registration.json'}
    # No new task data, no historical trajectory, no evaluator overlay added.
    for name in ('__init__.py','verify.py','test_mechanism.py','cpu_acceptance.py','owned_transport.py','CANDIDATE_MANIFEST.json'):
        files['meer/v01/'+name]=(HERE/name).read_bytes()
    files['meer/__init__.py']=b''  # Namespace marker only inside CPU payload.
    for p in (HERE/'candidates').rglob('*'):
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for arm in ('A','B','C'):
        files['meer/v01/submission_'+arm+'.zip']=(HERE/f'submission_{arm}.zip').read_bytes()
    old=json.loads((source/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())
    reg=dict(files={n:sha(b) for n,b in files.items()},wheel_hashes=old['wheel_hashes'],
             production_entry='meer.v01.cpu_acceptance.run',CPU_MODEL='SCRIPTED_ONLY',GPU_authorized=False)
    files['gpu_registration.json']=(json.dumps(reg,indent=2)+'\n').encode()
    payload=archive(files);directory=HERE/attempt
    write(directory/'payload.zip',payload)
    slug='wudangdexiaodoashi/meer-v01-'+attempt
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
RUN_DIR=Path('/kaggle/working/meer-v01-{attempt}');RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(payload).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None and all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'gpu_registration.json').read_bytes())
for n,h in REG['files'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n
(RUN_DIR/'PAYLOAD_IDENTITY.json').write_text(json.dumps(dict(payload_sha256={sha(payload)!r},files=REG['files'],mode='SCRIPTED_ONLY_CPU')))
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
assert {{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}==REG['wheel_hashes']
'''
    run=INSTALL+'''with (RUN_DIR/'cpu.log').open('x') as log:
    r=subprocess.run([sys.executable,'-m','meer.v01.cpu_acceptance',str(RUN_DIR/'validation')],cwd=SOURCE,stdout=log,stderr=subprocess.STDOUT,timeout=2400)
assert r.returncode==0,'CPU acceptance failed; original output preserved'
'''
    code="from harness_v2.evidence import bundle\ntry:\n"+''.join('    '+x+'\n' for x in run.splitlines())+"finally: print('MEER_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    for s in (setup,code):compile(s,'<meer-cpu>','exec')
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),
        cells=[dict(cell_type='code',source=s,id=sha(s.encode())[:12],metadata={},outputs=[],execution_count=None) for s in (setup,code)])
    notebook=(json.dumps(nb,indent=1)+'\n').encode()
    meta=dict(id=slug,title=slug.split('/')[1],code_file='study.ipynb',language='python',kernel_type='notebook',is_private=True,
        enable_gpu=False,enable_tpu=False,enable_internet=False,competition_sources=['gemma-4-developer-agent'],
        dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],model_sources=[],kernel_sources=[],
        docker_image=IMAGE,docker_image_pinning_type='original')
    write(directory/'notebook/study.ipynb',notebook);write(directory/'notebook/kernel-metadata.json',meta)
    write(directory/'BUILD.json',dict(execution_id=ID+'-'+attempt,slug=slug,max_dispatches=1,
        Notebook_sha256=sha(notebook),wire_sha256=sha(json.dumps(nb).encode()),payload_sha256=sha(payload),
        selection_protocol_sha256=sha((HERE/'CANDIDATE_MANIFEST.json').read_bytes()),
        configuration=dict(GPU=False,TPU=False,internet=False,model_sources=[],Agent_runs=4,Gemma_calls=0,formal_submission=False),
        expected_candidates_in_order=['A','B','C'],sdk_versions={n:importlib.metadata.version(n) for n in ('kaggle','kagglesdk')},payload_members=reg['files']))
    print('SEALED_CPU_PAYLOAD',sha(payload),len(files))


def validate(attempt):
    d=HERE/attempt;b=json.loads((d/'BUILD.json').read_bytes());raw=(d/'payload.zip').read_bytes()
    assert sha(raw)==b['payload_sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        for n,h in b['payload_members'].items():assert sha(z.read(n))==h
    assert sha((d/'notebook/study.ipynb').read_bytes())==b['Notebook_sha256']
    return True


def factory(attempt):
    from u_re.v02.experiments.action_first_replication_01 import cpu_control as prior
    source=inspect.getsource(prior.factory)
    source=source.replace('gemma4-u-re-v02-','meer-v01-').replace("'v02-'+attempt","'meer-v01-'+attempt")
    source=source.replace('agent_runs==1','agent_runs==4')
    source=source.replace("if attempt.startswith('screen'):validate_screen(attempt)",'validate(attempt)')
    source=source.replace('Current V02 replication human task explicitly authorizes CPU native screening max16 first4 and final production-payload CPU acceptance. No Gemma/GPU/formal Submission in this CPU dispatch.',
        'Current human MEER V0.1 task authorizes CPU development, owned adversarial tests and official Compiler/ADK/Runner/Skill/native Verifier acceptance. Exactly one CPU save per version. No GPU/Gemma/formal Submission.')
    ns=dict(prior.__dict__,HERE=HERE,ROOT=ROOT,ID=ID,validate=validate)
    exec(compile(source,'<reused-CPU-controller>','exec'),ns)
    return ns['factory'](attempt,agent_runs=4)


if __name__=='__main__':
    import sys
    command,attempt=sys.argv[1:3]
    if command=='build':build(attempt)
    elif command=='launch':factory(attempt).launch()
    elif command=='collect':factory(attempt).collect(sys.argv[3])
