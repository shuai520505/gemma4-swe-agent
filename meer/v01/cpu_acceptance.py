"""Owned SCRIPTED_ONLY sessions through unmodified official compile/Runner/Verifier.

The chroot adapter is the previously accepted research deployment, not shipped
inside any candidate. Only the organizer's SkillToolset executes verify.py.
"""
import asyncio
import hashlib
import inspect
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent


def write(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,default=str)+'\n',encoding='utf-8')


def transport(actions):
    """Reuse GPU03's owned fixture and HTTP server, replace model responses only."""
    from . import owned_transport as cpu_transport
    source=Path(cpu_transport.__file__).read_text(encoding='utf-8')
    a=source.index('        actions=iter([');b=source.index('        calls=[]',a)
    source=source[:a]+'        actions=iter(ACTIONS)\n'+source[b:]
    mod=types.ModuleType('meer_scripted_boundary');mod.__file__=str(cpu_transport.__file__)
    mod.__dict__['ACTIONS']=actions
    exec(compile(source,str(cpu_transport.__file__),'exec'),mod.__dict__)
    return mod.CPUTransport()


def actions(arm):
    bad='def accepts(value):\n    return value > 0\n'
    check='from fastapi.owned import accepts\nassert accepts(0)\nassert accepts(3)\nassert not accepts(-1)\n'
    create='python3 -c '+shlex.quote('from pathlib import Path; Path("/tmp/meer_check.py").write_text('+repr(check)+')')
    script=dict(skill_name='meer-evidence',file_path='scripts/verify.py',
                args=dict(check='/tmp/meer_check.py',seconds='10'))
    common=[('get_status',{}),('read_file',dict(filepath='fastapi/owned.py')),
            ('write_file',dict(filepath='owned-scratch.txt',content='owned fixture')),
            ('run_command',dict(command=create)),
            # A genuine tool error must return to the Agent, not abort Runner.
            ('run_command',dict(command='python3 -c "raise ValueError(\'OWNED_EXPECTED_ERROR\')"'))]
    if arm!='A':
        common += [('load_skill',dict(skill_name='meer-evidence')),
                   ('run_skill_script',script)]
    common += [('edit_file',dict(filepath='fastapi/owned.py',old_string=bad,new_string=bad.replace('> 0','>= 0')))]
    if arm!='A':
        common += [('run_skill_script',script),('run_skill_script',script)]
    common += [('run_command',dict(command='python3 checks.py && rm owned-scratch.txt && git diff --check && git diff')),
               ('submit_patch',{}),'End.']
    return common


