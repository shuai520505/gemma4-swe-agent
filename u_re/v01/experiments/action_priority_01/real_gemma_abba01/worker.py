"""Real local vLLM -> unchanged official Agent phase -> separate native Verifier.

Observations never enter Agent decisions. No scripted model implementation here.
"""
import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
import stat
import sys
import time
import traceback
from unittest.mock import patch

from harness_v2.evidence import Journal,atomic_json,atomic_bytes,read_events
from ..integrated_cpu_01 import agent_phase


def source_state(workspace):
    """Read only regular source files using O_NOFOLLOW directory descriptors."""
    result={}
    def visit(fd,prefix):
        for name in os.listdir(fd):
            if name in ('.git','__pycache__','.venv'):continue
            info=os.stat(name,dir_fd=fd,follow_symlinks=False)
            rel=prefix+'/'+name if prefix else name
            if stat.S_ISDIR(info.st_mode):
                child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                try:visit(child,rel)
                finally:os.close(child)
            elif stat.S_ISREG(info.st_mode) and name.endswith('.py') and rel.startswith('fastapi/'):
                child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
                try:
                    h=hashlib.sha256()
                    while True:
                        raw=os.read(child,1048576)
                        if not raw:break
                        h.update(raw)
                    result[rel]=h.hexdigest()
                finally:os.close(child)
    fd=os.open(workspace,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:visit(fd,'')
    finally:os.close(fd)
    return result


class SubprocessManager(agent_phase.SubprocessManager):
    """Passive source hashes at actual tool filesystem boundary; no new tool."""
    def _process(self,sid,mode,argument,data=None,timeout=None):
        workspace=self.sandboxes[sid]['workspace'];before=source_state(workspace);start=time.monotonic()
        result=super()._process(sid,mode,argument,data=data,timeout=timeout)
        after=source_state(workspace);end=time.monotonic()
        changed=sorted(n for n in set(before)|set(after) if before.get(n)!=after.get(n))
        self.journal.append(dict(kind='source_boundary_observation',mode=mode,start_monotonic=start,end_monotonic=end,
            operation_sha256=hashlib.sha256(argument.encode()).hexdigest(),exit_code=result[2],
            before=before,after=after,production_changed=changed,
            timing='Change occurred within this actual operation interval; end is observation upper bound'))
        if changed:
            raw,err,code,_,_=super()._process(sid,'exec','git diff --binary _swegemma_baseline',timeout=30)
            if code==0:self.journal.patch(raw.decode(),source='observed_source_change')
        return result


async def evaluate(spec,directory):
    from adk_submission import ModelRegistry,compile_submission
    from google.adk.models.lite_llm import LiteLlm,LiteLLMClient
    from swegemma.config import EvalConfig,build_submission_limits
    from swegemma.models import Task,load_tasks
    from swegemma.context import SwegemmaContext
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from harness_v2.official import GuardedClient
    from harness_v2.context_budget import VllmCounter
    from s1.guard import Guard
    from s1.config import Config,validate_compiled
    from s1.infrastructure_recovery.wire import observe_http,audit_requests
    from s1.verifier_v3.environment import SubprocessManager as Trusted,research_environment
    from s1.verifier_v3.audit import audit_verifier
    directory=Path(directory);j=Journal(directory);j.stage('prepare_agent')
    budget=Config();data=Path(spec['data']);original=next(t for t in load_tasks(data/'tasks.jsonl') if t.instance_id==spec['instance_id'])
    task=Task(instance_id=original.instance_id,repo=original.repo,base_commit=original.base_commit,problem_statement=original.problem_statement)
    assert not task.test_patch
    snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots',task.instance_id,task.repo)
    # This registry is backed by the real served path and live tokenizer.
    model=LiteLlm(model='openai/'+spec['model_path'],api_base=spec['base_url'],api_key='EMPTY')
    model.llm_client=GuardedClient(Guard(VllmCounter(spec['base_url'],'EMPTY'),LiteLLMClient().acompletion,
        core_issue=task.problem_statement,emit=j.append,config=budget))
    registry=ModelRegistry();registry.register('gemma-4-31b-it-qat-w4a16-ct',model)
    limits,constraints=build_submission_limits()
    cfg=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=directory/'harness',
        submission_dir=Path(spec['agent_dir']),models=registry,sandbox='subprocess',wheels_dir=data/'wheels',
        max_time_minutes=5,max_tool_calls=60,timeout_seconds=120,verification_timeout_seconds=300,
        limits=limits,generation_constraints=constraints,enable_sandbox_testing=True,display_mode='quiet')
    compiled=compile_submission(cfg.submission_dir,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
    validate_compiled(compiled,budget)
    atomic_json(directory/'runtime_config.json',dict(budget=budget.snapshot(),real_model=True,model_path=spec['model_path'],
        generation=compiled.generate_content_config.model_dump(mode='json',exclude_none=True)))
    # Separate working directory and stripped Task; research tests are not inputs.
    handler=logging.FileHandler(directory/'official_harness.log',encoding='utf-8')
    for name in ('swegemma','adk_submission'):
        logger=logging.getLogger(name);logger.setLevel(logging.INFO);logger.addHandler(handler)
    context=None;trusted=None;clean=False;agent_error=None
    begin=time.perf_counter()
    try:
        j.stage('agent')
        with patch.object(agent_phase,'SubprocessManager',SubprocessManager),observe_http(directory/'agent'):
            patch_text,agent_error,context=await agent_phase.run(cfg,task,snapshot,directory/'agent',base_snapshot=base,incremental_patch=overlay)
        atomic_bytes(directory/'final.patch',patch_text.encode())
        j.patch(patch_text,source='native_agent_return')
        j.stage('prepare_verifier')
        # Original task with evaluator overlay exists ONLY in this trusted phase.
        native=directory/'verifier';native.mkdir()
        trusted=Trusted(journal=Journal(native),base_dir=native/'roots',audit_modules=['fastapi'],task_wheels=data/'wheels',timeout_seconds=120)
        trusted.agent_id='TRUSTED_EVALUATOR_NO_AGENT'
        j.stage('verification')
        try:
            with research_environment(audit_modules=['fastapi'],task_wheels=data/'wheels'):
                result=await verify_task(trusted,cfg,original,snapshot,base_snapshot_path=base,patch_path=overlay,agent_patch=patch_text,start_time=begin)
            raw=result.model_dump(mode='json',exclude={'trace'})
            atomic_json(native/'official_result.json',raw);atomic_json(directory/'official_result.json',raw)
        finally:
            trusted.cleanup_all();atomic_json(native/'cleanup.json',dict(complete=not trusted.sandboxes))
        baseline=json.loads(Path(spec['baseline_capture']).read_bytes());baseline['eligible']=True
        structured=audit_verifier(native,baseline=baseline);atomic_json(native/'structured_verifier.json',structured)
        assert (native/'phase2.junit.xml').is_file(),'Missing original native JUnit'
        atomic_json(directory/'native_summary.json',dict(resolved=result.resolved,test_exit_code=result.test_exit_code,
            counts=structured.get('counts'),category=structured['category'],infrastructure_stop=structured['infrastructure_stop'],
            attribution=structured.get('attribution'),agent_error=agent_error,patch_bytes=len(patch_text.encode())))
        events=read_events(directory/'agent/events.jsonl')
        deadlines=[r for r in events if r.get('stage')=='save_patch' and r.get('agent_elapsed_seconds',0)>=299]
        http=audit_requests(directory/'agent',deadline_evidence=dict(official_agent_deadline=bool(deadlines),
            cleanup_verified=True,cutoff_monotonic=deadlines[-1]['recorded_monotonic'] if deadlines else None))
        atomic_json(directory/'HTTP_AUDIT.json',http)
        # Validate actual inputs without leaking evaluator strings into them.
        for row in read_events(directory/'agent/http_wire.jsonl'):
            if row['kind']=='http_request':
                assert not original.test_patch or original.test_patch not in row.get('raw_body_utf8','')
        assert http['passed'],('Unaccounted HTTP lifecycle',http['reasons'])
        assert not structured['infrastructure_stop'],('Native verifier environment/evidence STOP',structured['category'])
        clean=True
    finally:
        j.stage('cleanup');handler.flush();handler.close()
        if trusted:trusted.cleanup_all()
        agent_cleanup=json.loads((directory/'agent/cleanup.json').read_bytes()) if (directory/'agent/cleanup.json').exists() else {}
        atomic_json(directory/'worker_done.json',dict(cleanup_complete=bool(agent_cleanup.get('complete')) and (trusted is None or not trusted.sandboxes),
            integrity_complete=clean,agent_error=agent_error))


def main():
    directory=Path(sys.argv[2]);directory.mkdir(parents=True,exist_ok=True)
    try:asyncio.run(evaluate(json.loads(Path(sys.argv[1]).read_bytes()),directory))
    except BaseException as exc:
        atomic_json(directory/'worker_exception.json',dict(type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()));raise

if __name__=='__main__':main()
