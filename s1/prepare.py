"""Self-contained Notebook builder. Immutable registrations; CPU gate precedes GPU."""
import argparse
import ast
import base64
import json
from pathlib import Path
import subprocess
from experiments.prepare import write_new
from . import VERSION,MODEL
from .util import sha,sha_file,save,archive

ROOT=Path(__file__).resolve().parents[1]
SELECTED={'smoke':['requests_7328'],'screen_a':['requests_7427','rich_3894'],
          'screen_b':['fastapi_14794','fastapi_14349']}
EXPOSED=['fastapi_15661','fastapi_15589','requests_7315','rich_3777','rich_4006',
         'requests_7309','fastapi_14258','rich_3052','httpx_3672']
MODEL_REF='google/gemma-4/Other/'+MODEL+'/2'
IMAGE='gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461'


def register(revision,evidence_repo):
    original=Path(evidence_repo)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()=='972d1dd940db3910dd78685d6e37152e96ab514b' or (ROOT/'s1/registrations').is_dir()
    r12=json.loads((ROOT/'harness_v2/registrations/r12.json').read_text())
    # Copy byte-preserving frozen evidence into the upload only. Never rewrite
    # a frozen working file to correct a Windows checkout newline difference.
    files={n:(original/n).read_bytes() for n in r12['source_hashes']}
    assert all(sha(files[n])==h for n,h in r12['source_hashes'].items())
    files['experiments/prepare.py']=(ROOT/'experiments/prepare.py').read_bytes()
    files['scripts/agent_config.py']=(ROOT/'scripts/agent_config.py').read_bytes()
    files['tests/test_submission.py']=(ROOT/'tests/test_submission.py').read_bytes()
    for p in (ROOT/'submission').rglob('*'):
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for p in (ROOT/'s1').rglob('*.py'):
        if 'results' not in p.parts:files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for name in ('candidates.json',):files['s1/'+name]=(ROOT/'s1'/name).read_bytes()
    for parent in ('candidates','packages'):
        for p in (ROOT/'s1'/parent).rglob('*'):
            if p.is_file():files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    rows={r['instance_id']:r for r in map(json.loads,(ROOT.parent/'official-inputs/tasks.jsonl').read_text(encoding='utf-8').splitlines())}
    public={i:{k:rows[i][k] for k in ('instance_id','repo','base_commit','problem_statement')}
        for values in SELECTED.values() for i in values}
    assert not set(public).intersection(EXPOSED)
    wheels=json.loads((ROOT/'experiments/formal-paired-01/protocol.json').read_text())['wheel_hashes']
    registration=dict(version=VERSION,revision=revision,status='not_executed',source_hashes={n:sha(b) for n,b in files.items()},
        wheel_hashes=wheels,selected=SELECTED,public_issues=public,excluded=EXPOSED,
        source_base='972d1dd940db3910dd78685d6e37152e96ab514b',CURE_source_included=False)
    save(ROOT/f's1/registrations/{revision}.json',registration)
    files['s1/registration.json']=(ROOT/f's1/registrations/{revision}.json').read_bytes()
    return registration,files


INSTALL='''import glob
os.environ.update(TRANSFORMERS_NO_TF='1',TRANSFORMERS_NO_FLAX='1',TRANSFORMERS_OFFLINE='1',HF_HUB_OFFLINE='1',LITELLM_LOCAL_MODEL_COST_MAP='True',LITELLM_TELEMETRY='False',OTEL_SDK_DISABLED='true',PYTHONIOENCODING='utf-8')
for pattern in ('/usr/local/lib/python*/dist-packages/*cutlass*.pth','/usr/local/lib/python*/site-packages/*cutlass*.pth'):
    for path in glob.glob(pattern):Path(path).unlink(missing_ok=True)
links=RUN_DIR/'wheelhouse_links';links.mkdir()
try:
    for p in WHEELHOUSE_DIR.glob('*.whl'):
        if 'cutlass' in p.name.lower():continue
        name=p.name.replace('cu128','+cu128') if 'cu128' in p.name and '+' not in p.name else p.name
        (links/name).symlink_to(p)
    with (RUN_DIR/'installation.log').open('x') as log:
        subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps','--force-reinstall']+sorted(str(p) for p in links.glob('*.whl')),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
finally:shutil.rmtree(links)
'''