async def session(arm, output, data):
    from adk_submission import ModelRegistry,compile_submission,validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import EvalConfig,build_submission_limits
    from swegemma.context import SwegemmaContext
    from swegemma.models import Task,load_tasks
    from swegemma.harness.verification import verify_task
    from harness_v2.evidence import Journal
    from u_re.v01.experiments.action_priority_01.integrated_cpu_01 import agent_phase
    from s1.verifier_v3.environment import SubprocessManager as Trusted,research_environment
    import adk_submission
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    t=transport(actions(arm)).start(data,out)
    compiled=[];context=None;trusted=None
    try:
        model=LiteLlm(model='openai/gemma-4-31b-it-qat-w4a16-ct',api_base=t.base_url,api_key='EMPTY')
        registry=ModelRegistry();registry.register('gemma-4-31b-it-qat-w4a16-ct',model)
        limits,constraints=build_submission_limits()
        directory=HERE/'candidates'/arm
        validate_directory(directory,limits=limits)
        cfg=EvalConfig(tasks_path=t.data/'tasks.jsonl',snapshots_dir=t.data/'snapshots',
            results_dir=out/'harness',submission_dir=directory,models=registry,sandbox='subprocess',
            wheels_dir=data/'wheels',max_time_minutes=5,max_tool_calls=60,timeout_seconds=120,
            verification_timeout_seconds=300,limits=limits,generation_constraints=constraints,
            enable_sandbox_testing=True,display_mode='quiet')
        original=load_tasks(t.data/'tasks.jsonl')[0]
        task=Task(instance_id=original.instance_id,repo=original.repo,base_commit=original.base_commit,
                  problem_statement=original.problem_statement)
        assert not task.test_patch
        native_compile=adk_submission.compile_submission
        expected=(directory/'prompts/system.md').read_text(encoding='utf-8')
        def observe(*args,**kwargs):
            agent=native_compile(*args,**kwargs)
            assert agent.instruction==expected and not agent.sub_agents
            gen=agent.generate_content_config.model_dump(mode='json',exclude_none=True)
            assert gen==dict(max_output_tokens=16384,seed=17,thinking_config=dict(thinking_budget=4096))
            compiled.append(dict(class_name=type(agent).__name__,instruction_sha256=hashlib.sha256(expected.encode()).hexdigest(),
                generation=gen,code_executor_provided=kwargs.get('code_executor') is not None,
                tool_entries=[getattr(x,'__name__',type(x).__name__) for x in agent.tools]))
            return agent
        # A separate empty-state compile does not install a custom callback registry.
        empty=native_compile(directory,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
        assert empty.instruction==expected
        start=time.perf_counter()
        from swegemma.harness import agent_runner as native_runner
        with patch.object(adk_submission,'compile_submission',observe), patch.object(native_runner,'compile_submission',observe):
            patch_text,error,context=await agent_phase.run(cfg,task,t.data/'snapshots/ure_gpu03_owned.tgz',out/'agent')
        assert context.patch_submitted and patch_text and 'owned-scratch' not in patch_text
        (out/'final.patch').write_text(patch_text)
        native=out/'verifier';native.mkdir()
        trusted=Trusted(journal=Journal(native),base_dir=native/'roots',audit_modules=['fastapi'],
                        task_wheels=data/'wheels',timeout_seconds=120)
        trusted.agent_id='TRUSTED_EVALUATOR_NO_AGENT'
        try:
            with research_environment(audit_modules=['fastapi'],task_wheels=data/'wheels'):
                result=await verify_task(trusted,cfg,original,t.data/'snapshots/ure_gpu03_owned.tgz',
                                         agent_patch=patch_text,start_time=start)
            write(out/'TaskResult.json',result.model_dump(mode='json',exclude={'trace'}))
        finally:
            trusted.cleanup_all()
        junit=native/'phase2.junit.xml'
        xml=ET.parse(junit).getroot()
        assert result.resolved and result.test_exit_code==0
        assert len(list(xml.iter('testcase')))>=1 and not list(xml.iter('failure')) and not list(xml.iter('error'))
        events=[json.loads(x) for x in (out/'agent/adk_events.jsonl').read_bytes().splitlines()]
        responses=[p['function_response'] for e in events for p in e.get('event',{}).get('content',{}).get('parts',[]) if p.get('function_response')]
        names={r['name'] for r in responses}
        assert {'get_status','run_command','read_file','edit_file','write_file','submit_patch'}<=names
        evidence=[]
        for r in responses:
            if r['name']!='run_skill_script':continue
            response=r['response']
            # ADK FunctionTool returns a dictionary; preserve actual output privately.
            if isinstance(response,dict) and isinstance(response.get('stdout'),str):
                try:evidence.append(json.loads(response['stdout']))
                except ValueError:pass
        if arm=='B':
            assert [r['verdict'] for r in evidence]==['CONTRADICTED','SUPPORTED','OBSERVED'],evidence
            assert [r['subprocess_invocations'] for r in evidence]==[1,1,0]
        if arm=='C':
            assert len(evidence)==3 and all(r['verdict']=='UNKNOWN' for r in evidence),evidence
        cleanup=json.loads((out/'agent/cleanup.json').read_bytes())
        assert cleanup['complete'] and compiled and all(x['code_executor_provided'] for x in compiled)
        declarations=[]
        for req in t.calls:
            system='\n'.join(m['content'] for m in req['messages'] if m.get('role')=='system')
            assert expected.strip() in system
            assert req.get('max_completion_tokens',req.get('max_tokens'))==16384
            assert req['thinking_token_budget']==4096 and req['seed']==17
            declarations.append(sorted(x['function']['name'] for x in req['tools']))
        write(out/'SCRIPTED_HTTP_REQUESTS.json',t.calls)  # Private raw archive only.
        summary=dict(arm=arm,CPU_MODEL='SCRIPTED_ONLY',real_Gemma_requests=0,
            compiled=compiled,empty_state_compile=True,tool_names=sorted(names),
            schemas=sorted(set(tuple(x) for x in declarations)),HTTP_requests=len(t.calls),
            charged_tools=context.tool_calls_used,agent_wall_seconds=context.agent_elapsed_seconds,
            worker_wall_seconds=time.perf_counter()-start,patch_bytes=len(patch_text.encode()),
            patch_sha256=hashlib.sha256(patch_text.encode()).hexdigest(),explicit_submit=True,
            native_resolved=result.resolved,TaskResult_sha256=hashlib.sha256((out/'TaskResult.json').read_bytes()).hexdigest(),
            JUnit_sha256=hashlib.sha256(junit.read_bytes()).hexdigest(),
            mechanism_evidence=evidence,cleanup_complete=True,agent_error=error)
        write(out/'SUMMARY.json',summary)
        return summary
    finally:
        if trusted:trusted.cleanup_all()
        t.stop()
        write(out/'TRANSPORT_CLEANUP.json',dict(complete=t.cleaned))


def source_audit():
    import adk_submission.compiler,adk_submission.resolvers.callbacks
    from swegemma.harness import agent_runner
    from google.adk.tools import skill_toolset
    from adk_eval_core.sandbox import AdkSandboxCodeExecutor
    modules=[adk_submission.compiler,adk_submission.resolvers.callbacks,agent_runner,skill_toolset]
    result={}
    for mod in modules:
        p=Path(mod.__file__)
        result[mod.__name__]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),lines=len(p.read_text().splitlines()))
    runner=inspect.getsource(agent_runner.run_agent_sandbox)
    assert 'code_executor=code_executor' in runner and 'callback_registry=' not in runner
    executor=inspect.getsource(AdkSandboxCodeExecutor.execute_code)
    assert 'budget_check_fn' in executor and 'self.sandbox' in executor
    return result


async def run(output):
    import torch
    assert torch.cuda.device_count()==0
    from s1.task_identity import find_data
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    write(output/'OFFICIAL_SOURCE_AUDIT.json',source_audit())
    from . import test_mechanism
    with (output/'MECHANISM_TESTS.log').open('w') as log:
        tests=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_mechanism))
    write(output/'MECHANISM_TESTS.json',dict(tests=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors),skipped=len(tests.skipped)))
    assert tests.wasSuccessful()
    records=[]
    for arm in ('A','B','C'):
        records.append(await session(arm,output/arm,find_data()))
    assert records[1]['schemas']==records[2]['schemas']
    assert records[0]['compiled'][0]['generation']==records[1]['compiled'][0]['generation']==records[2]['compiled'][0]['generation']
    write(output/'CPU_ACCEPTANCE.json',dict(status='MEER_CPU_ENGINEERING_PASS',CPU_MODEL='SCRIPTED_ONLY',
        real_Gemma_requests=0,GPU=False,formal_submission=False,records=records,
        mechanism_scope='Skill verification verdict/caching; direct tools and submit remain unblocked'))


if __name__=='__main__':
    asyncio.run(run(sys.argv[1]))
