"""Authorized one-Notebook, four-session ABBA coordinator. No Kaggle write API."""
import asyncio
from dataclasses import asdict
import hashlib
import importlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import shlex
import sys
import time
import traceback

from harness_v2.evidence import Journal,atomic_json,read_events

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'integrated_cpu_01'
ROOT=HERE.parents[4]

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8388608),b''):h.update(chunk)
    return h.hexdigest()


async def native_baseline(data,task,frozen,output):
    """Original trusted native evaluator; no patch and no model."""
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from s1.verifier_v3.environment import SubprocessManager,research_environment
    from s1.verifier_v3.audit import audit_verifier
    from u_re.v01.experiments.fastapi_pilot_01.screen import source_hashes,provenance
    output.mkdir(parents=True)
    # Observe source identity on the actual trusted workspace at pytest boundaries.
    Parent=SubprocessManager
    class SubprocessManager(Parent):
        def exec(self,sid,command,*,timeout=None):
            if ' -m pytest ' in command:atomic_json(output/'before.json',source_hashes(self.sandboxes[sid]['workspace']))
            return super().exec(sid,command,timeout=timeout)
        def stop(self,sid):
            if sid in self.sandboxes and sid in self.junit_paths:
                w=self.sandboxes[sid]['workspace'];atomic_json(output/'after.json',source_hashes(w))
                atomic_json(output/'provenance.json',provenance(output,'fastapi',w))
            return super().stop(sid)
    manager=SubprocessManager(journal=Journal(output),base_dir=output/'roots',audit_modules=['fastapi'],task_wheels=data/'wheels')
    manager.agent_id='TRUSTED_BASELINE_NO_AGENT'
    cfg=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=output/'unused',
        submission_dir=ROOT/'u_re/v01/candidate_noegv',models=ModelRegistry(),sandbox='subprocess',wheels_dir=data/'wheels',
        verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
    snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots',task.instance_id,task.repo)
    try:
        with research_environment(audit_modules=['fastapi'],task_wheels=data/'wheels'):
            result=await verify_task(manager,cfg,task,snapshot,base_snapshot_path=base,patch_path=overlay,agent_patch='',start_time=time.perf_counter())
        atomic_json(output/'official_result.json',result.model_dump(mode='json',exclude={'trace'}))
    finally:manager.cleanup_all();atomic_json(output/'cleanup.json',dict(complete=not manager.sandboxes))
    audit=audit_verifier(output);atomic_json(output/'audit.json',audit)
    assert audit['category']=='assertion_failure' and not audit['infrastructure_stop']
    assert result.resolved is False and result.test_exit_code==1 and audit['counts']==frozen['native_baseline_counts']
    assert (output/'before.json').read_bytes()==(output/'after.json').read_bytes()
    assert json.loads((output/'provenance.json').read_bytes())['verified']
    capture=json.loads((output/'phase2_junit_capture.json').read_bytes())
    return dict(eligible=True,production_source_hashes=capture['production_source_hashes'])


