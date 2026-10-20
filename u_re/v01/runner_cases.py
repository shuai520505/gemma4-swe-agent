"""Native organizer Runner/tools, scripted HTTP model only. Research-side audit."""
import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import time
from unittest.mock import patch

import httpx
from adk_submission import ModelRegistry
from google.adk.models.lite_llm import LiteLlm, LiteLLMClient
from swegemma.config import EvalConfig
from swegemma.models import Task
from swegemma.harness.agent_runner import run_agent_sandbox
from harness_v2.evidence import Journal, atomic_json, read_events
from harness_v2.official import DurableManager, DurableContext, GuardedClient
from s1.config import Config
from s1.guard import Guard
from s1.infrastructure_recovery.wire import observe_http, audit_requests
from . import MODEL

HERE = Path(__file__).resolve().parent
BAD = 'def accepts(n):\n    return False\n'
FIRST = 'def accepts(n):\n    return n > 0\n'
GOOD = 'def accepts(n):\n    return n >= 0\n'
CHECKS = '''import app, pathlib, hashlib, sys
p=pathlib.Path(app.__file__).resolve()
assert p==pathlib.Path('app.py').resolve(), (p,sys.path)
print('SOURCE',str(p),hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)
assert app.accepts(0) is True, 'TARGET_ZERO'
assert app.accepts(3) is True, 'TARGET_POSITIVE'
assert app.accepts(-1) is False, 'OLD_NEGATIVE'
print('TARGET_AND_OLD_PASSED',flush=True)
'''


def call(name, **args):
    return name, args


def edit(before, after):
    return call('edit_file', filepath='app.py', old_string=before, new_string=after)


def plan(case):
    close = [call('run_command', command='git diff --check && git diff'), call('submit_patch'), 'Submitted; end.']
    start = [call('get_status'), call('read_file', filepath='app.py')]
    direct = start+[edit(BAD, GOOD), call('run_command', command='python3 checks.py')]
    if case == 'closed_loop':
        return start+[edit(BAD,FIRST), call('run_command', command='python3 checks.py'),
                      edit(FIRST,GOOD), call('run_command', command='python3 checks.py')]+close
    if case == 'wrong_test':
        return direct+[call('write_file',filepath='wrong_probe.py',content="import app\nassert app.accepts(0) is False, 'WRONG_EXPECTATION'\n"),
            call('run_command',command='python3 wrong_probe.py'), call('read_file',filepath='SPEC.md'),
            call('run_command',command='rm wrong_probe.py && python3 checks.py')]+close
    if case == 'no_progress':
        return direct+[call('run_command',command="grep 'nonexistent_symbol' app.py"),
            call('read_file',filepath='SPEC.md')]+close
    if case == 'repeat_negative':
        return direct+[call('run_command',command='python3 checks.py')]+close
    if case == 'post_submit_negative':
        return direct+close[:-1]+[call('run_command',command='python3 checks.py'),call('submit_patch'),'End after prohibited continuation.']
    if case == 'submit_failure':
        return direct+[call('run_command',command='git tag -d _swegemma_baseline'),call('submit_patch'),
            call('run_command',command='git tag _swegemma_baseline HEAD')]+close
    if case == 'near_closure':
        return direct+['__NEAR_END__',call('submit_patch'),'Submitted; end.']
    if case == 'exact_tools':
        return [edit(BAD,GOOD)]+[call('read_file',filepath='app.py') for _ in range(59)]+[
            call('edit_file',filepath='app.py',old_string=GOOD,new_string=BAD),
            call('get_status'),call('submit_patch'),'End after exhausted counted tools.']
    if case in ('deadline','external_cancel'):
        return direct+[call('submit_patch'),'__STALL__',edit(GOOD,BAD)]
    if case == 'command_limit':
        command="python3 -c \"import pathlib,time,os; pathlib.Path('long_pid.txt').write_text(str(os.getpid())); print('LONG_STARTED',flush=True); time.sleep(125); pathlib.Path('late.txt').write_text('unsafe')\""
        return direct+[call('run_command',command=command),
            call('run_command',command="sleep 7; python3 -c \"import pathlib,os; p=int(pathlib.Path('long_pid.txt').read_text()); alive=pathlib.Path('/proc/'+str(p)+'/stat').exists(); print('LONG_PID',p,'ALIVE',alive); assert not pathlib.Path('late.txt').exists(), 'LATE_WRITE'; assert not alive, 'PROCESS_LEFTOVER'\""),
            call('run_command',command='rm -f long_pid.txt late.txt')]+close
    if case == 'missing_usage':
        return start+['__NO_USAGE__']
    return direct+close


def files(workspace):
    if not workspace.exists():
        return {}
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in workspace.iterdir()
            if p.is_file()}