def make_notebook(kind,revision,files,registration):
    payload=archive(files)
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
from datetime import datetime,timezone
RUN_DIR=Path('/kaggle/working/s1_e1_01')/{kind!r}/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(payload).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'s1/registration.json').read_text())
for n,digest in REG['source_hashes'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==digest,n
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==REG['wheel_hashes'],'Wheel bytes drift'
(RUN_DIR/'wheel_hashes.json').write_text(json.dumps(actual,indent=2))
os.environ.update(VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',VLLM_ENGINE_READY_TIMEOUT_S='1200',VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS='1',NCCL_DEBUG='WARN',PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True',LOCAL_API_KEY='EMPTY',OPENAI_API_KEY='EMPTY')
'''
    if kind=='cpu':
        run='''from harness_v2.evidence import bundle
try:
    p=subprocess.run([sys.executable,'-m','s1.cpu',str(RUN_DIR/'validation')],cwd=SOURCE,capture_output=True,text=True,timeout=1500)
    (RUN_DIR/'runner.stdout.log').write_text(p.stdout);(RUN_DIR/'runner.stderr.log').write_text(p.stderr)
    print(p.stdout+p.stderr,flush=True)
    assert p.returncode==0,'CPU gate failed; GPU forbidden'
    from s1.task_identity import identify,find_data
    selection=[i for items in REG['selected'].values() for i in items]
    (RUN_DIR/'task_inputs.json').write_text(json.dumps(identify(find_data(),selection),indent=2))
finally:print('S1_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)
'''
    else:
        run=f'''from harness_v2.evidence import bundle
from s1.session import run
try:await run(SOURCE,RUN_DIR,{kind!r})
finally:print('S1_GPU_EVIDENCE',bundle(RUN_DIR),flush=True)
'''
    cells=[]
    for code in (setup,INSTALL,run):
        compile(code,'<s1-notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=code,outputs=[],execution_count=None,id=sha(code.encode())[:12]))
    raw=(json.dumps(dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3')),nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    slug=f'gemma4-s1-e1-01-{revision}-{kind.replace("_","-")}'
    base=ROOT/f's1/notebooks/{revision}/{kind}'
    write_new(base/'study.ipynb',raw)
    meta=dict(id='wudangdexiaodoashi/'+slug,title=slug,code_file='study.ipynb',language='python',kernel_type='notebook',
        is_private=True,enable_gpu=kind!='cpu',enable_tpu=False,enable_internet=False,
        competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],
        model_sources=[] if kind=='cpu' else [MODEL_REF],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    if kind!='cpu':meta['machine_shape']='NvidiaL4'
    save(base/'kernel-metadata.json',meta)
    save(ROOT/f's1/registrations/{revision}-{kind}-notebook.json',dict(kernel=meta['id'],notebook_sha256=sha(raw),payload_sha256=sha(payload),status='not_executed'))
    return base


def cpu(revision,evidence_repo):
    reg,files=register(revision,evidence_repo)
    return make_notebook('cpu',revision,files,reg)


def gpu(kind,revision,cpu_dir,model_identity,previous_gate=None):
    cpu_dir=Path(cpu_dir)
    reg=json.loads((ROOT/f's1/registrations/{revision}.json').read_text())
    gate=json.loads((cpu_dir/'validation/cpu_gate.json').read_text())
    assert gate['passed'] and gate['legacy_count']==38 and gate['new_count']>=18 and gate['static_count']==5
    assert gate['source_hashes']==reg['source_hashes']
    # Use the exact CPU uploaded bytes, including byte-preserved baseline files.
    files={n:(cpu_dir/'source'/n).read_bytes() for n in reg['source_hashes']}
    assert all(sha(b)==reg['source_hashes'][n] for n,b in files.items())
    for n in reg['source_hashes']:
        if n.startswith('s1/') and n.endswith('.py'):assert sha_file(ROOT/n)==reg['source_hashes'][n],n
    files['s1/registration.json']=(ROOT/f's1/registrations/{revision}.json').read_bytes()
    files['s1/cpu_gate.json']=(cpu_dir/'validation/cpu_gate.json').read_bytes()
    inputs=json.loads((cpu_dir/'task_inputs.json').read_text())
    candidates=json.loads((ROOT/'s1/candidates.json').read_text())
    batches={};index=1
    for batch,identifiers in SELECTED.items():
        rows=[]
        for j,ident in enumerate(identifiers):
            # Within the four screening tasks: AB, BA, AB, BA.
            arms=['control','e1_output8192'] if j%2==0 else ['e1_output8192','control']
            for arm in arms:rows.append(dict(index=index,instance_id=ident,arm=arm));index+=1
        batches[batch]=rows
    protocol=dict(experiment_id='s1-e1-public-01',status_at_registration='not_executed',runner_version=VERSION,
        cpu_revision=revision,cpu_gate_sha256=sha_file(cpu_dir/'validation/cpu_gate.json'),
        source_hashes=reg['source_hashes'],model=MODEL_REF,
        model_files=json.loads(Path(model_identity).read_text())['files'],wheel_hashes=reg['wheel_hashes'],
        candidates={k:candidates[k] for k in ('control','e1_output8192')},task_inputs=inputs,batches=batches,
        selection='Issue-only selection before observing any reference/test patch. Public exposure/model contamination cannot be excluded. Three new repos; HTTPX has only one public task, already exposed.',
        excluded=EXPOSED,session_seconds=10800,context=dict(capacity=32768,safety=1024,compaction_interval=5,overlap=1,threshold=8192,retention=4),
        single_factor='Only output cap 16384 vs8192; S0 Prompt/default sampling/default include_thoughts and thinking4096. Both arms seed17 as new common research condition; no reuse of S0 outcome.',
        primary='All four complete screening pairs official resolved difference; smoke excluded. Report discordant pairs; no robust superiority claim from n4.',
        stop='Global stop on first infrastructure/compatibility/evidence/leakage/cleanup failure or unknown. No retry, task replacement or splicing. Native assertion failure with evidence continues. No extension beyond four screening tasks in this protocol.',
        advancement='Smoke infrastructure gate including offline raw audit before screen_a; screen_b requires screen_a gate. No candidate freezing on speed alone. No outcome-based task substitution.',
        costs=dict(agent_seconds_per_run=300,runs_smoke=2,runs_screen=8,max_agent_minutes=50,
            outer_seconds_per_run=1350,startup_allowance_seconds=2700,finalization_allowance_seconds=900,
            max_node_hours_all_three_batches=6.75,max_L4_GPU_hours_all_three_batches=27),
        formal_submission=False,LoRA=False,CURE=False)
    save(ROOT/'s1/experiments/e1-public-01/protocol.json',protocol)
    files['s1/gpu_protocol.json']=(ROOT/'s1/experiments/e1-public-01/protocol.json').read_bytes()
    if kind!='smoke':
        assert previous_gate
        prior=json.loads(Path(previous_gate).read_text())
        assert prior['infrastructure_passed'] and prior['protocol_sha256']==sha(files['s1/gpu_protocol.json'])
        files['s1/previous_batch_gate.json']=Path(previous_gate).read_bytes()
    return make_notebook(kind,revision,files,reg)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['cpu','smoke','screen_a','screen_b']);p.add_argument('--revision',default='r01')
    p.add_argument('--evidence-repo',default=str(ROOT.parent/'gemma4-swe-agent'))
    p.add_argument('--cpu-dir');p.add_argument('--model-identity');p.add_argument('--previous-gate')
    a=p.parse_args()
    print(cpu(a.revision,a.evidence_repo) if a.kind=='cpu' else gpu(a.kind,a.revision,a.cpu_dir,a.model_identity,a.previous_gate))
