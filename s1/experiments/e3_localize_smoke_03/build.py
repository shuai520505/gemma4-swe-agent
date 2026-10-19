"""Build this study from the byte-verified 97-test recovery payload, no old evidence edits."""
import ast
import base64
import json
from pathlib import Path
import zipfile
from experiments.prepare import write_new
from s1.prepare import INSTALL,IMAGE,MODEL_REF
from s1.util import archive,save,sha,sha_file
from . import EXPERIMENT_ID

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
MODULE='s1.experiments.e3_localize_smoke_03'


def sources():
    prior=ROOT/'s1/infrastructure_recovery'
    reg=json.loads((prior/'registrations/r05.json').read_text())
    gate=json.loads((prior/'results/r05/validation/cpu_gate.json').read_text())
    assert gate['passed'] and gate['tests_run']==97 and gate['source_hashes']==reg['source_hashes']
    assert sha_file(prior/'results/r05/raw.zip')=='62914802d04f25f0e37f04d15f32c257362eb9a2ca79a74a8bc790aafb7c71fd'
    with zipfile.ZipFile(prior/'results/r05/raw.zip') as z:
        assert z.testzip() is None
        files={name:z.read('source/'+name) for name in reg['source_hashes']}
    for name,digest in reg['source_hashes'].items():
        assert sha(files[name])==digest,name
        if name.startswith('s1/'):assert sha_file(ROOT/name)==digest,name
    for p in HERE.glob('*.py'):files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    return dict(reg,revision=EXPERIMENT_ID,experiment_id=EXPERIMENT_ID,
        recovery_97_source_hashes=reg['source_hashes'],source_hashes={n:sha(b) for n,b in sorted(files.items())}),files


