"""Selected real snapshots,official Runner,scripted model;no repair/evaluator run."""
import asyncio
import hashlib
import json
from pathlib import Path
import shlex
import sys
from unittest.mock import patch

import httpx
from harness_v2.evidence import atomic_json
from . import agent_phase

HERE=Path(__file__).resolve().parent


def strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,dict):
        for v in value.values():yield from strings(v)
    elif isinstance(value,list):
        for v in value:yield from strings(v)


async def run(output):
    import torch
    assert torch.cuda.device_count()==0
    from s1.task_identity import find_data,identify
    from swegemma.models import load_tasks,Task
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.config import EvalConfig
    from adk_submission import ModelRegistry
    from google.adk.models.lite_llm import LiteLlm,LiteLLMClient
    from harness_v2.official import GuardedClient
    from s1.guard import Guard
    from s1.config import Config
    from s1.infrastructure_recovery.wire import observe_http
    from harness_v2.evidence import Journal
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    selected=json.loads((HERE/'SELECTED_TASKS.json').read_bytes());assert selected['status']=='TWO_TASKS_ADMITTED'
    data=find_data();records={t.instance_id:t for t in load_tasks(data/'tasks.jsonl')};results=[]
    for frozen in selected['tasks']:
        ident=frozen['instance_id'];original=records[ident];actual=identify(data,[ident])[ident]
        for key in ('repo','base_commit','issue_sha256','task_record_sha256','test_patch_sha256','input_files'):assert actual[key]==frozen[key]
        # Explicitly remove evaluator-only task fields before Phase1.
        task=Task(instance_id=ident,repo=original.repo,base_commit=original.base_commit,problem_statement=original.problem_statement)
        assert not task.test_patch
        snapshot,base,incremental=resolve_task_snapshot_paths(data/'snapshots',ident,task.repo)
        code='from pathlib import Path;import fastapi;from fastapi import FastAPI;from fastapi.testclient import TestClient;assert Path(fastapi.__file__).resolve().is_relative_to(Path("/workspace"));app=FastAPI();app.get("/owned_runtime")(lambda:{"ok":True});r=TestClient(app).get("/owned_runtime");assert r.status_code==200 and r.json()=={"ok":True};print("REAL_WORKSPACE_HTTP_200",fastapi.__file__)'
        actions=iter([('get_status',{}),('read_file',dict(filepath='fastapi/__init__.py')),
            ('run_command',dict(command='python3 -c '+shlex.quote(code)+' && git diff --check')),
            ('submit_patch',{}),'End.'])
        requests=[];responses=[]
        async def send(client,request,**kwargs):
            assert request.url.host=='127.0.0.1' and request.url.path.endswith('/chat/completions')
            body=json.loads(request.content)
            assert all(original.test_patch not in s for s in strings(body))
            requests.append(body)
            action=next(actions,'End.')
            if isinstance(action,tuple):
                name,args=action;message=dict(role='assistant',content=None,tool_calls=[dict(id='task_runtime_'+str(len(requests)),type='function',function=dict(name=name,arguments=json.dumps(args)))])
                finish='tool_calls'
            else:message=dict(role='assistant',content=action);finish='stop'
            response=dict(id='owned_'+str(len(requests)),object='chat.completion',created=1,model='gemma-4-31b-it-qat-w4a16-ct',
                choices=[dict(index=0,message=message,finish_reason=finish)],usage=dict(prompt_tokens=100,completion_tokens=8,total_tokens=108))
            responses.append(response)
            return httpx.Response(200,request=request,json=response)
        async def count(body):return dict(count=100,max_model_len=32768)
        directory=output/ident;journal=Journal(output/(ident+'_transport'))
        model=LiteLlm(model='openai/gemma-4-31b-it-qat-w4a16-ct',api_base='http://127.0.0.1:8000/v1',api_key='EMPTY')
        model.llm_client=GuardedClient(Guard(count,LiteLLMClient().acompletion,config=Config(),core_issue=task.problem_statement,emit=journal.append))
        registry=ModelRegistry();registry.register('gemma-4-31b-it-qat-w4a16-ct',model)
        cfg=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=output/(ident+'_native_logs'),
            submission_dir=HERE.parents[2]/'candidate_noegv',models=registry,sandbox='subprocess',wheels_dir=data/'wheels',max_time_minutes=5,max_tool_calls=60,timeout_seconds=120,enable_sandbox_testing=True,display_mode='quiet')
        with patch('httpx.AsyncClient.send',send),observe_http(journal.directory):
            patch_text,error,context=await agent_phase.run(cfg,task,snapshot,directory,base_snapshot=base,incremental_patch=incremental)
        events=[json.loads(line) for line in (directory/'adk_events.jsonl').read_bytes().splitlines()]
        tool_results=[part['function_response'] for e in events for part in e.get('event',{}).get('content',{}).get('parts',[]) if part.get('function_response')]
        assert error is None and not patch_text.strip() and context.patch_submitted
        assert any(r['name']=='run_command' and r['response']['status']=='ok' and 'REAL_WORKSPACE_HTTP_200' in str(r['response']) for r in tool_results)
        assert all(r['response']['status']=='ok' for r in tool_results)
        atomic_json(directory/'scripted_requests.json',requests)
        atomic_json(directory/'task_identity.json',actual)
        results.append(dict(instance_id=ident,real_original_snapshot=True,official_Runner=True,workspace_import_and_HTTP_assertion=True,
            approved_runtime_fingerprint=True,empty_patch_expected=True,evaluator_overlay_not_supplied=True,cleanup=True,
            HTTP_model='SCRIPTED_ONLY',real_Gemma=0,agent_seconds=context.agent_elapsed_seconds,charged_tools=context.tool_calls_used))
    atomic_json(output/'REAL_TASK_RUNTIME_ACCEPTANCE.json',dict(status='PASS',tasks=results,Agent_runs=2,GPU=False,real_Gemma=0,native_task_baseline_calls=0))
    print('REAL_TASK_RUNTIME_ACCEPTANCE_PASS',flush=True)


if __name__=='__main__':asyncio.run(run(sys.argv[1]))
