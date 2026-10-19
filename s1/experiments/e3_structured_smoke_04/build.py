"""Immutable CPU-first payloads; no frozen source or candidate is rewritten."""
import ast
import base64
import json
from pathlib import Path
import zipfile
from experiments.prepare import write_new
from s1.prepare import INSTALL,IMAGE,MODEL_REF
from s1.util import archive,save,sha,sha_file
from . import EXPERIMENT_ID

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
MODULE='s1.experiments.e3_structured_smoke_04'


def sources():
    old=ROOT/'s1/experiments/e3_localize_smoke_03'
    prior=json.loads((old/'registration_cpu02.json').read_text())
    with zipfile.ZipFile(old/'results/cpu02/raw.zip') as z:
        assert z.testzip() is None
        files={n:z.read('source/'+n) for n in prior['source_hashes']}
    for name,digest in prior['source_hashes'].items():
        assert sha(files[name])==digest,name
        if name.startswith('s1/'):assert sha_file(ROOT/name)==digest,name
    for parent in (ROOT/'s1/verifier_v3',HERE):
        for p in parent.rglob('*'):
            if not p.is_file() or {'_local','__pycache__','results','notebooks'}.intersection(p.relative_to(parent).parts):continue
            if p.suffix=='.py' or parent.name=='verifier_v3' and p.suffix=='.json':files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for name in ('selection.json','selection_rule.json'):files[(HERE/name).relative_to(ROOT).as_posix()]=(HERE/name).read_bytes()
    old_protocol=json.loads((old/'protocol.json').read_text())
    return dict(version='s1-verifier-0.3.0',experiment_id=EXPERIMENT_ID,
        structured_test_count=sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test_') for n in ast.walk(ast.parse((ROOT/'s1/verifier_v3/tests.py').read_text()))),
        source_hashes={n:sha(b) for n,b in sorted(files.items())},frozen_parent_source_hashes=prior['source_hashes'],
        wheel_hashes=prior['wheel_hashes'],task_wheel_hashes=old_protocol['official_task_wheels']),files