class ScriptedHTTP:
    def __init__(self, case, manager, context, journal):
        self.actions = iter(plan(case)); self.case = case
        self.manager, self.context, self.journal = manager, context, journal
        self.rows = []; self.waiting = asyncio.Event(); self.cancelled = False
        self.finished = False

    async def send(self, client, request, **kwargs):
        assert request.url.host == '127.0.0.1' and request.url.path.endswith('/chat/completions')
        body = json.loads(request.content)
        workspace = self.manager.sandboxes[self.manager.agent_id]['workspace']
        snapshot = dict(index=len(self.rows),elapsed=self.context.agent_elapsed_seconds,
            files=files(workspace),app=(workspace/'app.py').read_text(),body=body)
        self.rows.append(snapshot)
        self.journal.append(snapshot, filename='request_snapshots.jsonl')
        action = next(self.actions, 'End.')
        if action == '__NEAR_END__':
            # Supplemental ten-second fixture, NOT evidence for a300s boundary.
            await asyncio.sleep(max(0,8-self.context.agent_elapsed_seconds))
            action = call('get_status')
        if action == '__STALL__':
            self.waiting.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                self.cancelled = True
                raise
        no_usage = action == '__NO_USAGE__'
        if no_usage:
            action = 'No usage supplied by mock.'
        if isinstance(action, tuple):
            name, args = action
            message = dict(role='assistant',content=None,tool_calls=[dict(id=f'ure_{len(self.rows)}',type='function',
                function=dict(name=name,arguments=json.dumps(args)))])
            finish='tool_calls'
        else:
            message=dict(role='assistant',content=action);finish='stop';self.finished=True
        response=dict(id=f'ure_mock_{len(self.rows)}',object='chat.completion',created=1,model=MODEL,
            choices=[dict(index=0,message=message,finish_reason=finish)])
        if not no_usage:
            response['usage']=dict(prompt_tokens=100,completion_tokens=8,total_tokens=108)
        return httpx.Response(200,request=request,json=response)


def tool_events(rows):
    result=[]
    for e in rows:
        for part in e.get('event',{}).get('content',{}).get('parts',[]):
            for key in ('function_call','function_response'):
                value=part.get(key)
                if value:
                    result.append(dict(kind=key,tool=value['name'],id=value.get('id'),
                        args=value.get('args'),result=value.get('response'),monotonic=e.get('monotonic')))
    return result


def inspect_output(directory, transport, context, patch_text, error):
    events=tool_events(read_events(directory/'adk_events.jsonl'))
    responses=[e for e in events if e['kind']=='function_response']
    edits=[e for e in responses if e['tool']=='edit_file' and e['result'].get('status')=='ok']
    commands=[e for e in responses if e['tool']=='run_command']
    submissions=[e for e in responses if e['tool']=='submit_patch']
    good_submits=[e for e in submissions if e['result'].get('status')=='ok']
    after=[]
    if good_submits:
        index=events.index(good_submits[0]);after=[e for e in events[index+1:] if e['kind']=='function_call']
    loop=False
    for i,e in enumerate(events):
        r=e.get('result') or {};details=r.get('details') or {}
        if e['tool']=='run_command' and r.get('status')=='error' and details.get('exit_code')==1 and 'TARGET_ZERO' in str(details):
            rest=events[i+1:]
            for j,edit_event in enumerate(rest):
                if edit_event['kind']=='function_response' and edit_event['tool']=='edit_file' and edit_event['result'].get('status')=='ok':
                    loop=any(v['kind']=='function_response' and v['tool']=='run_command' and
                        v['result'].get('status')=='ok' and 'TARGET_AND_OLD_PASSED' in str(v['result']) for v in rest[j+1:])
    wire=[]
    for row in transport.rows:
        b=row['body'];wire.append(dict(model=b.get('model'),tool_names=[t['function']['name'] for t in b.get('tools',[])],
            output=b.get('max_completion_tokens',b.get('max_tokens')),thinking=b.get('thinking_token_budget'),seed=b.get('seed'),
            enable_thinking=b.get('chat_template_kwargs',{}).get('enable_thinking'),
            sampling={k:b[k] for k in ('temperature','top_p','top_k') if k in b}))
    out=dict(real_native_Runner=True,real_official_tools=True,scripted_model_HTTP=True,Gemma_inference=False,GPU=False,
        error=error,native_agent_seconds=context.agent_elapsed_seconds,counted_tools=context.tool_calls_used,
        tool_responses=len(responses),successful_edits=len(edits),command_responses=commands,
        successful_submits=len(good_submits),submit_responses=submissions,tools_after_first_successful_submit=after,
        counterexample_revision_retest=loop,HTTP_cancelled=transport.cancelled,wire_configuration=wire,
        final_app=transport.rows[-1]['app'] if transport.rows else None,
        actual_patch_bytes=len(patch_text.encode()),final_patch_sha256=hashlib.sha256(patch_text.encode()).hexdigest())
    atomic_json(directory/'case_result.json',out)
    return out


