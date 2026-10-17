"""Study 02 C1 session: pinned model bytes, full Runner CPU gate, fresh B/C1 pair."""
import asyncio
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
from harness_v2.evidence import atomic_json, bundle
from harness_v2.supervisor import supervise
from cure.runner import require_gate
from cure.runtime_config import ResearchConfig, validate_compiled
from cure.gpu_mechanism.audit import inspect_run


def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''): h.update(chunk)
    return h.hexdigest()


async def run(source, output, batch):
    import torch
    from adk_submission import VllmConfig, VllmServer, compile_submission, discover_adapters
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    from google.adk.models.lite_llm import LiteLLMClient
    from harness_v2.context_budget import VllmCounter, ContextBudgetExceeded
    from cure.request_guard import ConfiguredGuard
    source,output=Path(source),Path(output)
    plan=json.loads((source/'study/protocol.json').read_text())
    require_gate(source/'study/cpu_gate.json',source)
    runner_gate=json.loads((source/'study/full_runner_cpu_gate.json').read_text())
    registration=json.loads((source/'study/runner_registration.json').read_text())
    assert runner_gate['passed'] is True and runner_gate['runner_tests_passed'] is True
    assert runner_gate['registration_sha256']==sha_file(source/'study/runner_registration.json')
    for name,digest in registration['source_hashes'].items():
        assert sha_file(source/name)==digest,name
    for name,digest in plan['runtime_source_hashes'].items():
        assert sha_file(source/name)==digest, name
    config=ResearchConfig(**plan['research_config'])
    def one(paths):
        paths=list(paths); assert len(paths)==1,paths
        return paths[0]
    model_path=one(p.parent for p in Path('/kaggle/input').rglob('config.json')
        if plan['model_alias'] in p.parts and any(p.parent.glob('*.safetensors')))
    assert model_path.name=='2','Require pinned Kaggle model version 2'
    assert torch.cuda.device_count()==4 and all('L4' in torch.cuda.get_device_name(i) for i in range(4))
    # Attest all model bytes before the first generation, including weights/tokenizer/template.
    identity={p.relative_to(model_path).as_posix():sha_file(p) for p in sorted(model_path.rglob('*')) if p.is_file()}
    atomic_json(output/'model_identity.json',dict(version=plan['model'],files=identity,
        manifest_sha256=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()))
    assert identity==plan['expected_model_files'],'Pinned model bytes changed'
    limits,constraints=build_submission_limits()
    adapters=discover_adapters(str(source/'cure/candidates/checklist')); assert not adapters.adapters
    cfg=VllmConfig(model=str(model_path),host='127.0.0.1',port=8000,tool_call_parser='gemma4',
        reasoning_parser='gemma4',max_model_len=32768,dtype='bfloat16',gpu_memory_utilization=.90,
        enable_auto_tool_choice=True,enable_lora=False,scheduler_reserve_full_isl=False,
        tensor_parallel_size=4,startup_timeout=1200)
    atomic_json(output/'vllm_config.json',asdict(cfg))
    server=VllmServer(cfg,adapter_manifest=adapters)
    records=[]; stop_reason=None
    try:
        server.start()
        key=os.environ.get('LOCAL_API_KEY','EMPTY')
        with urllib.request.urlopen(urllib.request.Request(server.base_url+'/models',
            headers={'Authorization':'Bearer '+key}),timeout=30) as response:
            served=json.load(response)
        atomic_json(output/'served_models.json',served)
        assert any(x['id']==str(model_path) for x in served['data'])
        registry=server.create_model_registry(aliases=[plan['model_alias']],model_prefix='openai/',api_key=key)
        for arm in ('checklist','cure_v01_c1'):
            agent=compile_submission(source/'cure/candidates'/arm,SwegemmaContext().create_tools(),registry,
                limits=limits,generation_constraints=constraints)
            validate_compiled(agent,config)
        admissions=[]
        backend=LiteLLMClient()
        guard=ConfiguredGuard(VllmCounter(server.base_url,key),backend.acompletion,
            core_issue='Infrastructure-only probe: reply READY.',config=config,emit=admissions.append)
        reply=await guard.acompletion(model='openai/'+str(model_path),api_base=server.base_url,api_key=key,
            messages=[dict(role='user',content='Infrastructure-only probe: reply READY.')],tools=None,
            max_completion_tokens=8192,temperature=.2,top_p=.95,top_k=40,
            extra_body=dict(chat_template_kwargs=dict(enable_thinking=True),thinking_token_budget=4096))
        atomic_json(output/'gpu_probe.json',dict(response=reply.model_dump(),admissions=admissions))
        assert reply.model==str(model_path) and reply.usage.prompt_tokens==admissions[-1]['input_tokens']
        assert reply.usage.completion_tokens>0
        async def forbidden(**kwargs): raise AssertionError('Oversize generation reached backend')
        over=[]
        oversize=ConfiguredGuard(VllmCounter(server.base_url,key),forbidden,core_issue='Boundary',config=config,emit=over.append)
        try:
            await oversize.acompletion(model='openai/'+str(model_path),messages=[dict(role='user',content=' token'*30000)],max_completion_tokens=8192)
        except ContextBudgetExceeded: pass
        else: raise AssertionError('Oversize request not rejected')
        atomic_json(output/'oversize_probe.json',over)
        rows=plan['batches'][batch]
        for row in rows:
            name=f"{row['index']:02d}-{row['task_id']}-{row['arm']}"
            directory=output/'runs'/name
            spec=dict(research_config=plan['research_config'],agent_dir=str(source/'cure/candidates'/row['arm']),
                candidate_hashes=plan['candidates'][row['arm']]['members'],
                tasks_path=str(source/'study/data/tasks.jsonl'),snapshots_dir=str(source/'study/data/snapshots'),
                wheels_dir=str(source/'study/data/wheels'),graph_dir=str(source/'study/data/graphs'),
                embeddings_dir=str(source/'study/data/embeddings'),model_alias=plan['model_alias'],
                model_path=str(model_path),base_url=server.base_url,instance_id=row['task_id'],
                base_commit=row['base_commit'],problem_sha256=row['problem_sha256'])
            spec_path=output/'specs'/(name+'.json'); atomic_json(spec_path,spec)
            result=supervise([sys.executable,'-m','cure.gpu_mechanism.worker_entry',str(spec_path),str(directory)],
                directory,outer_seconds=config.outer_seconds,stage_caps=config.stage_caps,cwd=source)
            audit=inspect_run(directory,str(model_path))
            atomic_json(directory/'mechanism_audit.json',audit)
            bundle(directory)
            records.append(dict(**row,result=result,infrastructure_passed=audit['infrastructure_passed'],
                audit_path=str(directory/'mechanism_audit.json')))
            atomic_json(output/'records.json',records)
            if not audit['infrastructure_passed']:
                stop_reason='infrastructure_or_evidence_gate_failed_at_'+name
                break
        completed={r['index'] for r in records}
        not_run=[dict(**r,status='not_run',reason=stop_reason or 'separate batch not launched')
            for r in rows if r['index'] not in completed]
        atomic_json(output/'not_run.json',not_run)
        passed=len(records)==len(rows) and all(r['infrastructure_passed'] for r in records)
        atomic_json(output/'batch_gate.json',dict(experiment_id=plan['experiment_id'],batch=batch,
            infrastructure_passed=passed,stop_reason=stop_reason,records=records,model_files=identity,
            protocol_sha256=sha_file(source/'study/protocol.json')))
    except BaseException as exc:
        import traceback
        stop_reason=type(exc).__name__+': '+str(exc)
        atomic_json(output/'session_exception.json',dict(error=stop_reason,traceback=traceback.format_exc()))
        atomic_json(output/'batch_gate.json',dict(experiment_id=plan['experiment_id'],batch=batch,
            infrastructure_passed=False,stop_reason=stop_reason,records=records,model_files=identity))
        completed={r['index'] for r in records}
        atomic_json(output/'not_run.json',[dict(**r,status='not_run',reason=stop_reason)
            for r in plan['batches'][batch] if r['index'] not in completed])
        raise
    finally:
        log=getattr(server,'log_path',None)
        if log and Path(log).is_file(): shutil.copyfile(log,output/'vllm.log')
        server.stop()
        atomic_json(output/'server_stopped.json',dict(stop_returned=True))