def notebook(kind,files):
    payload=archive(files);slug='gemma4-s1-e3-struct04-'+kind
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
SESSION_STARTED=time.monotonic()
from pathlib import Path
from datetime import datetime,timezone
RUN_DIR=Path('/kaggle/working/s1_e3_structured_smoke_04')/{kind!r}/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(payload).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE));os.chdir(SOURCE)
REG=json.loads((SOURCE/'s1/registration.json').read_text())
for n,h in REG['source_hashes'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==REG['wheel_hashes'],'Model Wheelhouse drift'
(RUN_DIR/'wheel_hashes.json').write_text(json.dumps(actual,indent=2))
TASK_ROOTS=[p.parent for p in Path('/kaggle/input').rglob('tasks.jsonl') if (p.parent/'snapshots').is_dir()]
assert len(TASK_ROOTS)==1
TASK_WHEELS={{p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (TASK_ROOTS[0]/'wheels').glob('*.whl')}}
assert TASK_WHEELS==REG['task_wheel_hashes'],'Task wheel drift'
(RUN_DIR/'task_wheel_hashes.json').write_text(json.dumps(TASK_WHEELS,indent=2))
os.environ.update(VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',VLLM_ENGINE_READY_TIMEOUT_S='1200',VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS='1',NCCL_DEBUG='WARN',PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True',LOCAL_API_KEY='EMPTY',OPENAI_API_KEY='EMPTY')
'''
    if kind.startswith('cpu'):
        execution=f'''p=subprocess.run([sys.executable,'-m',{MODULE+'.cpu'!r},str(RUN_DIR/'validation')],cwd=SOURCE,capture_output=True,text=True,timeout=2600)
(RUN_DIR/'runner.stdout.log').write_text(p.stdout);(RUN_DIR/'runner.stderr.log').write_text(p.stderr)
print(p.stdout+p.stderr,flush=True)
assert p.returncode==0,'CPU or selected baseline blocked; no GPU permitted'
'''
    else:execution=f'''from {MODULE}.session import run
await run(SOURCE,RUN_DIR,session_started=SESSION_STARTED)
'''
    combined='from harness_v2.evidence import bundle\ntry:\n'+''.join('    '+line+'\n' for line in (INSTALL+'\n'+execution).splitlines())+"finally:print('STRUCTURED_E3_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for code in (setup,combined):
        compile(code,'<notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
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


def gpu(revision):
    reg,files=sources();assert reg==json.loads((HERE/('registration_'+revision+'.json')).read_text()),'CPU source drift'
    directory=HERE/'_local'/(revision+'-extract');gate=json.loads((directory/'validation/cpu_gate.json').read_text())
    assert gate['passed'] and gate['structured_tests']==reg['structured_test_count'] and gate['selected_baseline']['eligible']
    assert gate['source_hashes']==reg['source_hashes']
    for name,digest in reg['source_hashes'].items():assert sha_file(directory/'source'/name)==digest,name
    selected=json.loads((HERE/'selection.json').read_text())
    inputs=json.loads((directory/'validation/selected_baseline/task_inputs.json').read_text())
    assert set(inputs)=={selected['instance_id']}
    prior=json.loads((ROOT/'s1/experiments/e3_localize_smoke_03/protocol.json').read_text())
    candidates=json.loads((ROOT/'s1/candidates.json').read_text())
    assert candidates['control']['config']==candidates['e3_locate']['config']
    assert (ROOT/'candidates/s0/submission/prompts/system.md').read_bytes()==(ROOT/'s1/candidates/control/prompts/system.md').read_bytes()
    for arm in ('control','e3_locate'):
        assert sha_file(ROOT/'s1/packages'/arm/'submission.zip')==candidates[arm]['zip_sha256']
        for name,digest in candidates[arm]['members'].items():assert sha_file(ROOT/'s1/candidates'/arm/name)==digest
    protocol=dict(experiment_id=EXPERIMENT_ID,infrastructure_version=reg['version'],status_at_registration='not_executed',
        parent_commit='25c29549a92d669de7ce98b5f57febf6f35770ee',selection=selected,
        source_hashes=reg['source_hashes'],registration_sha256=sha_file(HERE/('registration_'+revision+'.json')),
        CPU_tests=gate['tests_run'],CPU_gate_sha256=sha_file(directory/'validation/cpu_gate.json'),CPU_raw_sha256=sha_file(HERE/'results'/revision/'raw.zip'),
        model=MODEL_REF,model_files=prior['model_files'],wheel_hashes=reg['wheel_hashes'],task_wheel_hashes=reg['task_wheel_hashes'],
        candidates={arm:candidates[arm] for arm in ('control','e3_locate')},task_inputs=inputs,
        runs=[dict(index=1,instance_id=selected['instance_id'],arm='control'),dict(index=2,instance_id=selected['instance_id'],arm='e3_locate')],
        condition='31BQATv2,4L4/TP4,context32768/safety1024,output16384/thinking4096/seed17,300s/60tools/command120s; omitted include_thoughts/sampling; frozen Prompt sole factor',
        isolation='Clean independent native Agent and verifier sandboxes per arm; evaluator-only clean baseline; no reference repair or prior Patch supplied',
        clocks='10800s setup-origin Notebook window with900s finalization; each1350s outer+60s server-idle observation; nativeAgent300/verifier300 unchanged',
        verifier='Original native JUnit byte-copy before cleanup; strict XML/count/terminal-summary/exit consistency. No free-text error scanner. Real ordinary assertion failure and empty but fully evaluated Patch continue. Error event attribution requires baseline/root-cause evidence; ambiguous errors fail closed as unknown, not automatically environmental. Historical no-XML nonzero replay is never a prospective admission.',
        cancellation='Unique request ID and one real terminal; native deadline/end timing+worker cleanup prove client cancel; usage absent remainsnull/partial. Three server zero-running/waiting snapshots>=1s apart before next arm; no invented request-specific abort. Stop if gauges absent/nonidle60s.',
        stop='Only true/unknown infrastructure,attribution-integrity,model/hash/config drift,unparsed/contradictory verifier evidence,leakage,cleanup/reclamation/resource failure. Retain valid ordinary test failures and continue. No retries/hotfixes/replacement or old trace splicing.',
        interpretation='One new selected-task mechanism pair; correctness and old behavior matter more than edit speed. Fixed control-first order confounds small timing changes. No population repair-rate or leaderboard claim.',
        authorization=dict(GPU_pairs=1,Agent_runs=2,LoRA=False,formal_submission=False,other_factors=False))
    save(HERE/'protocol.json',protocol)
    files.update({'s1/registration.json':(HERE/('registration_'+revision+'.json')).read_bytes(),
        's1/cpu_gate.json':(directory/'validation/cpu_gate.json').read_bytes(),
        's1/gpu_protocol.json':(HERE/'protocol.json').read_bytes()})
    notebook('gpu',files)


if __name__=='__main__':
    import sys
    cpu(sys.argv[1]) if sys.argv[1].startswith('cpu') else gpu(sys.argv[2])