def notebook(kind,files):
    payload=archive(files);slug='gemma4-s1-e3-smoke03-'+kind
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
SESSION_STARTED=time.monotonic()
from pathlib import Path
from datetime import datetime,timezone
RUN_DIR=Path('/kaggle/working/s1_e3_localize_smoke_03')/{kind!r}/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(payload).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
os.chdir(SOURCE)
REG=json.loads((SOURCE/'s1/registration.json').read_text())
for n,h in REG['source_hashes'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==REG['wheel_hashes'],'Official wheel drift'
(RUN_DIR/'wheel_hashes.json').write_text(json.dumps(actual,indent=2))
os.environ.update(VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',VLLM_ENGINE_READY_TIMEOUT_S='1200',VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS='1',NCCL_DEBUG='WARN',PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True',LOCAL_API_KEY='EMPTY',OPENAI_API_KEY='EMPTY')
'''
    if kind.startswith('cpu'):
        execution=f'''p=subprocess.run([sys.executable,'-m',{MODULE+'.cpu'!r},str(RUN_DIR/'validation')],cwd=SOURCE,capture_output=True,text=True,timeout=2400)
(RUN_DIR/'runner.stdout.log').write_text(p.stdout);(RUN_DIR/'runner.stderr.log').write_text(p.stderr)
print(p.stdout+p.stderr,flush=True)
assert p.returncode==0,'CPU/Phase2 gate failed; GPU forbidden'
'''
    else:execution=f'''from {MODULE}.session import run
await run(SOURCE,RUN_DIR,session_started=SESSION_STARTED)
'''
    combined='from harness_v2.evidence import bundle\ntry:\n'+''.join('    '+line+'\n' for line in (INSTALL+'\n'+execution).splitlines())+"finally:print('E3_SMOKE03_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for code in (setup,combined):
        compile(code,'<notebook>', 'exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=code,outputs=[],execution_count=None,id=sha(code.encode())[:12]))
    raw=(json.dumps(dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3')),nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    directory=HERE/'notebooks'/kind;write_new(directory/'study.ipynb',raw)
    metadata=dict(id='wudangdexiaodoashi/'+slug,title=slug,code_file='study.ipynb',language='python',kernel_type='notebook',
        is_private=True,enable_gpu=kind=='gpu',enable_tpu=False,enable_internet=False,
        competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],
        model_sources=[MODEL_REF] if kind=='gpu' else [],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    if kind=='gpu':metadata['machine_shape']='NvidiaL4'
    save(directory/'kernel-metadata.json',metadata)
    save(HERE/(kind+'_notebook.json'),dict(kernel=metadata['id'],notebook_sha256=sha(raw),payload_sha256=sha(payload),status='not_executed'))
    print(directory)


def cpu(kind):
    reg,files=sources();save(HERE/('registration_'+kind+'.json'),reg)
    files['s1/registration.json']=(HERE/('registration_'+kind+'.json')).read_bytes();notebook(kind,files)


def gpu():
    reg,files=sources();assert reg==json.loads((HERE/'registration_cpu02.json').read_text()),'CPU/source drift'
    directory=HERE/'_local/cpu02-extract';gate=json.loads((directory/'validation/cpu_gate.json').read_text())
    assert gate['passed'] and gate['tests_run']==100 and gate['Rich_full_phase2_environment']['eligible']
    assert gate['source_hashes']==reg['source_hashes']
    for name,digest in reg['source_hashes'].items():assert sha_file(directory/'source'/name)==digest,name
    draft=json.loads((ROOT/'s1/infrastructure_recovery/NEXT_GPU_PREREGISTRATION_DRAFT.json').read_text())
    inputs=json.loads((directory/'validation/rich_full_phase2/task_inputs.json').read_text())
    assert inputs=={'rich_3278':draft['task_inputs']['rich_3278']}
    candidates=json.loads((ROOT/'s1/candidates.json').read_text())
    assert candidates['control']['config']==candidates['e3_locate']['config']
    for arm in ('control','e3_locate'):
        assert sha_file(ROOT/'s1/packages'/arm/'submission.zip')==candidates[arm]['zip_sha256']
        for name,digest in candidates[arm]['members'].items():assert sha_file(ROOT/'s1/candidates'/arm/name)==digest
    protocol=dict(experiment_id=EXPERIMENT_ID,status_at_registration='not_executed',parent_commit='4d81fd7368d8ae1d4f9a4ccb5fbbc90099f3beb4',
        source_hashes=reg['source_hashes'],registration_sha256=sha_file(HERE/'registration_cpu02.json'),
        CPU_tests=100,CPU_gate_sha256=sha_file(directory/'validation/cpu_gate.json'),CPU_raw_sha256=sha_file(HERE/'results/cpu02/raw.zip'),
        model=MODEL_REF,model_files=draft['model_files'],wheel_hashes=reg['wheel_hashes'],
        official_task_wheels=draft['official_task_wheel_inventory'],selected_build_wheels=draft['selected_build_wheels'],
        candidates={arm:candidates[arm] for arm in ('control','e3_locate')},task_inputs=inputs,
        runs=[dict(index=1,instance_id='rich_3278',arm='control'),dict(index=2,instance_id='rich_3278',arm='e3_locate')],
        GPU='4 L4, TP4; official31B QAT version2; context32768',context_safety=1024,
        parameters='300s Agent / 60 tools / 120s command / output16384 / thinking4096 / seed17; include_thoughts and sampling omitted identically',
        agent='One official ADK Agent and six official tools. Only frozen Prompt differs. No private strategy controller.',
        isolation='Independent worker processes, clean official snapshots and verifier sandboxes. No Patch, traces or discoveries shared. Evaluator-only full baseline preflight on CPU and GPU host; no reference solution used.',
        clock='Notebook setup origin includes install/hash/load; 10800s global, 900s finalization, each1350s outer plus60s reclamation admission',
        cancellation='Unique ID + real CancelledError + exactly one terminal + verified native300s cutoff/end event within2s + worker/sandbox cleanup. Unreceived usage null/partial. Three server /metrics snapshots, >=1s apart, zero running/waiting before any next arm. Missing gauges or60s nonidle stops. Client cancel is not backend proof. Post-worker idle bounds reclamation only at observation time, not immediate abort latency.',
        stop='Global immediate STOP on hash/model/parameter drift, unknown HTTP terminal, transport failure, server reclamation unknown, verifier setup/collection errors, absent native Patch/Phase2, leakage, dirty sandbox/cleanup failure or insufficient full slot. No retries/hotfixes/replacement/splicing; pending not_run; unattribuable environment unknown.',
        empty_patch='Retain evidence; fails complete-infrastructure gate, so successor not_run. Ordinary assertion failure with complete evidence continues.',
        mechanism='Manual event/result/content audit; first successful production diff is not correctness. Penalize premature wrong edits; compare pre-edit calls, overlapping reads, failed tools, changed-source verification, submit, Phase2, tokens and time. One fixed-order pair cannot estimate population gain.',
        authorization=dict(GPU_pairs=1,GPU_Agent_runs=2,formal_submission=False,E1=False,E2=False,E4=False,CURE=False,LoRA=False))
    save(HERE/'protocol.json',protocol)
    files.update({'s1/registration.json':(HERE/'registration_cpu02.json').read_bytes(),
        's1/cpu_gate.json':(directory/'validation/cpu_gate.json').read_bytes(),
        's1/gpu_protocol.json':(HERE/'protocol.json').read_bytes()})
    notebook('gpu',files)


if __name__=='__main__':
    import sys
    cpu(sys.argv[1]) if sys.argv[1].startswith('cpu') else gpu()
