"""Draft S2 batch coordinator. Authorization fails closed before server startup."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from harness_v2.evidence import atomic_json,bundle,Journal,read_events
from harness_v2.supervisor import supervise
from s1 import MODEL
from s1.config import Config
from s2.egv_agenttool_v01.validation import validate_candidate
from s1.task_identity import identify,find_data
from s1.util import sha_file,sha
from s1.window import SessionWindow
from s1.verifier_v3 import VERSION
from s1.verifier_v3.audit import inspect_run
from s1.experiments.e1_outputcap_smoke_02.startup import observe_probe
EXPERIMENT_ID='S2-EGV-AGENTTOOL-MULTITASK-01'
from s1.experiments.e3_localize_smoke_03.idle import require_idle
from s1.verifier_v3.backend_logs import capture_logs


def require_cpu(source):
    source=Path(source)
    gate=json.loads((source/'s2/egv_agenttool_v01/CPU_FEASIBILITY.json').read_text())
    assert gate['passed'] and gate['original115_passed']
    candidate=source/'s2/egv_agenttool_v01/submission.zip'
    assert sha_file(candidate)==gate['candidate_zip_sha256']
    for n,h in gate['tested_runtime_hashes'].items():assert sha_file(source/n)==h,n
    return gate


def require_authorization(plan, authorization, batch):
    assert plan['status']=='AUTHORIZED_FROZEN', 'Draft is not executable authorization'
    assert authorization['authorized'] is True and authorization['batch']==batch
    assert authorization['experiment_id']==EXPERIMENT_ID
    assert authorization['protocol_sha256']==sha((json.dumps(plan,indent=2)+'\n').encode())
    if batch==2:
        prior=authorization['prior_batch']
        assert prior['infrastructure_passed'] and prior['complete_pairs']==4
        assert prior['protocol_sha256']==authorization['protocol_sha256']
        assert prior['raw_sha256'], 'Cross-batch evidence receipt required'


def audit_all_requests(directory,config,model):
    # The frozen legacy audit pairs replies by index; also validate every request,
    # including a final request that was cancelled without a reply.
    for row in read_events(Path(directory)/'http_wire.jsonl'):
        if row['kind']!='http_request':continue
        body=row['body']
        assert body['model']==model and body.get('seed')==17
        assert body.get('max_completion_tokens',body.get('max_tokens'))==16384
        assert body.get('thinking_token_budget')==4096
        assert body.get('chat_template_kwargs',{}).get('enable_thinking') is True
        assert all(body.get(key) is None for key in ('temperature','top_p','top_k'))


async def run(source,output,*,session_started,batch,authorization):
    import torch
    import psutil
    from adk_submission import VllmConfig,VllmServer,compile_submission,discover_adapters
    from swegemma.context import SwegemmaContext
    from swegemma.config import build_submission_limits
    source,output=Path(source),Path(output);require_cpu(source)
    plan=json.loads((source/'s2/gpu_protocol.json').read_text())
    require_authorization(plan,authorization,batch)
    runs=[r for r in plan['runs'] if r['batch']==batch]
    assert len(runs)==8
    assert plan['experiment_id']==EXPERIMENT_ID
    assert len(plan['selected'])==8 and len(plan['runs'])==16
    data=find_data();assert identify(data,plan['task_inputs'])==plan['task_inputs']
    from .environments import check
    for selected in plan['selected']:
        if selected['instance_id'] not in {r['instance_id'] for r in runs}:continue
        admission=await check(selected,output/'gpu_host_environment'/selected['instance_id'])
        assert admission['eligible'],'Fresh native baseline blocked; no task substitution'
    paths=[p.parent for p in Path('/kaggle/input').rglob('config.json') if MODEL in p.parts and any(p.parent.glob('*.safetensors'))]
    assert len(paths)==1;model_path=paths[0];assert model_path.name=='2'
    assert torch.cuda.device_count()==4 and all('L4' in torch.cuda.get_device_name(i) for i in range(4))
    identity={p.relative_to(model_path).as_posix():sha_file(p) for p in sorted(model_path.rglob('*')) if p.is_file()}
    atomic_json(output/'model_identity.json',dict(files=identity,manifest_sha256=sha(json.dumps(identity,sort_keys=True).encode())))
    assert identity==plan['model_files'],'Model bytes drift'
    candidates=plan['candidates'];limits,constraints=build_submission_limits()
    adapters=discover_adapters(str(source/'s1/egv_v01/candidate'));assert not adapters.adapters
    cfg=VllmConfig(model=str(model_path),host='127.0.0.1',port=8000,tool_call_parser='gemma4',
        reasoning_parser='gemma4',max_model_len=32768,dtype='bfloat16',gpu_memory_utilization=.90,
        enable_auto_tool_choice=True,enable_lora=False,scheduler_reserve_full_isl=False,tensor_parallel_size=4,startup_timeout=1200)
    atomic_json(output/'vllm_config.json',asdict(cfg));server=VllmServer(cfg,adapter_manifest=adapters)
    records=[];stop=None;known=[];journal=Journal(output)
    window=SessionWindow(session_started,limit_seconds=14400)
    try:
        admission=window.admission(1200+len(runs)*(1350+60));journal.append(dict(kind='startup_admission',**admission))
        assert admission['allow'],'Global time insufficient'
        server.start()
        proc=getattr(server,'_process',None) or getattr(server,'process',None)
        if proc:
            try:known=[psutil.Process(proc.pid)]+psutil.Process(proc.pid).children(recursive=True)
            except psutil.NoSuchProcess:pass
        key=os.environ.get('LOCAL_API_KEY','EMPTY')
        registry=server.create_model_registry(aliases=[MODEL],model_prefix='openai/',api_key=key)
        for arm in ('A','B'):
            agent=compile_submission(source/candidates[arm]['directory'],SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
            validate_candidate(agent,Config(**candidates[arm]['config']))
        probe=await observe_probe(server.base_url,str(model_path),key,directory=output/'startup')
        assert probe['response']['choices'][0]['message']['content'].strip()=='READY','Startup did not generate READY'
        atomic_json(output/'gpu_probe.json',probe)
        await require_idle(server.base_url,output/'startup_idle')
        for pos,row in enumerate(runs):
            ident=row['instance_id']
            arm=row['arm'];config=Config(**candidates[arm]['config'])
            admission=window.admission((len(runs)-pos)*(config.outer_seconds+60));journal.append(dict(kind='task_admission',index=row['index'],**admission))
            if not admission['allow']:stop='global time insufficient';break
            task=plan['task_inputs'][ident];directory=output/'runs'/f"{row['index']:02d}-{ident}-{arm}"
            environment=output/'gpu_host_environment'/ident/'environment_admission.json'
            spec=dict(instance_id=ident,base_commit=task['base_commit'],problem_sha256=task['issue_sha256'],
                research_config=config.snapshot(),agent_dir=str(source/candidates[arm]['directory']),candidate_hashes=candidates[arm]['members'],
                tasks_path=str(data/'tasks.jsonl'),snapshots_dir=str(data/'snapshots'),wheels_dir=str(data/'wheels'),
                graph_dir=str(data/'graphs'),embeddings_dir=str(data/'embeddings'),model_alias=MODEL,model_path=str(model_path),base_url=server.base_url,
                research_infrastructure=dict(version=VERSION,environment_admission_path=str(environment),
                    environment_admission_sha256=sha_file(environment),audit_modules=[{'fastapi/fastapi':'fastapi','Textualize/rich':'rich','psf/requests':'requests','encode/httpx':'httpx'}[task['repo']]]))
            spec_path=output/'specs'/f"{row['index']:02d}.json";atomic_json(spec_path,spec)
            print('START',row,flush=True)
            result=supervise([sys.executable,'-m','s2.egv_agenttool_v01.worker_entry',str(spec_path),str(directory)],
                directory,outer_seconds=config.outer_seconds,stage_caps=config.stage_caps,cwd=source)
            audit=inspect_run(directory,config.snapshot(),str(model_path),baseline=json.loads(environment.read_text()))
            from .nested_metrics import inspect_nested
            nested=inspect_nested(directory)
            atomic_json(directory/'nested_metrics.json',nested)
            if not nested['observed']:audit['reasons'].append('nested observer evidence missing')
            if nested['child_workspace_side_effects']:audit['reasons'].append('architecture_violation:child_workspace_write')
            if nested['concurrent_or_ambiguous_delegation']:audit['reasons'].append('architecture_violation:ambiguous_or_concurrent_delegation')
            try:
                audit_all_requests(directory,config,str(model_path))
                audit['server_idle']=await require_idle(server.base_url,directory/'server_reclamation')
            except BaseException as exc:
                audit['reasons'].append('request_semantics_or_server_reclamation:'+repr(exc))
            audit['infrastructure_passed']=not audit['reasons']
            atomic_json(directory/'research_audit.json',audit);bundle(directory)
            records.append(dict(**row,result=result,audit=audit));atomic_json(output/'records.json',records)
            print('RESULT',row,audit['outcome'],audit['reasons'],flush=True)
            if not audit['infrastructure_passed']:stop='infrastructure/evidence gate failed';break
    except BaseException as exc:
        import traceback
        stop=f'{type(exc).__name__}: {exc}'
        atomic_json(output/'session_exception.json',dict(error=stop,traceback=traceback.format_exc()))
        raise
    finally:
        capture_logs(server,output/'backend_logs',phase='before_stop')
        server.stop();psutil.wait_procs(known,timeout=10);forced=[]
        for process in known:
            try:
                if process.is_running() and process.status() not in (psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD):
                    process.kill();forced.append(process.pid)
            except psutil.NoSuchProcess:pass
        psutil.wait_procs(known,timeout=5);live=[]
        for process in known:
            try:
                if process.is_running() and process.status() not in (psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD):live.append(process.pid)
            except psutil.NoSuchProcess:pass
        capture_logs(server,output/'backend_logs',phase='after_stop')
        stopped=bool(known) and not live
        atomic_json(output/'server_cleanup.json',dict(observed_pids=[p.pid for p in known],forced_cleanup_pids=forced,remaining_pids=live,verified=stopped))
        if not stopped:stop=stop or 'server process tree cleanup unconfirmed'
        completed={r['index'] for r in records}
        pending=[dict(**r,status='not_run',reason=stop or 'unlaunched') for r in runs if r['index'] not in completed]
        atomic_json(output/'not_run.json',pending)
        atomic_json(output/'batch_gate.json',dict(experiment_id=EXPERIMENT_ID,infrastructure_passed=not stop and not pending,
            stop_reason=stop,records=records,not_run=pending,protocol_sha256=sha_file(source/'s2/gpu_protocol.json')))
