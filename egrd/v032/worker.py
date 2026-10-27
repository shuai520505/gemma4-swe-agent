"""Exactly one native S0 Agent invocation; actual local Gemma only, no mock route."""
import asyncio
import importlib.metadata as md
import json
from pathlib import Path
import sys
import time
import traceback
import zipfile

from egrd.v031.prepare import ROOT,HERE as FROZEN,S0_SHA,sha,write,arm_input
from harness_v2.evidence import Journal,read_events
from .source_observer import Tracker
from .observe import capture


async def run(spec,output):
    from adk_submission import ModelRegistry,compile_submission,validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import EvalConfig,build_submission_limits
    from swegemma.models import Task
    from swegemma.context import SwegemmaContext
    from swegemma.harness.agent_runner import run_agent_sandbox
    from harness_v2.official import DurableContext
    from egrd.v0311.sandbox_adapter import SubprocessManager as Accepted
    from .evaluate import evaluate
    assert spec['transport']=='REAL_GEMMA' and spec['arm'] in ('A','B')
    assert spec['base_url']=='http://127.0.0.1:8000/v1'
    out=Path(output);out.mkdir(parents=True,exist_ok=True);journal=Journal(out)
    journal.stage('prepare_agent');started=time.monotonic()
    arm=spec['arm'];data=Path(spec['data']);task=spec['task']
    package=ROOT/'candidates/s0/submission.zip';assert sha(package.read_bytes())==S0_SHA
    candidate=out/'candidate'
    with zipfile.ZipFile(package) as archive:archive.extractall(candidate)
    original=json.loads((FROZEN/'private/original_task.json').read_bytes())
    receipt=json.loads((FROZEN/'EVIDENCE_RECEIPT.json').read_bytes())
    problem=arm_input(original['problem_statement'],receipt,arm)
    assert sha(problem.encode())==spec['input_sha256']
    actual=Task(instance_id=original['instance_id'],repo=original['repo'],base_commit=original['base_commit'],problem_statement=problem)
    assert not actual.test_patch and not actual.hints_text
    registry=ModelRegistry();registry.register('gemma-4-31b-it-qat-w4a16-ct',LiteLlm(
        model='openai/'+spec['model_path'],api_base=spec['base_url'],api_key='EMPTY'))
    limits,constraints=build_submission_limits();validate_directory(candidate,limits=limits)
    compiled=compile_submission(candidate,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
    gen=compiled.generate_content_config.model_dump(mode='json',exclude_none=True)
    assert gen=={'max_output_tokens':16384,'thinking_config':{'thinking_budget':4096}}
    assert compiled.instruction==(candidate/'prompts/system.md').read_text()
    tools=[t.__name__ for t in compiled.tools]
    assert tools==['get_status','run_command','read_file','edit_file','write_file','submit_patch'] and not compiled.sub_agents
    write(out/'COMPILED_CONFIGURATION.json',dict(generation=gen,tools=tools,instruction_sha256=sha(compiled.instruction.encode()),
        S0_sha256=S0_SHA,model_registry_resolved=spec['model_path'],source_package_model_label='gemma-4-31b-it-qat-w4a16-ct',
        seed_explicit=False,include_thoughts_explicit=False,custom_Context_Guard=False))
    class SubprocessManager(Accepted):
        def _process(self,sid,mode,argument,*args,**kwargs):
            try:return super()._process(sid,mode,argument,*args,**kwargs)
            finally:
                context=getattr(self,'context',None)
                if context is not None and context.agent_start_time is not None and context.agent_end_time is None:
                    if sid in self.sandboxes:
                        self.tracker.observe(self.sandboxes[sid]['workspace'],context.agent_elapsed_seconds,mode)
    manager=SubprocessManager(journal=journal,base_dir=out/'roots',task_wheels=Path(spec['wheels']),timeout_seconds=120)
    manager.tracker=Tracker(out/'source_versions',journal,json.loads(Path(spec['production_baseline']).read_bytes()))
    class Context(DurableContext):
        def start_agent_session(self):
            super().start_agent_session()
            self.docker.tracker.observe(self.docker.sandboxes[self.docker.agent_id]['workspace'],self.agent_elapsed_seconds,'agent_start')
    cfg=EvalConfig(tasks_path=FROZEN/'private/original_task.json',snapshots_dir=Path(spec['snapshot']).parent,
        results_dir=out/'harness',submission_dir=candidate,models=registry,sandbox='subprocess',wheels_dir=Path(spec['wheels']),
        max_time_minutes=5,max_tool_calls=60,timeout_seconds=120,verification_timeout_seconds=300,
        limits=limits,generation_constraints=constraints,enable_sandbox_testing=True,display_mode='quiet')
    assert cfg.events_compaction_config is None
    context=Context(journal=journal,docker_manager=manager,task=actual,budget=cfg.budget,harness=cfg.harness)
    manager.context=context
    expected=json.loads(Path(spec['expected_request']).read_bytes())
    summary=dict(arm=arm,started=True,full_compiler=True,model_transport='REAL_GEMMA',official_native_resolved=None,
                 canonical_swebench_resolved=None,cleanup=False)
    try:
        with capture(out/'model_transport',expected):
            patch,error,trace=await run_agent_sandbox(manager,cfg,actual,Path(spec['snapshot']),context=context)
        journal.stage('save_patch')
        if trace is not None:write(out/'native_trace.json',trace.to_dict())
        name='submitted.patch' if context.patch_submitted else 'unsubmitted_fallback.patch'
        (out/name).write_bytes(patch.encode())
        manager.cleanup_all()
        closed=not manager.sandboxes and all(not Path(e['lease']).exists() for e in manager.entries)
        write(out/'AGENT_CLEANUP.json',dict(complete=closed,records=manager.cleanup_records))
        assert closed,'Agent cleanup failed; no trusted evaluation or next arm'
        summary.update(agent_error=error,agent_seconds=context.agent_elapsed_seconds,
            charged_tools=context.tool_calls_used,native_llm_calls=context.llm_calls_used,
            patch_submitted=context.patch_submitted,patch_bytes=len(patch.encode()),
            submitted_patch_sha256=sha(patch.encode()) if context.patch_submitted else None,
            fallback_patch_sha256=sha(patch.encode()) if not context.patch_submitted and patch else None,
            source_observer_seconds=manager.tracker.overhead_seconds,agent_cleanup=closed)
        write(out/'AGENT_RESULT.json',summary)
        # Evaluate every arm, including missing/empty submissions. An unsubmitted
        # fallback is retained privately but cannot become a submitted repair.
        submitted=patch if context.patch_submitted and patch else None
        evaluated=evaluate(task,data,out/'trusted',Path(spec['snapshot']),Path(spec['wheels']),
            Path(spec['regression']),submitted,stage=journal.stage)
        summary['evaluation']=evaluated
        summary['submission_state']='SUBMITTED_NONEMPTY' if submitted else 'EMPTY_SUBMITTED' if context.patch_submitted else 'MISSING_SUBMISSION'
        summary['cleanup']=closed and evaluated['cleanup']
        summary['boundary_pass']=json.loads((out/'model_transport/INITIAL_INPUT_GATE.json').read_bytes())['passed']
        summary['worker_seconds']=time.monotonic()-started
        write(out/'SESSION_RESULT.json',summary)
        assert summary['boundary_pass'] and summary['cleanup']
        assert evaluated.get('trusted_probe_unchanged') is True,'Trusted probe integrity unknown or changed'
        journal.stage('persist')
        write(out/'worker_done.json',dict(cleanup_complete=True,ordinary_agent_failure_retained=error is not None))
        return summary
    except BaseException as exc:
        write(out/'WORKER_EXCEPTION.json',dict(type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()))
        raise
    finally:
        journal.stage('cleanup');manager.cleanup_all()
        write(out/'FINAL_AGENT_CLEANUP.json',dict(complete=not manager.sandboxes,
            lease_files_absent=all(not Path(e['lease']).exists() for e in manager.entries),records=manager.cleanup_records))


if __name__=='__main__':asyncio.run(run(json.loads(Path(sys.argv[1]).read_bytes()),sys.argv[2]))
