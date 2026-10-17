"""Registered serial public-task experiment; never launch a successor after gate failure."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import shutil
import sys
import time
import urllib.request
from harness_v2.evidence import atomic_json,bundle
from harness_v2.supervisor import supervise
from . import MODEL
from .config import Config,validate_compiled
from .util import sha_file,sha
from .task_identity import identify,find_data
from .audit import inspect_run


def require_cpu(source):
    source=Path(source)
    gate=json.loads((source/'s1/cpu_gate.json').read_text())
    registration=json.loads((source/'s1/registration.json').read_text())
    assert gate['passed'] and gate['failures']==gate['errors']==gate['skipped']==0
    assert gate['legacy_count']==38 and gate['real_official_Runner']
    assert gate['source_hashes']==registration['source_hashes']
    for n,digest in gate['source_hashes'].items(): assert sha_file(source/n)==digest,n
    return gate


async def run(source,output,batch):
    import torch
    import psutil
    from adk_submission import VllmConfig,VllmServer,compile_submission,discover_adapters
    from swegemma.context import SwegemmaContext
    from swegemma.config import build_submission_limits
    from google.adk.models.lite_llm import LiteLLMClient
    from harness_v2.context_budget import VllmCounter,RequestGuard,ContextBudgetExceeded
    source,output=Path(source),Path(output)
    require_cpu(source)
    plan=json.loads((source/'s1/gpu_protocol.json').read_text())
    if batch!='smoke':
        prior=json.loads((source/'s1/previous_batch_gate.json').read_text())
        assert prior['infrastructure_passed'] and prior['protocol_sha256']==sha_file(source/'s1/gpu_protocol.json')
    data=find_data()
    assert identify(data,plan['task_inputs'])==plan['task_inputs'],'Task/snapshot bytes drift'
    candidates=plan['candidates']
    paths=[p.parent for p in Path('/kaggle/input').rglob('config.json') if MODEL in p.parts and any(p.parent.glob('*.safetensors'))]
    assert len(paths)==1
    model_path=paths[0];assert model_path.name=='2'
    assert torch.cuda.device_count()==4 and all('L4' in torch.cuda.get_device_name(i) for i in range(4))
    identity={p.relative_to(model_path).as_posix():sha_file(p) for p in sorted(model_path.rglob('*')) if p.is_file()}
    atomic_json(output/'model_identity.json',dict(files=identity,manifest_sha256=sha(json.dumps(identity,sort_keys=True).encode())))
    assert identity==plan['model_files'],'Model bytes drift'
    limits,constraints=build_submission_limits()
    adapters=discover_adapters(str(source/'s1/candidates/control'));assert not adapters.adapters
    cfg=VllmConfig(model=str(model_path),host='127.0.0.1',port=8000,tool_call_parser='gemma4',
        reasoning_parser='gemma4',max_model_len=32768,dtype='bfloat16',gpu_memory_utilization=.90,
        enable_auto_tool_choice=True,enable_lora=False,scheduler_reserve_full_isl=False,tensor_parallel_size=4,startup_timeout=1200)
    atomic_json(output/'vllm_config.json',asdict(cfg))
    server=VllmServer(cfg,adapter_manifest=adapters)
    records=[];stop=None;started=time.monotonic();known=[]
    try:
        server.start()
        # Observe the actual server tree so a stop-return alone is not called cleanup.
        proc=getattr(server,'_process',None) or getattr(server,'process',None)
        if proc is not None:
            try: known=[psutil.Process(proc.pid)]+psutil.Process(proc.pid).children(recursive=True)
            except psutil.NoSuchProcess:pass
        key=os.environ.get('LOCAL_API_KEY','EMPTY')
        with urllib.request.urlopen(urllib.request.Request(server.base_url+'/models',headers={'Authorization':'Bearer '+key}),timeout=30) as response: served=json.load(response)
        atomic_json(output/'served_models.json',served)
        assert any(x['id']==str(model_path) for x in served['data'])
        registry=server.create_model_registry(aliases=[MODEL],model_prefix='openai/',api_key=key)
        for arm in ('control','e1_output8192'):
            agent=compile_submission(source/'s1/candidates'/arm,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
            validate_compiled(agent,Config(**candidates[arm]['config']))
        admissions=[]
        guard=RequestGuard(VllmCounter(server.base_url,key),LiteLLMClient().acompletion,core_issue='Reply READY.',emit=admissions.append)
        response=await guard.acompletion(model='openai/'+str(model_path),api_base=server.base_url,api_key=key,
            messages=[dict(role='user',content='Reply READY.')],max_completion_tokens=16,
            extra_body={'chat_template_kwargs':{'enable_thinking':False}})
        assert response.model==str(model_path) and response.usage.prompt_tokens==admissions[-1]['input_tokens']
        async def forbidden(**kwargs):raise AssertionError('Oversize request sent')
        over=[]
        guard=RequestGuard(VllmCounter(server.base_url,key),forbidden,core_issue='Boundary',emit=over.append)
        try:await guard.acompletion(model='openai/'+str(model_path),messages=[dict(role='user',content=' token'*30000)],max_completion_tokens=16384)
        except ContextBudgetExceeded:pass
        else:raise AssertionError('Boundary not enforced')
        atomic_json(output/'gpu_probe.json',dict(response=response.model_dump(),admission=admissions,oversize=over))
        for row in plan['batches'][batch]:
            if stop:break
            arm=row['arm'];config=Config(**candidates[arm]['config'])
            if time.monotonic()-started+config.outer_seconds+900>plan['session_seconds']:
                stop='insufficient_complete_task_slot';break
            task=plan['task_inputs'][row['instance_id']]
            directory=output/'runs'/f"{row['index']:02d}-{row['instance_id']}-{arm}"
            spec=dict(instance_id=row['instance_id'],base_commit=task['base_commit'],problem_sha256=task['issue_sha256'],
                research_config=config.snapshot(),agent_dir=str(source/'s1/candidates'/arm),candidate_hashes=candidates[arm]['members'],
                tasks_path=str(data/'tasks.jsonl'),snapshots_dir=str(data/'snapshots'),wheels_dir=str(data/'wheels'),
                graph_dir=str(data/'graphs'),embeddings_dir=str(data/'embeddings'),model_alias=MODEL,model_path=str(model_path),base_url=server.base_url)
            spec_path=output/'specs'/f"{row['index']:02d}.json";atomic_json(spec_path,spec)
            print('START',row,flush=True)
            result=supervise([sys.executable,'-m','s1.wire',str(spec_path),str(directory)],directory,
                outer_seconds=config.outer_seconds,stage_caps=config.stage_caps,cwd=source)
            audit=inspect_run(directory,config.snapshot(),str(model_path))
            atomic_json(directory/'research_audit.json',audit);bundle(directory)
            records.append(dict(**row,result=result,audit=audit))
            atomic_json(output/'records.json',records)
            print('RESULT',row,audit['outcome'],audit['reasons'],flush=True)
            if not audit['infrastructure_passed']:stop='infrastructure/evidence gate failed'
    except BaseException as exc:
        import traceback
        stop=f'{type(exc).__name__}: {exc}'
        atomic_json(output/'session_exception.json',dict(error=stop,traceback=traceback.format_exc()))
        raise
    finally:
        log=getattr(server,'log_path',None)
        if log and Path(log).is_file():shutil.copyfile(log,output/'vllm.log')
        server.stop()
        psutil.wait_procs(known,timeout=10)
        forced=[]
        for p in known:
            try:
                if p.is_running() and p.status() not in (psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD):
                    p.kill();forced.append(p.pid)
            except psutil.NoSuchProcess:pass
        psutil.wait_procs(known,timeout=5)
        live=[]
        for p in known:
            try:
                if p.is_running() and p.status() not in (psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD):live.append(p.pid)
            except psutil.NoSuchProcess:pass
        stopped=bool(known) and not live
        atomic_json(output/'server_cleanup.json',dict(observed_pids=[p.pid for p in known],forced_cleanup_pids=forced,remaining_pids=live,verified=stopped))
        if not stopped:stop=stop or 'server process tree cleanup unconfirmed'
        completed={r['index'] for r in records}
        pending=[dict(**r,status='not_run',reason=stop or 'unlaunched') for r in plan['batches'][batch] if r['index'] not in completed]
        atomic_json(output/'not_run.json',pending)
        atomic_json(output/'batch_gate.json',dict(experiment_id=plan['experiment_id'],batch=batch,
            infrastructure_passed=not stop and not pending and all(r['audit']['infrastructure_passed'] for r in records),
            stop_reason=stop,records=records,not_run=pending,protocol_sha256=sha_file(source/'s1/gpu_protocol.json')))
