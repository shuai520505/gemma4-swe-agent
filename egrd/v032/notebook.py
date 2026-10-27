"""Seal a single private GPU Notebook with the validated CPU source closure."""
import base64
import io
import json
import zipfile

from meer.v01.build import archive
from s1.prepare import INSTALL,IMAGE
from .prepare import HERE,ROOT,PRIVATE,CPU_PRIVATE,REF,MODEL_REF,WINDOW,BASE,sha,write,verify_history


def freeze():
    identity=verify_history()
    historical=json.loads((ROOT/'u_re/v01/experiments/gemma_smoke_01/MODEL_RUNTIME_CONFIG.json').read_bytes())
    versions=dict(historical['historical_versions'],torch='2.10.0+cu128',**{'adk-eval-core':'0.1.0'})
    env=dict(model_source=MODEL_REF,model_files=historical['model_files'],versions=versions,
        Python='3.12',torch_cuda='12.8',devices='4x NVIDIA L4',tensor_parallel_size=4,
        VllmConfig=dict(host='127.0.0.1',port=8000,tool_call_parser='gemma4',reasoning_parser='gemma4',
            max_model_len=32768,dtype='bfloat16',gpu_memory_utilization=.90,enable_auto_tool_choice=True,
            enable_lora=False,scheduler_reserve_full_isl=False,tensor_parallel_size=4,startup_timeout=1200,
            extra_args=['--no-enable-prefix-caching']),
        generation={'max_completion_tokens':16384,'thinking_token_budget':4096,'chat_template_kwargs':{'enable_thinking':True}},
        explicit_request_seed=None,custom_Context_Guard=False,additional_safety_reserve=None,
        compaction_override=None,thought_history_filter_override=None,
        prefix_cache_policy='Disabled for both arms to avoid retaining task-specific KV between sessions',
        historical_serving_equivalence='HISTORICAL_SERVING_EQUIVALENCE_UNVERIFIED',
        driver='Observe actual compatible driver; no driver upgrade',docker_image=IMAGE)
    write(HERE/'GPU_ENVIRONMENT_LOCK.json',env)
    write(HERE/'MODEL_IDENTITY.json',dict(source=MODEL_REF,revision='Kaggle model instance version 2',
        files=historical['model_files'],actual_mounted_bytes='RECHECK_BEFORE_ANY_GENERATION',upstream_HF_commit=None))
    lock=dict(experiment='EGRD_V032_REAL_GEMMA_EVIDENCE_TO_PATCH',study='DEVELOPMENT_MECHANISM_STUDY',
        source_base_commit=BASE,owner_authorized=True,
        authorization_source='Explicit human EGRD V0.3.2 instruction in this conversation; one new GPU dispatch, two sessions A then B only',
        max_dispatches=1,max_sessions=2,order=['A','B'],task_id='django__django-16333',
        candidate_sha256=identity['S0_sha256'],inputs=identity['task_inputs'],receipt_sha256=identity['receipt_sha256'],
        CPU_archive_sha256=identity['CPU_archive_sha256'],CPU_payload_sha256=identity['CPU_payload_sha256'],
        environment_sha256=sha((HERE/'GPU_ENVIRONMENT_LOCK.json').read_bytes()),model_source=MODEL_REF,
        task_lock_sha256=sha((ROOT/'egrd/v031/TASK_IDENTITY_LOCK.json').read_bytes()),
        Agent_seconds=300,charged_tools=60,command_seconds=120,native_max_LLM_calls=500,
        model_requests_outside_scheduled_sessions=0,platform_window_seconds=WINDOW,
        shared_server=True,independent_workspaces_histories_and_workers=True,
        single_factor='Exact original frozen failure supplement appended only to B task input',
        no_adaptive_changes=True,no_reruns=True,formal_submission=False,
        context_policy='Native serving 32768 with unchanged 16384 output; no15360 Guard, safety override, history editing or seed injection',
        initial_admission='Both exact CPU-derived initial request bodies must fit actual serving /tokenize before A; actual first requests must match before forwarding',
        missing_submission='Record missing; retain unsubmitted fallback privately; evaluate original base as missing-patch negative, never repair success',
        primary='Independently reviewed defensible submitted behavioral repair plus fresh owned target/controls/regression',
        official_native_resolved=None,canonical_swebench_resolved=None,
        resource_planning=dict(report_seconds_floor=4*WINDOW+1200,report_multiplier_assumption=4,
            caveat='Conservative planning assumption, not measured Kaggle billing',
            envelope_seconds=7200,components='SDK1800 + model/file/source prep780 + load1200 + two bounded workers2820 + archival600',
            actual_platform_window_independent_field='Unavailable; verify accepted SaveKernel timeout and use first-cell elapsed dynamic gates'))
    write(HERE/'EXPERIMENT_FREEZE.json',lock)


