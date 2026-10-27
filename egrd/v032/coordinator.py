"""Single model startup, fixed A then B, native S0 workers, no extra generation."""
import asyncio
from dataclasses import asdict
import importlib.metadata as md
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import zipfile

from harness_v2.evidence import Journal
from .prepare import ROOT,HERE,WINDOW,S0_SHA,sha,write


def file_sha(path):
    import hashlib
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda:stream.read(8388608),b''):h.update(data)
    return h.hexdigest()


async def run(output,started,quota):
    import torch,psutil,httpx
    from adk_submission import VllmConfig,VllmServer,discover_adapters,ModelRegistry,compile_submission,validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    from harness_v2.supervisor import supervise
    from s1.experiments.e3_localize_smoke_03.idle import require_idle
    from s1.verifier_v3.backend_logs import capture_logs
    from .data import prepare
    from egrd.v0311.development_evaluator import evaluate as baseline_evaluate
    out=Path(output);out.mkdir(parents=True,exist_ok=True);journal=Journal(out)
    server=None;known=[];records=[];complete=False
    freeze=json.loads((HERE/'EXPERIMENT_FREEZE.json').read_bytes())
    assert freeze['owner_authorized'] and freeze['order']==['A','B'] and freeze['max_dispatches']==1 and freeze['max_sessions']==2
    assert sha((ROOT/'candidates/s0/submission.zip').read_bytes())==S0_SHA
    runtime=json.loads((HERE/'GPU_ENVIRONMENT_LOCK.json').read_bytes())
    def admit(pending,startup=False):
        elapsed=time.monotonic()-started
        need=pending*1410+900+(1200 if startup else 0)
        row=dict(elapsed=elapsed,window_remaining=WINDOW-elapsed,required_seconds=need,
                 conservative_report_quota_remaining=float(quota)-4*elapsed,quota_required=4*need)
        row['passed']=row['window_remaining']>=need and row['conservative_report_quota_remaining']>=row['quota_required']
        journal.append(dict(kind='resource_gate',**row));assert row['passed'],'Insufficient complete planned study window/quota'
    try:
        journal.stage('prepare_agent')
        assert sys.platform=='linux' and sys.version_info[:2]==(3,12)
        devices=[dict(name=torch.cuda.get_device_name(i),memory_bytes=torch.cuda.get_device_properties(i).total_memory) for i in range(torch.cuda.device_count())]
        write(out/'GPU_DEVICES.json',devices)
        assert len(devices)==4 and all(d['name']=='NVIDIA L4' and d['memory_bytes']>=22*1024**3 for d in devices)
        versions={n:md.version(n) for n in runtime['versions']}
        write(out/'GPU_RUNTIME.json',dict(versions=versions,torch_cuda=torch.version.cuda,Python=sys.version,
              driver=subprocess.check_output(['nvidia-smi','--query-gpu=driver_version','--format=csv,noheader'],text=True),
              requested_window=WINDOW,historical_serving_equivalence='UNVERIFIED'))
        assert versions==runtime['versions'] and torch.version.cuda=='12.8'
        identity=json.loads((ROOT/'egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json').read_bytes())
        for name,digest in identity['installed_official_source_hashes'].items():
            dist=md.distribution('google-adk' if name.startswith('google/') else name.split('/')[0].replace('_','-'))
            assert file_sha(dist.locate_file(name))==digest,name
        models=[p.parent for p in Path('/kaggle/input').rglob('config.json') if
                'gemma-4-31b-it-qat-w4a16-ct' in p.parts and p.parent.name=='2' and (p.parent/'model.safetensors').is_file()]
        assert len(models)==1;model=models[0]
        actual_files={p.relative_to(model).as_posix():file_sha(p) for p in model.rglob('*') if p.is_file()}
        assert actual_files==runtime['model_files'],'Frozen model/tokenizer/template bytes differ'
        config=json.loads((model/'config.json').read_bytes())
        write(out/'MODEL_IDENTITY.json',dict(model_source=freeze['model_source'],mounted_path=str(model),files=actual_files,
            quantization_config=config.get('quantization_config'),model_type=config.get('model_type'),
            generation_config=json.loads((model/'generation_config.json').read_bytes()),weights_verified=True))
        candidate=out/'candidate_gate'
        with zipfile.ZipFile(ROOT/'candidates/s0/submission.zip') as z:z.extractall(candidate)
        registry=ModelRegistry();registry.register('gemma-4-31b-it-qat-w4a16-ct',LiteLlm(
            model='openai/'+str(model),api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
        limits,constraints=build_submission_limits();validate_directory(candidate,limits=limits)
        compiled=compile_submission(candidate,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
        compiled_gen=compiled.generate_content_config.model_dump(mode='json',exclude_none=True)
        assert compiled_gen=={'max_output_tokens':16384,'thinking_config':{'thinking_budget':4096}}
        write(out/'PRELOAD_COMPILER_GATE.json',dict(passed=True,generation=compiled_gen,
            instruction_sha256=sha(compiled.instruction.encode()),tools=[t.__name__ for t in compiled.tools],model_requests=0))
        data=prepare(out/'data')
        baseline=baseline_evaluate(data['task'],Path(data['data']),out/'baseline',Path(data['snapshot']),Path(data['wheels']),Path(data['regression']))
        assert baseline['original_failing_probe_still_fails'] and baseline['positive_controls_passed']
        assert baseline['bounded_regression']['exit_code']==0 and baseline['cleanup']
        journal.append(dict(kind='baseline_and_sandbox_gate',passed=True,actual_null_device_and_Git_checked=True))
        # CPU-captured exact official initial requests; only registry model ID is
        # rebound to the actual server's mounted model path, identically in A/B.
        expected={}
        for arm in ('A','B'):
            body=json.loads((HERE/f'private/expected_{arm}.json').read_bytes())
            body['model']=str(model);expected[arm]=body
            write(out/f'expected_{arm}.json',body)
        from egrd.v0311.boundary_audit import compare
        original=json.loads((ROOT/'egrd/v031/private/original_task.json').read_bytes())['problem_statement']
        from egrd.v031.prepare import arm_input
        receipt=json.loads((ROOT/'egrd/v031/EVIDENCE_RECEIPT.json').read_bytes())
        suffix=arm_input(original,receipt,'B')[len(original):]
        pair,_=compare(json.dumps(expected['A']).encode(),json.dumps(expected['B']).encode(),original,suffix)
        assert pair['only_supplement_differs']
        admit(2,startup=True);journal.stage('load_model')
        os.environ.update(VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',VLLM_ENGINE_READY_TIMEOUT_S='1200',
            VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS='1',NCCL_DEBUG='WARN',PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True',
            LOCAL_API_KEY='EMPTY',OPENAI_API_KEY='EMPTY')
        adapters=discover_adapters(str(candidate));assert not adapters.adapters
        cfg=VllmConfig(model=str(model),**runtime['VllmConfig'])
        server=VllmServer(cfg,adapter_manifest=adapters)
        write(out/'VLLM_CONFIGURATION.json',dict(config=asdict(cfg),command=server.build_cmd(),
            explicit_request_seed=None,custom_guard=False,additional_research_safety_reserve=None,
            historical_serving_equivalence='HISTORICAL_SERVING_EQUIVALENCE_UNVERIFIED'))
        load_started=time.monotonic();server.start()
        write(out/'MODEL_LOAD_COMPLETED.json',dict(seconds=time.monotonic()-load_started,ready=True))
        known=[psutil.Process(server.process.pid)]+psutil.Process(server.process.pid).children(recursive=True)
        async with httpx.AsyncClient(trust_env=False,timeout=30) as client:
            r=await client.get(server.health_url);r.raise_for_status()
            r=await client.get(server.base_url+'/models');r.raise_for_status()
            write(out/'SERVED_MODELS.json',r.json());assert str(model) in {m['id'] for m in r.json()['data']}
            tokenized={}
            for arm,body in expected.items():
                token_request={k:body[k] for k in ('model','messages','tools','chat_template_kwargs')}
                token_request.update(add_generation_prompt=True,add_special_tokens=False)
                r=await client.post(server.base_url.removesuffix('/v1')+'/tokenize',json=token_request)
                r.raise_for_status();count=r.json();write(out/f'TOKENIZED_{arm}.json',count)
                assert count['max_model_len']==32768 and type(count['count']) is int
                assert count['count']+body['max_completion_tokens']<=32768,'Initial arm cannot fit unchanged server policy'
                tokenized[arm]=dict(input_tokens=count['count'],output_reservation=16384,model_context=32768,
                    headroom=32768-16384-count['count'])
        write(out/'INITIAL_CONTEXT_ADMISSION.json',dict(arms=tokenized,B_overhead_tokens=tokenized['B']['input_tokens']-tokenized['A']['input_tokens'],
             counter='Actual serving vLLM /tokenize with its exact mounted tokenizer/template and tools',
             generation_requests=0,additional_guard_or_safety_reserve=False))
        journal.append(dict(kind='serving_configuration_frozen',both_initial_arms_fit=True))
        await require_idle(server.base_url,out/'idle_before_A',seconds=60)
        for arm in ('A','B'):
            admit(2-len(records));journal.stage(arm+'_active')
            spec=dict(data,arm=arm,transport='REAL_GEMMA',base_url=server.base_url,model_path=str(model),
                input_sha256=freeze['inputs'][arm]['sha256'],expected_request=str(out/f'expected_{arm}.json'))
            spec_file=out/'specs'/f'{arm}.json';write(spec_file,spec)
            journal.append(dict(kind='arm_started',arm=arm));directory=out/arm
            print('REAL_GEMMA_SESSION_START',arm,flush=True)
            outcome=await asyncio.to_thread(supervise,[sys.executable,'-m','egrd.v032.worker',str(spec_file),str(directory)],directory,
                outer_seconds=1350,stage_caps=dict(prepare_agent=180,agent=330,save_patch=60,prepare_verifier=180,
                    apply_patch=60,verification=300,persist=60,cleanup=120),cwd=ROOT)
            summary=json.loads((directory/'SESSION_RESULT.json').read_bytes()) if (directory/'SESSION_RESULT.json').is_file() else None
            records.append(dict(arm=arm,worker=outcome,result=summary))
            write(out/'PAIR_RESULTS.json',dict(records=records,not_run=['B'] if arm=='A' else []))
            journal.append(dict(kind='arm_ended_and_evaluated',arm=arm,worker_complete=outcome['allow_next_run'],result_available=summary is not None))
            assert outcome['allow_next_run'] and summary is not None,'Worker integrity/cleanup incomplete; no next arm'
            await require_idle(server.base_url,out/('idle_after_'+arm),seconds=60)
            journal.append(dict(kind='arm_cleaned',arm=arm,server_idle=True))
            print('REAL_GEMMA_SESSION_END',arm,summary['submission_state'],flush=True)
        a=(out/'A/model_transport/initial_request.json').read_bytes()
        b=(out/'B/model_transport/initial_request.json').read_bytes()
        observed,diff=compare(a,b,original,suffix);assert observed['only_supplement_differs']
        write(out/'OBSERVED_BOUNDARY_COMPARISON.json',observed)
        (out/'PRIVATE_BOUNDARY_DIFF.txt').write_text(diff,encoding='utf8')
        complete=True;write(out/'EXECUTION_STATUS.json',dict(status='PAIR_COMPLETE',real_sessions=2))
    except BaseException as exc:
        write(out/'STOP.json',dict(error_type=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc(),completed_records=len(records)))
        raise
    finally:
        journal.stage('cleanup');server_cleanup=True
        if server is not None:
            try:capture_logs(server,out/'backend_logs',phase='before_stop')
            finally:
                server.stop();capture_logs(server,out/'backend_logs',phase='after_stop')
            psutil.wait_procs(known,timeout=10)
            for process in known:
                try:
                    if process.is_running() and process.status()!=psutil.STATUS_ZOMBIE:process.kill()
                except psutil.NoSuchProcess:pass
            psutil.wait_procs(known,timeout=5)
            live=[]
            for process in known:
                try:
                    if process.is_running() and process.status()!=psutil.STATUS_ZOMBIE:live.append(process.pid)
                except psutil.NoSuchProcess:pass
            server_cleanup=not live
            write(out/'MODEL_SERVER_CLEANUP.json',dict(observed_pids=[p.pid for p in known],live=live,complete=server_cleanup))
        write(out/'PAIR_RESULTS.json',dict(records=records,not_run=['A','B'][len(records):]))
        write(out/'COST_RAW.json',dict(first_cell_elapsed_seconds=time.monotonic()-started,real_sessions_started=len(records),
            GPU_billed_seconds=None,scope='Response usage and per-arm runtime in private HTTP/Agent journals'))
        if complete and server_cleanup:write(out/'worker_done.json',dict(cleanup_complete=True))


if __name__=='__main__':asyncio.run(run(sys.argv[1],float(sys.argv[2]),sys.argv[3]))