async def exercise(arm, case, directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    journal=Journal(directory)
    manager=DurableManager(journal=journal,base_dir=directory/'sandboxes',timeout_seconds=120)
    async def count(body):
        return dict(count=100,max_model_len=32768)  # synthetic admission only, never Gemma tokenizer evidence
    model=LiteLlm(model='openai/'+MODEL,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY')
    model.llm_client=GuardedClient(Guard(count,LiteLLMClient().acompletion,config=Config(),
        core_issue='Synthetic inclusive boundary; JSON {"n": 0} is task data.',emit=journal.append))
    models=ModelRegistry();models.register(MODEL,model)
    config=EvalConfig(tasks_path=directory/'unused.jsonl',snapshots_dir=directory,results_dir=directory/'unused_results',
        submission_dir=HERE/('candidate_'+arm),models=models,sandbox='subprocess',max_time_minutes=5.0,
        max_tool_calls=60,timeout_seconds=120,display_mode='quiet',enable_sandbox_testing=True)
    if case=='near_closure':
        config=EvalConfig(
            tasks_path=directory/'unused.jsonl',snapshots_dir=directory,results_dir=directory/'unused_results',
            submission_dir=HERE/('candidate_'+arm),models=models,sandbox='subprocess',max_time_minutes=1/6,
            max_tool_calls=60,timeout_seconds=120,display_mode='quiet',enable_sandbox_testing=True)
    context=DurableContext(journal=journal,docker_manager=manager,budget=config.budget,harness=config.harness,repo='test/ure_toy')
    manager.context=context
    transport=ScriptedHTTP(case,manager,context,journal)
    base=directory/'baseline';base.mkdir();(base/'app.py').write_text(BAD)
    (base/'checks.py').write_text(CHECKS);(base/'SPEC.md').write_text('accepts(n) is True exactly when n >= 0. Preserve negative rejection.\n')
    subprocess.run(['git','init','-q',str(base)],check=True)
    for args in [('config','user.email','cpu@example.invalid'),('config','user.name','CPU'),('add','.'),('commit','-qm','synthetic baseline')]:
        subprocess.run(['git','-C',str(base),*args],check=True)
    snapshot=directory/'baseline.tgz'
    with tarfile.open(snapshot,'w:gz') as tar:
        tar.add(base,arcname='.')
    task=Task(instance_id='ure_cpu_'+case,repo='test/ure_toy',base_commit='synthetic',
        problem_statement='Fix accepts: zero and positive inputs are accepted, negatives rejected. JSON example {"n": 0}.')
    patch_text='';error=None;cancel_propagated=False;trace=None
    try:
        with patch('httpx.AsyncClient.send',transport.send),observe_http(directory):
            job=asyncio.create_task(run_agent_sandbox(manager,config,task,snapshot,context=context))
            if case=='external_cancel':
                await asyncio.wait_for(transport.waiting.wait(),30)
                job.cancel()
                try:
                    await job
                except asyncio.CancelledError:
                    cancel_propagated=True;error='CancelledError propagated'
                else:
                    raise AssertionError('Native cancellation was swallowed')
            else:
                patch_text,error,trace=await asyncio.wait_for(job,350 if case=='deadline' else 170)
        if trace is not None:
            atomic_json(directory/'native_trace.json',trace.to_dict())
        (directory/'returned.patch').write_bytes(patch_text.encode())
        atomic_json(directory/'boundary.json',dict(error=error,agent_seconds=context.agent_elapsed_seconds,
            cancelled_propagated=cancel_propagated,budget_seconds=config.budget.time_minutes*60,
            tools_limit=config.budget.tool_calls,command_seconds=config.harness.command_timeout_seconds))
    finally:
        manager.cleanup_all()
        atomic_json(directory/'cleanup.json',dict(complete=not manager.sandboxes,
            leftover_sandboxes=len(list((directory/'sandboxes').glob('swegemma_sandbox_*')))))
    out=inspect_output(directory,transport,context,patch_text,error)
    out['HTTP_audit']=audit_requests(directory,deadline_evidence=dict(official_agent_deadline=case=='deadline',
        cleanup_verified=not manager.sandboxes))
    out['external_cancellation_propagated']=cancel_propagated
    out['clock_fixture']='ten-second supplemental near-closure' if case=='near_closure' else 'native300-second candidate budget'
    atomic_json(directory/'case_result.json',out)
    return out