def build():
    freeze()
    old=json.loads((ROOT/'egrd/v0311/CPU_BUILD.json').read_bytes())
    raw=(CPU_PRIVATE/'notebook-v1/payload.zip').read_bytes();assert sha(raw)==old['payload_sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if n!='v0311_registration.json'}
    # These CPU response generators are not part of the GPU executable entry.
    for name in ('egrd/v0311/cpu_preflight.py','egrd/v0311/scripted_boundary.py','egrd/v0311/boundary_audit.py'):
        if name!='egrd/v0311/boundary_audit.py':files.pop(name,None)
    names=('__init__.py','prepare.py','cleanup.py','source_observer.py','data.py','observe.py','evaluate.py','worker.py','coordinator.py',
           'EXPERIMENT_FREEZE.json','GPU_ENVIRONMENT_LOCK.json')
    for name in names:files['egrd/v032/'+name]=(HERE/name).read_bytes()
    prior_archive=json.loads((ROOT/'egrd/v0311/RAW_ARCHIVES.json').read_bytes())
    with zipfile.ZipFile(prior_archive['path']) as z:
        for arm in ('A','B'):
            files[f'egrd/v032/private/expected_{arm}.json']=z.read(f'results/{arm}/model-boundary/request_001.json')
    for n,body in files.items():
        if n.endswith('.py'):compile(body,n,'exec')
    reg=dict(files={n:sha(b) for n,b in files.items()},wheel_hashes=old['wheel_hashes'],entry='egrd.v032.coordinator.run',
             real_model_only=True,scope='One dispatch; exactly A then B; no readiness generations')
    files['v032_registration.json']=(json.dumps(reg,indent=2)+'\n').encode()
    payload=archive(files)
    folder=PRIVATE/'notebook-v1';folder.mkdir(parents=True,exist_ok=False)
    (folder/'payload.zip').write_bytes(payload)
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
SESSION_STARTED=time.monotonic()
RUN_DIR=Path('/kaggle/working/egrd-v032-real-gemma-ab');RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
raw=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(raw).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 assert z.testzip() is None and all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
 z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'v032_registration.json').read_bytes())
for n,digest in REG['files'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==digest,n
(RUN_DIR/'PAYLOAD_IDENTITY.json').write_text(json.dumps(dict(payload_sha256={sha(payload)!r},files=REG['files'])))
'''
    work='''device=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],capture_output=True,text=True,timeout=30)
(RUN_DIR/'EARLY_GPU_ALLOCATION.json').write_text(json.dumps(dict(returncode=device.returncode,stdout=device.stdout,stderr=device.stderr)))
assert device.returncode==0 and len(device.stdout.strip().splitlines())==4 and all('NVIDIA L4' in line for line in device.stdout.strip().splitlines()),'Actual 4xL4 allocation not available; no model loading'
WHEELHOUSE_DIR=next(p for p in Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl') if 'gemma-4-developer-agent-wheelhouse' in str(p)).parent
actual={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}
assert actual==REG['wheel_hashes']
'''+INSTALL+f'''
gates=json.loads((RUN_DIR/'DISPATCH_RESOURCE_BINDING.json').read_bytes())
from harness_v2.supervisor import supervise
outcome=supervise([sys.executable,'-m','egrd.v032.coordinator',str(RUN_DIR/'execution'),str(SESSION_STARTED),gates['remaining_report_seconds']],
 RUN_DIR/'execution',outer_seconds=max(1,{WINDOW}-(time.monotonic()-SESSION_STARTED)-300),
 stage_caps=dict(prepare_agent=1200,load_model=1300,cleanup=180),cwd=SOURCE)
(RUN_DIR/'NOTEBOOK_SUPERVISOR.json').write_text(json.dumps(outcome))
assert outcome['allow_next_run'],'Preserve failure and stop; no Notebook or arm retry'
'''
    # Contemporaneous quota binding is injected by the once-only dispatcher,
    # which freezes the exact resulting Notebook hash before sending SaveKernel.
    source_binding="(RUN_DIR/'DISPATCH_RESOURCE_BINDING.json').write_text(json.dumps(DISPATCH_RESOURCE_BINDING))\n"
    body='try:\n'+ '\n'.join(' '+line for line in (source_binding+work).splitlines())+'''
except BaseException as exc:
 (RUN_DIR/'NOTEBOOK_FAILURE.json').write_text(json.dumps(dict(type=type(exc).__name__,error=str(exc),retry=False)))
 raise
finally:
 try:
  from egrd.v032.cleanup import recover
  cleanup=recover(RUN_DIR/'execution')
  (RUN_DIR/'OWNED_ROOT_RECOVERY.json').write_text(json.dumps(cleanup))
 except BaseException as cleanup_error:
  (RUN_DIR/'OWNED_ROOT_RECOVERY_ERROR.json').write_text(json.dumps(dict(type=type(cleanup_error).__name__,error=str(cleanup_error))))
 from harness_v2.evidence import bundle
 print('EGRD_V032_RAW_ARCHIVE',bundle(RUN_DIR),flush=True)
'''
    for source in (setup,body):compile(source,'<GPU-notebook>','exec')
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),
        cells=[dict(cell_type='code',source=s,id=sha(s.encode())[:12],metadata={},outputs=[],execution_count=None) for s in (setup,body)])
    (folder/'study-template.ipynb').write_text(json.dumps(nb,indent=1)+'\n',encoding='utf8',newline='\n')
    metadata=dict(id=REF,title='EGRD V032 Real Gemma Evidence AB',code_file='study.ipynb',language='python',kernel_type='notebook',
        is_private=True,enable_gpu=True,enable_tpu=False,enable_internet=False,machine_shape='NvidiaL4',
        competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse','wudangdexiaodoashi/egrd-repair-development'],
        model_sources=[MODEL_REF],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    write(folder/'kernel-metadata.json',metadata)
    write(HERE/'BUILD.json',dict(payload_sha256=sha(payload),payload_bytes=len(payload),members=reg['files'],
        entry=reg['entry'],template_sha256=sha((folder/'study-template.ipynb').read_bytes()),metadata_sha256=sha((folder/'kernel-metadata.json').read_bytes()),
        environment_sha256=sha((HERE/'GPU_ENVIRONMENT_LOCK.json').read_bytes()),experiment_sha256=sha((HERE/'EXPERIMENT_FREEZE.json').read_bytes()),
        Notebook_ref=REF,window=WINDOW,competition_mount='Public host-only competition input for established L4 environment; no task/evaluator files read or staged from it'))
    print('Frozen real-Gemma payload',sha(payload),'NO DISPATCH')


if __name__=='__main__':build()