async def run(output,session_started):
    import torch,psutil,httpx
    from adk_submission import VllmConfig,VllmServer,discover_adapters
    from s1.config import Config
    from s1.task_identity import find_data,identify
    from swegemma.models import load_tasks
    from harness_v2.supervisor import supervise
    from s1.experiments.e3_localize_smoke_03.idle import require_idle
    from s1.verifier_v3.backend_logs import capture_logs
    from ..integrated_cpu_01.agent_phase import SubprocessManager
    from .ISOLATION_CANARY import CANARY
    output=Path(output);output.mkdir(parents=True,exist_ok=False);j=Journal(output)
    lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    admitted=json.loads((HERE/'ADMISSION_RECONCILIATION.json').read_bytes())
    grant=json.loads((HERE/'GPU_AUTHORIZATION.json').read_bytes())
    assert grant['GPU_authorized'] and grant['max_SaveKernel_dispatches']==1 and grant['max_Agent_runs']==4
    assert grant['order']==lock['order'] and grant['Agent_seconds']==300 and grant['platform_window_seconds']==10000
    assert admitted['status']=='EVIDENCE_RECONCILED_TWO_TASKS_ADMITTED'
    assert [r['instance_id'] for r in admitted['tasks']]==['fastapi_9425','fastapi_14786']
    server=None;known=[];records=[];stop=None;window=10000
    def remaining():return window-(time.monotonic()-session_started)
    def admission(pending,startup=False):
        need=pending*1410+900+(1200 if startup else 0)
        # Assume worst-case2x wall-time reported consumption,not a billing claim.
        quota=float(grant['quota_at_dispatch_report_seconds'])-2*(time.monotonic()-session_started)
        row=dict(pending=pending,remaining_window=remaining(),required_seconds=need,remaining_quota_conservative=quota,
            pass_gate=remaining()>=need and quota>=need*2)
        j.append(dict(kind='remaining_resource_admission',**row));assert row['pass_gate'],'Insufficient complete remaining experiment resources'
    try:
        j.stage('prepare_agent')
        assert sys.platform=='linux' and sys.version_info[:2]==(3,12)
        devices=[dict(name=torch.cuda.get_device_name(i),memory_bytes=torch.cuda.get_device_properties(i).total_memory) for i in range(torch.cuda.device_count())]
        atomic_json(output/'GPU_DEVICES.json',devices)
        assert len(devices)==4 and all('L4' in d['name'] and d['memory_bytes']>=22*1024**3 for d in devices)
        actual_versions={n:importlib.metadata.version(n) for n in ('swegemma','adk-submission','google-adk','google-genai','litellm','pytest','vllm','torch')}
        expected=json.loads((ROOT/'u_re/v01/experiments/gemma_smoke_01/MODEL_RUNTIME_CONFIG.json').read_bytes())['historical_versions']
        atomic_json(output/'GPU_RUNTIME.json',dict(versions=actual_versions,torch_cuda=torch.version.cuda,driver=os.popen('nvidia-smi --query-gpu=driver_version --format=csv,noheader').read(),
            requested_window=window,window_basis='Platform accepted SaveKernel sessionTimeoutSeconds=10000; elapsed clock begins in first Notebook cell; SDK exposes no independent effective-window field',session_started=session_started))
        assert all(actual_versions[n]==v for n,v in expected.items()) and torch.version.cuda=='12.8'
        for n,h in lock['source_pins'].items():assert digest(PRIOR/n)==h,('CPU accepted source drift',n)
        for n,h in lock['native_verifier_source_sha256'].items():assert digest(inspect.getfile(importlib.import_module(n)))==h
        data=find_data();frozen={t['instance_id']:t for t in lock['tasks']};tasks={t.instance_id:t for t in load_tasks(data/'tasks.jsonl')}
        actual=identify(data,list(frozen))
        for ident,f in frozen.items():
            for key in ('repo','base_commit','issue_sha256','task_record_sha256','test_patch_sha256','input_files'):assert actual[ident][key]==f[key]
        atomic_json(output/'TASK_IDENTITIES.json',actual)
        model_paths=[p.parent for p in Path('/kaggle/input').rglob('config.json') if 'gemma-4-31b-it-qat-w4a16-ct' in p.parts and (p.parent/'model.safetensors').is_file()]
        assert len(model_paths)==1 and model_paths[0].name=='2';model_path=model_paths[0]
        model_files={p.relative_to(model_path).as_posix():digest(p) for p in sorted(model_path.rglob('*')) if p.is_file()}
        atomic_json(output/'MODEL_FILES.json',model_files);assert model_files==lock['model']['files']
        # Synthetic boundary recheck before any model generation;not CPU suite repetition.
        probe=output/'isolation';probe.mkdir();research=probe/'owned_research';research.mkdir()
        targets=[]
        for name in ('research','evaluator','other_arm'):
            p=research/(name+'.canary');p.write_text('OWNED_SYNTHETIC_'+name);targets.append(str(p))
        before={p:digest(p) for p in targets};fd=os.open(targets[0],os.O_RDONLY);os.set_inheritable(fd,True)
        manager=SubprocessManager(journal=Journal(probe),base_dir=probe/'roots',task_wheels=data/'wheels')
        try:
            sid=manager.start();code=CANARY.replace('TARGETS',repr(targets))
            result=manager.exec(sid,'python3 -c '+shlex.quote(code),timeout=120)
            atomic_json(probe/'result.json',dict(exit_code=result.exit_code,stdout=result.stdout,stderr=result.stderr))
            assert result.exit_code==0 and 'INTEGRATED_CANARY_AND_DEPENDENCIES_OK' in result.stdout
        finally:os.close(fd);manager.cleanup_all()
        assert before=={p:digest(p) for p in targets}
        atomic_json(probe/'cleanup.json',dict(complete=not manager.sandboxes))
        for ident,f in frozen.items():
            baseline=await native_baseline(data,tasks[ident],f,output/'baselines'/ident)
            atomic_json(output/'baselines'/ident/'BASELINE_CAPTURE.json',baseline)
        admission(4,startup=True)
        j.stage('load_model')
        os.environ.update(VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',VLLM_ENGINE_READY_TIMEOUT_S='1200',
            VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS='1',NCCL_DEBUG='WARN',PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True',LOCAL_API_KEY='EMPTY',OPENAI_API_KEY='EMPTY')
        adapters=discover_adapters(str(ROOT/'u_re/v01/candidate_noegv'));assert not adapters.adapters
        cfg=VllmConfig(model=str(model_path),host='127.0.0.1',port=8000,tool_call_parser='gemma4',reasoning_parser='gemma4',
            max_model_len=32768,dtype='bfloat16',gpu_memory_utilization=.90,enable_auto_tool_choice=True,enable_lora=False,
            scheduler_reserve_full_isl=False,tensor_parallel_size=4,startup_timeout=1200)
        atomic_json(output/'VLLM_CONFIG.json',asdict(cfg));server=VllmServer(cfg,adapter_manifest=adapters);server.start()
        p=getattr(server,'_process',None) or getattr(server,'process',None)
        if p:known=[psutil.Process(p.pid)]+psutil.Process(p.pid).children(recursive=True)
        async with httpx.AsyncClient(trust_env=False,timeout=30) as client:
            r=await client.get(server.base_url.removesuffix('/v1')+'/health');r.raise_for_status()
            r=await client.get(server.base_url+'/models');r.raise_for_status();atomic_json(output/'SERVED_MODELS.json',r.json())
            assert str(model_path) in {m['id'] for m in r.json()['data']}
        # No READY generation:only normal model requests in the four task sessions.
        await require_idle(server.base_url,output/'idle_before',seconds=60)
        for index,row in enumerate(lock['order']):
            admission(4-index)
            ident=row['instance_id'];arm=row['arm'];directory=output/'runs'/f"{row['run']:02d}-{ident}-{arm}"
            agent=ROOT/'u_re/v01/candidate_noegv' if arm=='A' else ROOT/'u_re/v01/experiments/action_priority_01/candidate_action_v01'
            spec=dict(instance_id=ident,arm=arm,agent_dir=str(agent),data=str(data),model_path=str(model_path),base_url=server.base_url,
                baseline_capture=str(output/'baselines'/ident/'BASELINE_CAPTURE.json'))
            file=output/'specs'/f"{row['run']:02d}.json";atomic_json(file,spec)
            print('REAL_GEMMA_RUN_START',row,flush=True)
            started=time.monotonic()
            outcome=supervise([sys.executable,'-m',__package__+'.worker',str(file),str(directory)],directory,
                outer_seconds=Config().outer_seconds,stage_caps=Config().stage_caps,cwd=ROOT)
            await require_idle(server.base_url,output/('idle_after_'+str(row['run'])),seconds=60)
            summary=json.loads((directory/'native_summary.json').read_bytes()) if (directory/'native_summary.json').exists() else None
            records.append(dict(**row,worker=outcome,native=summary,worker_seconds=time.monotonic()-started,status='COMPLETE' if outcome['allow_next_run'] else 'UNKNOWN'))
            atomic_json(output/'ABBA_RESULTS.json',dict(records=records,not_run=lock['order'][index+1:]))
            print('REAL_GEMMA_RUN_END',row,summary,flush=True)
            assert outcome['allow_next_run'],'Worker integrity/cleanup failed;no successor'
        atomic_json(output/'EXECUTION_STATUS.json',dict(status='REAL_GEMMA_ABBA_COMPLETE',runs=4))
    except BaseException as exc:
        stop=str(exc);atomic_json(output/'STOP.json',dict(error_type=type(exc).__name__,reason=stop,traceback=traceback.format_exc(),completed=len(records)))
        raise
    finally:
        idle_error=None
        if server:
            try:await require_idle(server.base_url,output/'idle_final',seconds=60)
            except BaseException as exc:idle_error=type(exc).__name__
            finally:
                capture_logs(server,output/'backend_logs',phase='before_stop');server.stop();capture_logs(server,output/'backend_logs',phase='after_stop')
        psutil.wait_procs(known,timeout=10)
        live=[]
        for p in known:
            try:
                if p.is_running() and p.status() not in (psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD):live.append(p.pid)
            except psutil.NoSuchProcess:pass
        atomic_json(output/'SERVER_CLEANUP.json',dict(observed_pids=[p.pid for p in known],remaining=live,confirmed=bool(known) and not live,idle_error=idle_error))
        atomic_json(output/'ABBA_RESULTS.json',dict(records=records,not_run=lock['order'][len(records):],stop=stop))
        actual_requests=sum(sum(e.get('kind')=='http_request' for e in read_events(d/'agent/http_wire.jsonl')) for d in (output/'runs').glob('*')) if (output/'runs').exists() else 0
        atomic_json(output/'GPU_COST.json',dict(session_elapsed_seconds=time.monotonic()-session_started,
            actual_Gemma_requests=actual_requests,request_count_source='Actual http_request records',GPU_billed_seconds=None))
