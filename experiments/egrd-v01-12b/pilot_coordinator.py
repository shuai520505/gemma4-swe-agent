"""Small engineering pilot using existing Server/supervisor/worker contracts."""
import asyncio,hashlib,importlib.metadata as md,json,os,sys,time
from pathlib import Path
from dataclasses import asdict
import psutil,torch
from adk_submission import VllmConfig,VllmServer,discover_adapters
from harness_v2.supervisor import supervise
from s1.experiments.e3_localize_smoke_03.idle import require_idle
from s1.verifier_v3.backend_logs import capture_logs
from r2a_runtime import HERE,write
from r2a_coordinator import admission as legacy
from stop_policy import admission
D=Path(__file__).resolve().parent
def file_sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
async def run(out,started):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert not (out/'PILOT_RESULTS.json').exists()
    plan=json.loads((D/'TASK_IDENTITY_MANIFEST.json').read_bytes());models=json.loads((D/'MODEL_CONFIGURATIONS.json').read_bytes())
    issues={r['instance_id']:r for r in json.loads((HERE/'ISSUES.agent.json').read_bytes())}
    version_rows=json.loads((HERE/'TASK_IDENTITY_LOCK.json').read_bytes())['rows']
    records=[];not_run=list(plan['sessions']);server=None;known=[];stop=None
    devices=[dict(name=torch.cuda.get_device_name(i),memory=torch.cuda.get_device_properties(i).total_memory) for i in range(torch.cuda.device_count())]
    assert len(devices)==4 and all(d['name']=='NVIDIA L4' for d in devices)
    write(out/'ACTUAL_GPU.json',dict(devices=devices,versions={n:md.version(n) for n in ['torch','vllm','swegemma','adk-submission','google-adk']},CUDA=torch.version.cuda))
    os.environ.update(VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',VLLM_ENGINE_READY_TIMEOUT_S='1200',VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS='1',NCCL_DEBUG='WARN',PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True',LOCAL_API_KEY='EMPTY',OPENAI_API_KEY='EMPTY')
    try:
        for size in ['12b','31b']:
            if size=='31b':
                b=[r['result'] for r in records if r['candidate']=='B']
                if len(b)!=3 or not all(r.get('EGRD_state_recorded') for r in b):
                    stop='PILOT_WORKFLOW_NOT_ESTABLISHED_NO_31B_EXTENSION';break
                states=[json.loads((out/'sessions'/f"{r['index']:02d}_{r['candidate']}_{r['task']}"/'EGRD_STATE.json').read_bytes()) for r in records if r['candidate']=='B']
                if not any(s.get('cause') and s.get('patch_intent') and any(e.get('type')=='TEST_RESULT' for e in s.get('evidence',[])) for s in states):
                    stop='NO_COMPLETE_EGRD_WORKFLOW_NO_31B_EXTENSION';break
            remaining=[r for r in not_run if r['model']==size]
            assert 18000-(time.monotonic()-started)>=1200*len(remaining)+2100,'Insufficient complete batch reserve'
            cfg=models[size];model=Path('/kaggle/input/models/google/gemma-4/other')/cfg['alias']/'2'
            assert model.is_dir() and (model/'model.safetensors').is_file()
            batch=out/size;batch.mkdir()
            observed={p.relative_to(model).as_posix():file_sha(p) for p in model.rglob('*') if p.is_file()}
            write(batch/'MODEL_IDENTITY.json',dict(alias=cfg['alias'],asset=cfg['mount'],files=observed,expected_files=cfg['expected_files']))
            assert observed==cfg['expected_files'],'Frozen model file identity mismatch'
            empty=batch/'no-adapters';empty.mkdir()
            vcfg=VllmConfig(model=str(model),host='127.0.0.1',port=8000,max_model_len=32768,dtype='bfloat16',gpu_memory_utilization=.9,tensor_parallel_size=4,enable_auto_tool_choice=True,tool_call_parser='gemma4',reasoning_parser='gemma4',scheduler_reserve_full_isl=False,enable_lora=False,startup_timeout=1200,extra_args=tuple(cfg['extra_args'])+('--no-enable-prefix-caching',))
            server=VllmServer(vcfg,adapter_manifest=discover_adapters(str(empty)))
            write(batch/'SERVER_CONFIG.json',dict(config=asdict(vcfg),command=server.build_cmd()))
            begin=time.monotonic();server.start();write(batch/'MODEL_LOAD.json',dict(seconds=time.monotonic()-begin))
            known=[psutil.Process(server.process.pid)]+psutil.Process(server.process.pid).children(recursive=True)
            for item in remaining:
                await require_idle(server.base_url,batch/('idle-before-'+str(item['index'])),seconds=60)
                ident=item['task'];identity=next(r for r in plan['tasks'] if r['instance_id']==ident)
                snapshot=HERE/'assets/snapshots'/(ident+'.tgz');assert file_sha(snapshot)==identity['SDK_snapshot_sha256']
                assert hashlib.sha256(issues[ident]['problem_statement'].encode()).hexdigest()==identity['issue_sha256']
                binding=dict(issue=issues[ident],snapshot=str(snapshot),wheels=str(HERE/'assets/wheels'),version=next(r['version'] for r in version_rows if r['instance_id']==ident))
                spec=dict(binding=binding,candidate=item['candidate'],model_path=str(model),model_alias=cfg['alias'],real_Gemma=True,authorized_GPU_pilot=True)
                specfile=out/'specs'/f"{item['index']}.json";write(specfile,spec)
                directory=out/'sessions'/f"{item['index']:02d}_{item['candidate']}_{ident}"
                outcome=await asyncio.to_thread(supervise,[sys.executable,'-m','pilot_worker',str(specfile),str(directory)],directory,outer_seconds=1200,stage_caps=dict(prepare_agent=240,agent=345,save_patch=60,verification=600,persist=60,cleanup=120),cwd=D)
                result=json.loads((directory/'SESSION_RESULT.json').read_bytes()) if (directory/'SESSION_RESULT.json').exists() else None
                records.append(dict(item,result=result,worker=outcome));not_run=[r for r in not_run if r['index']!=item['index']]
                write(out/'PILOT_RESULTS.json',dict(records=records,not_run=not_run,semantic_review='PENDING',complete=False))
                assert result is not None and admission(result,outcome,legacy)=='CONTINUE','Infrastructure/trust stop'
                await require_idle(server.base_url,batch/('idle-after-'+str(item['index'])),seconds=60)
            capture_logs(server,batch/'backend_logs',phase='before-stop');server.stop();capture_logs(server,batch/'backend_logs',phase='after-stop');psutil.wait_procs(known,timeout=10)
            live=[]
            for p in known:
                try:
                    if p.is_running() and p.status()!=psutil.STATUS_ZOMBIE:live.append(p.pid)
                except psutil.NoSuchProcess:pass
            write(batch/'SERVER_CLEANUP.json',dict(complete=not live,live=live));assert not live
            server=None;known=[]
    except BaseException as exc:
        import traceback
        stop=dict(type=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc());write(out/'STOP.json',stop)
    finally:
        if server is not None:
            capture_logs(server,out/'backend_failure_logs',phase='before-stop');server.stop();capture_logs(server,out/'backend_failure_logs',phase='after-stop');psutil.wait_procs(known,timeout=10)
        live=[]
        for p in known:
            try:
                if p.is_running() and p.status()!=psutil.STATUS_ZOMBIE:live.append(p.pid)
            except psutil.NoSuchProcess:pass
        write(out/'FINAL_CLEANUP.json',dict(complete=not live,live=live))
        write(out/'PILOT_RESULTS.json',dict(records=records,not_run=not_run,stop=stop,complete=not not_run and not live,semantic_review='REQUIRED_SEPARATELY',pilot_only=True,elapsed_seconds=time.monotonic()-started,official_hidden_resolved=None))
if __name__=='__main__':asyncio.run(run(sys.argv[1],float(sys.argv[2])))
