"""Mock model responses drive real ADK AgentTool and real organizer sandbox tools.

These fixtures test execution capability and negative-path detection, never model
reasoning ability. They contain no public task/evaluator/repair answers.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time
from unittest.mock import patch

import httpx
from adk_submission import ModelRegistry, compile_submission, validate_directory
from google.adk.models.lite_llm import LiteLlm, LiteLLMClient
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from swegemma.budget import EvaluationBudget, HarnessLimits
from swegemma.context import SwegemmaContext
from swegemma.config import build_submission_limits
from harness_v2.evidence import Journal, atomic_json, read_events
from harness_v2.official import DurableManager, DurableContext, GuardedClient
from s2.egv_agenttool_t500_v01.config import Config
from s1.guard import Guard
from s1.infrastructure_recovery.wire import observe_http, audit_requests
from s2.egv_agenttool_t500_v01.runtime_audit import AuditPlugin, snapshot

HERE = Path(__file__).resolve().parents[1]
MODEL = 'gemma-4-31b-it-qat-w4a16-ct'
BAD = 'def accepts(n):\n    return False\n'
FIRST = 'def accepts(n):\n    return n > 0\n'
GOOD = 'def accepts(n):\n    return n >= 0\n'
CHECKS = '''import app, hashlib, pathlib, sys
print('SOURCE', app.__file__, hashlib.sha256(pathlib.Path(app.__file__).read_bytes()).hexdigest(), flush=True)
print('SYS_PATH', sys.path, flush=True)
print('TARGET', app.accepts(0), flush=True)
assert app.accepts(0) is True, 'TARGET_BOUNDARY'
print('TARGET_PASSED', flush=True)
assert app.accepts(-1) is False, 'OLD_NEGATIVE'
print('OLD_PASSED', flush=True)
'''


def call(name, **args):
    return (name, args)


def edit(before, after):
    return call('edit_file', filepath='app.py', old_string=before, new_string=after)


def plan(case):
    request = 'Issue: accepts(0) must be True and accepts(-1) False. Hypothesis: boundary fixed. app.py changed from False to n > 0; inspect the current diff and falsify it with checks.py. Return remaining risks.'
    delegate = call('egv_verifier', request=request)
    main = [call('get_status'), call('read_file', filepath='app.py'), edit(BAD, FIRST), delegate]
    child = [call('get_status'), call('read_file', filepath='app.py'), call('run_command', command='python3 checks.py'),
             'Verification status: FAIL\nExecution evidence: python3 checks.py failed TARGET_BOUNDARY.\nCounterevidence: zero is rejected by the current workspace app.py.\nRegression coverage: negative case not reached.\nRecommended next action: correct the inclusive boundary and retest.\nRemaining uncertainty: old behavior not yet established.']
    corrected = GOOD
    if case == 'still_fails': corrected = 'def accepts(n):\n    return n < 0\n'
    if case == 'old_regression': corrected = 'def accepts(n):\n    return True\n'
    if case == 'unknown': child = ['Verification status: UNKNOWN; no executed evidence.']
    if case == 'lost_result': child = ['']
    if case == 'invalid_probe': child[2] = call('run_command', command='python3 -c "raise SyntaxError(\'invalid probe\')"')
    if case == 'child_command_timeout': child[2] = call('run_command', command='python3 -c "import time; time.sleep(3)"')
    if case == 'child_write': child.insert(2, call('run_command', command="printf 'def accepts(n):\\n    return True\\n' > app.py"))
    if case == 'forbidden_tool': child = [call('edit_file', filepath='app.py', old_string=FIRST, new_string=GOOD)]
    if case in ('cancel_child', 'native_deadline', 'exact_deadline'): child = ['__STALL__']
    if case=='exact_budget':
        main=[call('get_status')]+[call('read_file',filepath='app.py') for _ in range(59)]+[edit(BAD,FIRST),delegate]
    if case == 'transport_error': child = ['__TRANSPORT_ERROR__']
    if case == 'missing_usage': child = ['__MISSING_USAGE__']
    if case == 'ignored':
        main += [call('run_command', command='git diff --check && git diff'), call('submit_patch'), 'PASS claimed without repair']
    elif case == 'near_deadline':
        main = [call('get_status'), edit(BAD, GOOD), call('run_command', command='python3 checks.py'),
                call('run_command', command='git diff --check && git diff'), call('submit_patch'), 'Complete']
    else:
        main += [edit(FIRST, corrected)]
        if case == 'direct_retest': main += [call('run_command', command='python3 checks.py')]
        else:
            main += [delegate]
            child += [call('read_file', filepath='app.py'), call('run_command', command='python3 checks.py'),
                      'Verification status: PASS for checks.py only; target and old negative assertions passed. Unverified risks remain.']
        main += [call('run_command', command='git diff --check && git diff'), call('submit_patch'), 'Complete']
    return main, child


class ScriptedTransport:
    def __init__(self, case):
        self.case = case
        self.main, self.child = plan(case)
        self.rows = []
        self.stalled = asyncio.Event()
        self.cancelled = False

    async def send(self, _client, request, **kwargs):
        body = json.loads(request.content)
        system = str(body['messages'][0].get('content', ''))
        actor = 'egv_verifier' if 'You are egv_verifier,' in system else 'main_coding_agent'
        queue = self.child if actor == 'egv_verifier' else self.main
        step = queue.pop(0) if queue else 'No further evidence.'
        self.rows.append(dict(actor=actor, body=body, step=step))
        if step == '__STALL__':
            self.stalled.set()
            try: await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.cancelled = True
                raise
        if step == '__TRANSPORT_ERROR__': raise httpx.ConnectError('CPU injected transport failure', request=request)
        if isinstance(step, tuple):
            name, args = step
            message = dict(role='assistant', content=None, tool_calls=[dict(id='cpu_'+str(len(self.rows)), type='function',
                function=dict(name=name, arguments=json.dumps(args)))])
            finish = 'tool_calls'
        else:
            message = dict(role='assistant', content='UNKNOWN: usage unavailable' if step == '__MISSING_USAGE__' else step)
            finish = 'stop'
        payload = dict(id='cpu_'+str(len(self.rows)), object='chat.completion', created=1, model=MODEL,
            choices=[dict(index=0, message=message, finish_reason=finish)])
        if step != '__MISSING_USAGE__': payload['usage'] = dict(prompt_tokens=100, completion_tokens=5, total_tokens=105)
        return httpx.Response(200, request=request, json=payload)


def inspect_case(directory, transport, context):
    rows = read_events(directory/'nested_audit.jsonl')
    starts = {e.get('call_id'):e for e in rows if e['kind']=='tool_start'}
    ends = [e for e in rows if e['kind']=='tool_end']
    children = [e for e in ends if e['actor']=='egv_verifier']
    side_effects = [dict(tool=e['tool'], before=starts[e['call_id']]['files'], after=e['files'])
        for e in children if starts[e['call_id']]['files'] != e['files']]
    target_fail = [e for e in children if e['tool']=='run_command' and 'checks.py' in e['args']['command']
        and 'TARGET_BOUNDARY' in json.dumps(e['result'])]
    delivered = [e for e in ends if e['actor']=='main_coding_agent' and e['tool']=='egv_verifier'
        and 'Counterevidence: zero' in str(e['result'])]
    handled = [e for e in ends if e['actor']=='main_coding_agent' and e['tool']=='edit_file'
        and e['result'].get('status')=='ok' and delivered and e['monotonic'] > delivered[0]['monotonic']
        and starts[e['call_id']]['files'].get('app.py') != e['files'].get('app.py')]
    cleared = [e for e in ends if e['tool']=='run_command' and 'checks.py' in e['args']['command']
        and e['result'].get('status')=='ok' and 'TARGET_PASSED' in str(e['result'])
        and 'OLD_PASSED' in str(e['result']) and handled and e['monotonic'] > handled[0]['monotonic']]
    result=dict(real_compiler=True, real_ADK_Runner=True, mocked_HTTP=True, Gemma_inference=False,
        target_counterevidence=bool(target_fail), feedback_delivered=bool(delivered), feedback_handled=bool(handled),
        counterevidence_cleared=bool(cleared), closed_loop=bool(target_fail and delivered and handled and cleared),
        child_side_effects=side_effects, explicit_submit=context.patch_submitted,
        counted_tools=context.tool_calls_used, actual_tool_events=len(ends),
        model_requests=len(transport.rows), actors={a:sum(r['actor']==a for r in transport.rows) for a in ('main_coding_agent','egv_verifier')},
        all_model_rows=transport.rows, child_HTTP_cancelled=transport.cancelled,
        token_scope='Mock usage only, not Gemma token consumption')
    return result


async def exercise(case, directory, *, native=False, skip=False, research_observer=False):
    directory=Path(directory); directory.mkdir(parents=True, exist_ok=False)
    journal=Journal(directory)
    manager=DurableManager(journal=journal,base_dir=directory/'sandboxes',timeout_seconds=120)
    if case=='submit_fail':
        from adk_eval_core.sandbox import ExecutionResult
        actual_exec=manager.exec
        def failing_git(sandbox_id, command, *, timeout=None):
            if 'git diff --binary' in command:
                return ExecutionResult(status='error',exit_code=2,stdout='',stderr='CPU injected git failure')
            return actual_exec(sandbox_id,command,timeout=timeout)
        manager.exec=failing_git
    real_stop=manager.stop
    def observed_stop(sandbox_id):
        info=manager.sandboxes.get(sandbox_id)
        if native and info:
            before=snapshot(info['workspace'])
            time.sleep(.2)
            after=snapshot(info['workspace'])
            atomic_json(directory/'post_deadline_stability.json',dict(unchanged=before==after,before=before,after=after,
                observation='After native Runner returned/cancelled and before its own sandbox_stop deletes workspace',seconds=.2))
        return real_stop(sandbox_id)
    manager.stop=observed_stop
    transport=ScriptedTransport(case)
    model=LiteLlm(model='openai/'+MODEL,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY')
    async def count(body): return dict(count=100,max_model_len=32768)
    model.llm_client=GuardedClient(Guard(count,LiteLLMClient().acompletion,config=Config(),
        core_issue='Synthetic boundary repair only; JSON payload {"n": 0} is task data.',emit=journal.append))
    models=ModelRegistry();models.register(MODEL,model)
    budget=EvaluationBudget(time_minutes=.05 if case=='native_deadline' else __import__('yaml').safe_load((HERE/'candidate/eval_config.yaml').read_text())['evaluation']['max_time_minutes'],tool_calls=3 if case=='budget' else 60)
    harness=HarnessLimits(command_timeout_seconds=1 if case=='child_command_timeout' else 120,max_stdout_chars=2000)
    context=DurableContext(journal=journal,docker_manager=manager,budget=budget,harness=harness,repo='test/mock_repo')
    manager.context=context
    session=None;runner=None;error=None;plugin=None
    try:
        if native:
            from swegemma.harness.agent_runner import run_agent_sandbox
            from swegemma.config import EvalConfig
            from swegemma.models import Task
            base=directory/'snapshot_source';base.mkdir();(base/'app.py').write_text(BAD);(base/'checks.py').write_text(CHECKS)
            subprocess.run(['git','init','-q',str(base)],check=True)
            # A real task archive has a valid Git baseline. An unborn HEAD
            # makes the actual submit_patch Git diff fail, independently of
            # AgentTool correctness. Keep CPU02's failure evidence unchanged.
            for args in [('config','user.email','cpu@example.invalid'),('config','user.name','CPU'),
                         ('add','.'),('commit','-qm','synthetic baseline')]:
                subprocess.run(['git','-C',str(base),*args],check=True)
            archive=directory/'synthetic.tgz'
            with tarfile.open(archive,'w:gz') as tar:tar.add(base,arcname='.')
            task=Task(instance_id='s2_cpu_'+case,repo='test/mock_repo',base_commit='synthetic',problem_statement='Fix boundary without changing negative behavior.')
            config=EvalConfig(tasks_path=directory/'unused.jsonl',snapshots_dir=directory,results_dir=directory/'native',
                submission_dir=HERE/'candidate',models=models,sandbox='subprocess',max_time_minutes=budget.time_minutes,
                max_tool_calls=budget.tool_calls,timeout_seconds=120,display_mode='quiet',enable_sandbox_testing=True)
            original_init=Runner.__init__
            def observed_init(obj,*args,**kwargs):
                nonlocal plugin
                if plugin is None: plugin=AuditPlugin(manager.sandboxes[manager.agent_id]['workspace'],context,journal)
                app=kwargs.get('app')
                plugins=list((app.plugins if app is not None else kwargs.get('plugins')) or [])
                if not any(p.name==plugin.name for p in plugins):plugins.append(plugin)
                if app is not None: app.plugins=plugins
                else: kwargs['plugins']=plugins
                original_init(obj,*args,**kwargs)
            if research_observer:
                from s2.egv_agenttool_t500_v01.runner_observer import observe_nested
                with patch('httpx.AsyncClient.send',transport.send),observe_http(directory),observe_nested(manager,context,journal):
                    submitted,error,trace=await run_agent_sandbox(manager,config,task,archive,context=context)
            else:
                with patch('httpx.AsyncClient.send',transport.send),observe_http(directory),patch.object(Runner,'__init__',observed_init):
                    submitted,error,trace=await run_agent_sandbox(manager,config,task,archive,context=context)
            atomic_json(directory/'native_trace.json',trace.to_dict());(directory/'native.patch').write_text(submitted)
            atomic_json(directory/'native_boundary.json',dict(error=error,agent_seconds=context.agent_elapsed_seconds))
        else:
            sid=manager.start();context.container_id=sid;workspace=manager.sandboxes[sid]['workspace']
            (workspace/'app.py').write_text(BAD);(workspace/'checks.py').write_text(CHECKS)
            for cmd in ['git init -q','git config user.email cpu@example.invalid','git config user.name CPU',
                        'git add .','git commit -qm baseline','git tag _swegemma_baseline']:
                res=manager.exec(sid,cmd);assert res.exit_code==0,res.stderr
            context.start_agent_session()
            if case=='near_deadline': context.agent_start_time-=470
            limits,constraints=build_submission_limits();validate_directory(HERE/'candidate',limits=limits)
            agent=compile_submission(HERE/'candidate',context.create_tools(),models,limits=limits,generation_constraints=constraints)
            assert agent.tools[-1].agent.name=='egv_verifier'
            if skip:agent.tools[-1].skip_summarization=True
            assert len(agent.tools)==7 and len(agent.tools[-1].agent.tools)==3
            if case=='parameter_drift': agent.tools[-1].agent.generate_content_config.max_output_tokens=8192
            plugin=AuditPlugin(workspace,context,journal)
            sessions=InMemorySessionService();session=await sessions.create_session(app_name='s2_cpu',user_id='cpu',state={})
            assert session.state=={}
            runner=Runner(agent=agent,app_name='s2_cpu',session_service=sessions,plugins=[plugin])
            async def consume():
                async for e in runner.run_async(user_id='cpu',session_id=session.id,
                    new_message=types.Content(role='user',parts=[types.Part(text='Synthetic boundary repair; JSON {"n": 0}.')])):
                    pass
            with patch('httpx.AsyncClient.send',transport.send),observe_http(directory):
                if case=='cancel_child':
                    running=asyncio.create_task(consume())
                    await asyncio.wait_for(transport.stalled.wait(),20)
                    running.cancel()
                    try: await running
                    except asyncio.CancelledError: error='CancelledError propagated'
                    else: raise AssertionError('Cancellation swallowed')
                else:
                    try: await asyncio.wait_for(consume(),45)
                    except Exception as exc:error=repr(exc)
            session=await sessions.get_session(app_name='s2_cpu',user_id='cpu',session_id=session.id)
            atomic_json(directory/'state.json',session.state)
            atomic_json(directory/'final_files.json',snapshot(workspace))
            (directory/'submitted.patch').write_text(context.submitted_patch or '')
            (directory/'final_app.py').write_bytes((workspace/'app.py').read_bytes())
            context.stop_agent_session()
    finally:
        if runner: await runner.close()
        manager.cleanup_all()
        atomic_json(directory/'cleanup.json',dict(complete=not manager.sandboxes,
            leftover_sandboxes=len(list((directory/'sandboxes').glob('swegemma_sandbox_*')))))
    result=inspect_case(directory,transport,context)
    result.update(error=error,native_Harness=native,skip_summarization=skip,
        HTTP=audit_requests(directory,deadline_evidence=dict(official_agent_deadline=case in ('native_deadline','exact_deadline'),
            cleanup_verified=not manager.sandboxes)))
    atomic_json(directory/'result.json',result)
    return result
