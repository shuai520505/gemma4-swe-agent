"""Byte-pinned standalone Notebook builder for this new experiment only."""
import argparse
import ast
import base64
import json
from pathlib import Path
import subprocess

from experiments.prepare import write_new
from s1.prepare import INSTALL, IMAGE, MODEL_REF
from s1.util import archive, save, sha, sha_file
from . import EXPERIMENT_ID

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
REL=HERE.relative_to(ROOT).as_posix()
MODULE='s1.experiments.e1_outputcap_smoke_02'


def source_files():
    baseline=json.loads((ROOT/'s1/registrations/r04.json').read_text())
    files={n:(ROOT/'s1/_local/cpu-r04/source'/n).read_bytes() for n in baseline['source_hashes']}
    assert all(sha(b)==baseline['source_hashes'][n] for n,b in files.items())
    for n,h in baseline['source_hashes'].items():
        if n.startswith('s1/'):assert sha_file(ROOT/n)==h,n
    for p in HERE.glob('*.py'):
        files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    registration=dict(baseline,revision='r04-observer-01',experiment_id=EXPERIMENT_ID,
        source_hashes={n:sha(b) for n,b in sorted(files.items())},
        frozen_r04_source_hashes=baseline['source_hashes'])
    return registration, files


def notebook(kind, files, registration):
    payload=archive(files)
    slug='gemma4-s1-e1-smoke02-'+kind
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
SESSION_STARTED=time.monotonic()
from pathlib import Path
from datetime import datetime,timezone
RUN_DIR=Path('/kaggle/working/s1_e1_outputcap_smoke_02')/{kind!r}/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
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
        execution=f'''p=subprocess.run([sys.executable,'-m',{MODULE+'.cpu'!r},str(RUN_DIR/'validation')],cwd=SOURCE,capture_output=True,text=True,timeout=1500)
(RUN_DIR/'runner.stdout.log').write_text(p.stdout);(RUN_DIR/'runner.stderr.log').write_text(p.stderr)
print(p.stdout+p.stderr,flush=True)
assert p.returncode==0,'CPU gate failed; GPU forbidden'
from s1.task_identity import identify,find_data
(RUN_DIR/'task_inputs.json').write_text(json.dumps(identify(find_data(),['requests_7328']),indent=2))
'''
    else:
        execution=f'''from {MODULE}.startup import run
await run(SOURCE,RUN_DIR,'smoke',session_started=SESSION_STARTED)
'''
    # Installation and execution share a finally, so even early failures retain
    # logs. The global clock originates in setup, before hashes/installation.
    combined='from harness_v2.evidence import bundle\ntry:\n'+''.join(
        '    '+line+'\n' for line in (INSTALL+'\n'+execution).splitlines())+"finally:print('E1_SMOKE02_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for code in (setup,combined):
        compile(code,'<notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=code,outputs=[],execution_count=None,id=sha(code.encode())[:12]))
    raw=(json.dumps(dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3')),nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    directory=HERE/'notebooks'/kind
    write_new(directory/'study.ipynb',raw)
    meta=dict(id='wudangdexiaodoashi/'+slug,title=slug,code_file='study.ipynb',language='python',kernel_type='notebook',
        is_private=True,enable_gpu=kind!='cpu',enable_tpu=False,enable_internet=False,
        competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],
        model_sources=[] if kind=='cpu' else [MODEL_REF],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    if kind!='cpu':meta['machine_shape']='NvidiaL4'
    save(directory/'kernel-metadata.json',meta)
    save(HERE/f'{kind}_notebook.json',dict(kernel=meta['id'],notebook_sha256=sha(raw),payload_sha256=sha(payload),status='not_executed'))
    return directory


def cpu():
    reg,files=source_files()
    save(HERE/'registration.json',reg)
    files['s1/registration.json']=(HERE/'registration.json').read_bytes()
    return notebook('cpu',files,reg)


def gpu(cpu_directory):
    directory=Path(cpu_directory)
    reg=json.loads((HERE/'registration.json').read_text())
    gate=json.loads((directory/'validation/cpu_gate.json').read_text())
    assert gate['passed'] and gate['tests_run']>=77 and gate['startup_observer_count']==6
    assert gate['source_hashes']==reg['source_hashes']
    files={n:(directory/'source'/n).read_bytes() for n in reg['source_hashes']}
    assert all(sha(b)==reg['source_hashes'][n] for n,b in files.items())
    assert source_files()[0]['source_hashes']==reg['source_hashes'],'CPU source drift'
    previous=json.loads((ROOT/'s1/experiments/e1-public-01/protocol.json').read_text())
    inputs=json.loads((directory/'task_inputs.json').read_text())
    assert set(inputs)=={'requests_7328'}
    assert inputs['requests_7328']==previous['task_inputs']['requests_7328']
    candidates=json.loads((ROOT/'s1/candidates.json').read_text())
    protocol=dict(experiment_id=EXPERIMENT_ID,status_at_registration='not_executed',
        parent_source_commit='be8c80efc65866f31fdaf6e9f0a4455347cb3b99',
        r04_unchanged=True,registration_sha256=sha_file(HERE/'registration.json'),
        source_hashes=reg['source_hashes'],cpu_gate_sha256=sha_file(directory/'validation/cpu_gate.json'),
        cpu_raw_sha256=sha_file(HERE/'results/cpu/raw.zip'),cpu_tests=gate['tests_run'],
        model=MODEL_REF,model_files=previous['model_files'],wheel_hashes=reg['wheel_hashes'],
        candidates={k:candidates[k] for k in ('control','e1_output8192')},task_inputs=inputs,
        batches={'smoke':[dict(index=1,instance_id='requests_7328',arm='control'),dict(index=2,instance_id='requests_7328',arm='e1_output8192')]},
        context=previous['context'],session_seconds=10800,
        clocks='Notebook setup before extraction, hashes, installation, model loading; r04 complete-slot admission plus 900s finalization at every task',
        single_factor='max_output_tokens A16384 vs B8192. Same original S0 Prompt; thinking4096 is INSIDE output cap; seed17; include_thoughts omitted; all other sampling defaults omitted.',
        isolation='Two fresh worker process trees and independently reset official base snapshots, separate native contexts/verifiers, no shared Patch, thoughts or sandbox. Official hidden tests only in evaluator.',
        stop='Global stop on any model/parameter/hash/context/compatibility/leakage/evidence/cleanup failure or insufficient full task slot. r04 audit remains strict: unknown or absent real Phase2 stops. Confirmed ordinary test failure with complete evidence continues. Empty Patch/timeouts are retained, never rerun; if they fail the evidence gate, B remains not_run. No hotfix, retry, replacement or splicing within this ID.',
        interpretation='One engineering/mechanism smoke pair, excluded from future four-task main effects. No repair-rate/generalization conclusion. Public model pretraining exposure cannot be excluded.',
        decision='Go only if startup and both task infrastructure gates pass and evidence supports safe output behavior; no further run authorized here. Model success alone insufficient; truncation/unknown/cleanup loss => No-Go pending new registration.',
        startup='One real chat completion via unchanged s1.preflight.check_model tools=None; health/models/tokenizer, actual usage equality, oversize reject, nonempty text. Passive observer journals full HTTP and tokenizer before errors. Startup costs separate.',
        outputs=dict(platform_root='/kaggle/working/s1_e1_outputcap_smoke_02/smoke',local_root=REL+'/results/gpu',raw_archive='raw.zip',report=REL+'/S1_E1_GPU_PAIR_RESULTS.md'),
        costs=dict(agent_seconds_per_run=300,command_seconds=120,tool_budget=60,outer_seconds_per_run=1350,verification_seconds=300,session_seconds=10800,finalization_seconds=900,reservation_is_not_usage=True),
        authorization=dict(smoke_runs=2,screening_runs=0,formal_submission=False,LoRA=False,CURE=False))
    save(HERE/'protocol.json',protocol)
    files.update({'s1/registration.json':(HERE/'registration.json').read_bytes(),
        's1/cpu_gate.json':(directory/'validation/cpu_gate.json').read_bytes(),
        's1/gpu_protocol.json':(HERE/'protocol.json').read_bytes()})
    return notebook('smoke',files,reg)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['cpu','gpu']);parser.add_argument('--cpu-directory')
    args=parser.parse_args()
    print(cpu() if args.kind=='cpu' else gpu(args.cpu_directory))
