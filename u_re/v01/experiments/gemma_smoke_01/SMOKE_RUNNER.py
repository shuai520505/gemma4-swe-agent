"""One engineering smoke, no Kaggle write API. Default is an offline plan.

Real execution requires a separately reviewed grant AND deployment-isolation proof.
Mock transport never imports torch/ADK or starts processes/models.
"""
import argparse
import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from u_re.v01.experiments.gemma_smoke_01.inputs import candidate,agent_input,ZIPS,TOOLS

EXPERIMENT='U-RE-V01-GEMMA-SMOKE-01'
STAGES=['PREFLIGHT','LOAD_MODEL','READY_CHECK','INIT_AGENT','LOAD_TASK','RUN_AGENT',
        'COLLECT_PATCH','NATIVE_VERIFY','EXPORT','CLEANUP']

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def save(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');tmp.replace(path)

def claim_once(output):
    with (Path(output)/'dispatch.claim').open('x') as f:
        f.write(EXPERIMENT+'\n');f.flush()
        import os
        os.fsync(f.fileno())

def authorize(grant,protocol):
    """No default grant and no boolean-only bypass. Provenance must be human-reviewed."""
    required={'experiment_id':EXPERIMENT,'task':'fastapi_14492','candidate':'noegv',
        'agent_runs':1,'agent_seconds':300,'tool_budget':60,'gpu_count':4,'gpu_type':'NVIDIA L4',
        'formal_submission':False,'gpu_authorized':True}
    for k,v in required.items():
        if type(grant.get(k)) is not type(v) or grant[k]!=v:raise PermissionError('Grant scope mismatch: '+k)
    if grant.get('protocol_sha256')!=digest(protocol):raise PermissionError('Grant protocol identity mismatch')
    if not grant.get('human_authorization_reference'):raise PermissionError('Missing human authorization provenance')
    if datetime.fromisoformat(grant['expires_utc'])<=datetime.now(timezone.utc):raise PermissionError('Expired grant')
    # This flag must cite a separately reviewed deployment, not the subprocess adapter itself.
    if not grant.get('isolation_review_reference'):raise PermissionError('Filesystem isolation is unverified')

class Recorder:
    def __init__(self,output,mock=False):
        self.output=Path(output);self.output.mkdir(parents=True,exist_ok=True);self.mock=mock
        self.rows=[]

    @contextmanager
    def stage(self,name):
        row=dict(stage=name,start_utc=datetime.now(timezone.utc).isoformat(),end_utc=None,
            elapsed_seconds=None,status='RUNNING',error_class=None,token_usage=None,tool_calls=None,
            GPU_memory_bytes=None,evidence=[],mock=self.mock)
        start=time.monotonic();self.rows.append(row);self.flush()
        try:
            yield row;row['status']='PASS'
        except BaseException as exc:
            # Raw traceback is retained by native worker in private evidence; public wrapper stores class only.
            row.update(status='ERROR',error_class=type(exc).__name__);raise
        finally:
            row.update(end_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start)
            self.flush()

    def observed(self,name,status,evidence):
        # Native nested phases are observed after execution: do not invent their timestamps.
        self.rows.append(dict(stage=name,status=status,start_utc=None,end_utc=None,elapsed_seconds=None,
            error_class=None,token_usage=None,tool_calls=None,GPU_memory_bytes=None,evidence=evidence,mock=self.mock))
        self.flush()

    def flush(self):save(self.output/'STAGES.json',dict(experiment_id=EXPERIMENT,mock=self.mock,stages=self.rows))

def mock_run(output,backend):
    """Exercise adapter contracts with synthetic inputs, not official task tests."""
    r=Recorder(output,mock=True);patch=None;result=None
    try:
        for stage in STAGES[:-2]:
            with r.stage(stage) as event:
                reply=backend(stage,tools=TOOLS,task=agent_input(dict(instance_id='synthetic',repo='local/toy',
                    base_commit='synthetic',problem_statement='Repair the toy function.')))
                if stage=='COLLECT_PATCH':patch=reply['patch']
                if stage=='NATIVE_VERIFY':result=reply['TaskResult']
                event['token_usage']=reply.get('usage')
                event['tool_calls']=reply.get('tool_calls')
        with r.stage('EXPORT'):
            save(r.output/'MOCK_RESULT.json',dict(mock=True,TaskResult=result,patch=patch,
                algorithm_evidence=False,formal_submission=False))
    finally:
        with r.stage('CLEANUP'):backend('CLEANUP',tools=TOOLS,task=None)
    return result

def runtime_files(runtime,plan):
    # This runs before importing CUDA or initiating any HTTP request.
    for folder,expected in ((runtime['model_path'],plan['model_files']),
                            (runtime['official_wheels'],plan['official_wheels']),
                            (runtime['task_wheels'],plan['task_wheels'])):
        for name,h in expected.items():
            wanted=h if isinstance(h,str) else h['sha256']
            if digest(Path(folder)/name)!=wanted:raise ValueError('Pinned file changed: '+name)
    for name,h in plan['execution_sources'].items():
        if digest(ROOT/name)!=h:raise ValueError('Execution source changed: '+name)
    if digest(runtime['snapshot'])!=plan['task']['input_files']['snapshots/fastapi_14492.tgz']:
        raise ValueError('Snapshot changed')
    if digest(runtime['admission'])!=plan['admission_sha256']:raise ValueError('Admission evidence changed')
    # Read only selected task record; never serialize reference/gold fields to evidence or inputs.
    records=(json.loads(line) for line in Path(runtime['tasks_path']).read_text(encoding='utf-8').splitlines())
    task=next(t for t in records if t['instance_id']=='fastapi_14492')
    if task['base_commit']!=plan['task']['base_commit']:raise ValueError('Task base changed')
    if hashlib.sha256(task['problem_statement'].encode()).hexdigest()!=plan['task']['issue_sha256']:
        raise ValueError('Issue changed')
    if hashlib.sha256(task['test_patch'].encode()).hexdigest()!=plan['task']['test_patch_sha256']:
        raise ValueError('Verifier overlay changed')
    candidate(runtime['candidate_zip'],ZIPS['noegv'])
    projection=agent_input({k:task[k] for k in ('instance_id','repo','base_commit','problem_statement')})
    return projection

async def run_authorized(grant, runtime, output):
    protocol=HERE/'SMOKE_PLAN.json';authorize(grant,protocol)
    plan=json.loads(protocol.read_text(encoding='utf-8'));output=Path(output).resolve()
    if output.is_relative_to(ROOT):raise ValueError('Raw evidence must be outside the public checkout')
    output.mkdir(parents=True,exist_ok=True)
    # Exclusive durable claim: no automatic retry after any started attempt.
    claim_once(output)
    r=Recorder(output);server=None;known=[]
    projection=runtime_files(runtime,plan)
    # Approval/window/quota evidence is a runtime requirement; old snapshots are invalid.
    if runtime.get('quota_available_seconds',0)<plan['minimum_reported_quota_seconds']:
        raise ValueError('Runtime quota admission failed')
    start=runtime['session_started_monotonic']
    def remaining():return runtime['session_window_seconds']-(time.monotonic()-start)
    if remaining()<plan['conservative_seconds']:raise ValueError('Complete runtime window unavailable')
    if not runtime.get('deployment_isolation_verified'):raise ValueError('Isolation gate failed')
    import importlib.metadata
    if sys.platform!='linux' or sys.version_info[:2]!=(3,12):raise ValueError('Require frozen Linux/Python 3.12 runtime')
    for name,version in plan['official_versions'].items():
        if importlib.metadata.version(name)!=version:raise ValueError('Installed runtime version changed: '+name)
    import torch
    import psutil
    from adk_submission import VllmConfig,VllmServer,discover_adapters
    from s1.config import Config
    from harness_v2.supervisor import supervise
    from s1.experiments.e3_localize_smoke_03.idle import require_idle
    from s1.verifier_v3.audit import inspect_run
    from s1.verifier_v3.backend_logs import capture_logs
    if torch.cuda.device_count()!=4 or any('L4' not in torch.cuda.get_device_name(i) for i in range(4)):
        raise ValueError('Require exactly four L4 devices')
    if any(torch.cuda.get_device_properties(i).total_memory<22*1024**3 for i in range(4)):
        raise ValueError('GPU memory admission failed')
    candidate_dir=Path(runtime['agent_dir'])
    import zipfile
    with zipfile.ZipFile(runtime['candidate_zip']) as z:
        for n in z.namelist():
            if not (candidate_dir/n).is_file() or digest(candidate_dir/n)!=hashlib.sha256(z.read(n)).hexdigest():
                raise ValueError('Compiled directory does not match frozen ZIP')
    try:
        with r.stage('PREFLIGHT'):
            save(output/'runtime_preflight.json',dict(devices=4,model_files_verified=True,window_remaining=remaining(),quota=runtime['quota_available_seconds']))
        with r.stage('LOAD_TASK'):
            # Only this public projection can enter the prompt. Official worker receives a private task record.
            save(output/'public_input_identity.json',{k:hashlib.sha256(v.encode()).hexdigest() for k,v in projection.items()})
        with r.stage('LOAD_MODEL'):
            import os
            os.environ.update(VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',
                VLLM_ENGINE_READY_TIMEOUT_S='1200',VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS='1',
                NCCL_DEBUG='WARN',PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True',
                LOCAL_API_KEY='EMPTY',OPENAI_API_KEY='EMPTY')
            adapters=discover_adapters(str(candidate_dir))
            if adapters.adapters:raise ValueError('No adapters permitted')
            cfg=VllmConfig(model=runtime['model_path'],host='127.0.0.1',port=8000,
                tool_call_parser='gemma4',reasoning_parser='gemma4',max_model_len=32768,
                dtype='bfloat16',gpu_memory_utilization=.90,enable_auto_tool_choice=True,enable_lora=False,
                scheduler_reserve_full_isl=False,tensor_parallel_size=4,startup_timeout=1200)
            server=VllmServer(cfg,adapter_manifest=adapters);server.start()
            proc=getattr(server,'_process',None) or getattr(server,'process',None)
            if proc:known=[psutil.Process(proc.pid)]+psutil.Process(proc.pid).children(recursive=True)
        with r.stage('READY_CHECK'):
            # Transport readiness only; no extra READY text generation/inference.
            import httpx
            async with httpx.AsyncClient(trust_env=False,timeout=30) as client:
                response=await client.get(server.base_url.removesuffix('/v1')+'/health');response.raise_for_status()
                response=await client.get(server.base_url.rstrip('/')+'/models');response.raise_for_status()
                if runtime['model_path'] not in {m['id'] for m in response.json()['data']}:raise ValueError('Served model alias mismatch')
        with r.stage('INIT_AGENT'):
            from adk_submission import compile_submission
            from swegemma.config import build_submission_limits
            from swegemma.context import SwegemmaContext
            from s1.config import validate_compiled
            registry=server.create_model_registry(aliases=['gemma-4-31b-it-qat-w4a16-ct'],model_prefix='openai/',api_key='EMPTY')
            limits,constraints=build_submission_limits()
            compiled=compile_submission(candidate_dir,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
            validate_compiled(compiled,Config())
        budget=Config();directory=output/'native';directory.mkdir()
        if remaining()<budget.outer_seconds+plan['finalization_seconds']:
            raise ValueError('Insufficient window before first Agent inference')
        pins=candidate(runtime['candidate_zip'],ZIPS['noegv'])
        spec=dict(instance_id='fastapi_14492',base_commit=plan['task']['base_commit'],
            problem_sha256=plan['task']['issue_sha256'],research_config=budget.snapshot(),
            agent_dir=str(candidate_dir),candidate_hashes=pins['members'],tasks_path=runtime['tasks_path'],
            snapshots_dir=str(Path(runtime['snapshot']).parent),wheels_dir=runtime['task_wheels'],
            graph_dir=runtime['graph_dir'],embeddings_dir=runtime['embeddings_dir'],
            model_alias='gemma-4-31b-it-qat-w4a16-ct',model_path=runtime['model_path'],base_url=server.base_url,
            research_infrastructure=dict(version='s1-verifier-0.3.0',audit_modules=['fastapi'],
                environment_admission_path=runtime['admission'],environment_admission_sha256=plan['admission_sha256']))
        save(output/'worker_spec.json',spec)
        # Compilation and tools are checked by the actual native worker too.
        with r.stage('RUN_AGENT'):
            supervise([sys.executable,'-m','s1.verifier_v3.worker',str(output/'worker_spec.json'),str(directory)],
                directory,outer_seconds=budget.outer_seconds,stage_caps=budget.stage_caps,cwd=ROOT)
        raw=json.loads((directory/'official_result.json').read_text(encoding='utf-8'))
        audit=inspect_run(directory,budget.snapshot(),runtime['model_path'],baseline=json.loads(Path(runtime['admission']).read_text(encoding='utf-8')))
        save(output/'native_audit.json',audit)
        from u_re.v01.experiments.gemma_smoke_01.closure_metrics import summarize
        save(output/'closure_metrics.json',summarize(directory))
        for stage,filename in [('COLLECT_PATCH','official_result.json'),('NATIVE_VERIFY','phase2.junit.xml')]:
            r.observed(stage,'EVIDENCE_AVAILABLE' if (directory/filename).is_file() else 'NOT_OBSERVED',[str(directory/filename)])
        # Availability does not itself prove valid tools, patch quality, explicit submission or success.
        with r.stage('EXPORT'):
            save(output/'evidence_manifest.json',{str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file()})
            save(output/'SMOKE_RESULT.json',dict(resolved=raw.get('resolved'),mock=False,
                experiment_id=EXPERIMENT,GPU_inference_executed=True,cleanup_verified=None,
                stages=r.rows,token_usage=audit.get('usage'),
                algorithm_evidence=False,infrastructure_passed=audit['infrastructure_passed'],formal_submission=False))
        if not audit['infrastructure_passed']:raise RuntimeError('Native evidence or lifecycle audit failed')
        return raw
    finally:
        with r.stage('CLEANUP'):
            try:
                if server:await require_idle(server.base_url,output/'idle',seconds=60)
            finally:
                if server:
                    capture_logs(server,output/'backend_logs',phase='before_stop')
                    server.stop()
                    capture_logs(server,output/'backend_logs',phase='after_stop')
                psutil.wait_procs(known,timeout=10)
                live=[p.pid for p in known if p.is_running() and p.status() not in (psutil.STATUS_DEAD,psutil.STATUS_ZOMBIE)]
                save(output/'server_cleanup.json',dict(observed_pids=[p.pid for p in known],remaining_pids=live,verified=bool(known) and not live))
                if live:raise RuntimeError('Server process cleanup failed')
        result_path=output/'SMOKE_RESULT.json'
        if result_path.is_file():
            result=json.loads(result_path.read_text(encoding='utf-8'));result.update(stages=r.rows,cleanup_verified=bool(known) and not live)
            save(result_path,result)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
    p.add_argument('--grant',type=Path);p.add_argument('--runtime',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not a.execute:
        print(json.dumps(dict(experiment_id=EXPERIMENT,execute=False,gpu_authorized=False,
            formal_submission=False,status='OFFLINE_PLAN_ONLY')));return
    if not all((a.grant,a.runtime,a.output)):p.error('Separate grant, runtime evidence and private output directory required')
    asyncio.run(run_authorized(json.loads(a.grant.read_text(encoding='utf-8')),json.loads(a.runtime.read_text(encoding='utf-8')),a.output))

if __name__=='__main__':main()
