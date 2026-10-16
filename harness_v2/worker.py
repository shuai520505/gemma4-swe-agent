"""One official evaluate_task per disposable process, sharing only the model server."""
import argparse
import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
import traceback

from .budgets import Budgets
from .context_budget import RequestGuard,VllmCounter
from .evidence import Journal,atomic_json,atomic_bytes
from . import VERSION


async def evaluate(spec,directory):
    from adk_submission import ModelRegistry,compile_submission
    from google.adk.agents.context_cache_config import ContextCacheConfig
    from google.adk.apps._configs import EventsCompactionConfig
    from google.adk.models.lite_llm import LiteLlm,LiteLLMClient
    from swegemma.config import EvalConfig,build_submission_limits
    from swegemma.budget import HarnessLimits
    from swegemma.models import load_tasks
    from .official import DurableContext,DurableEvaluator,DurableManager,GuardedClient
    j=Journal(directory)
    j.stage('prepare_agent')
    budget=Budgets()
    agent_dir=Path(spec['agent_dir'])
    for name,digest in spec['candidate_hashes'].items():
        assert hashlib.sha256((agent_dir/name).read_bytes()).hexdigest()==digest,'Candidate changed'
    task=next(t for t in load_tasks(Path(spec['tasks_path'])) if t.instance_id==spec['instance_id'])
    assert task.base_commit==spec['base_commit']
    assert hashlib.sha256(task.problem_statement.encode()).hexdigest()==spec['problem_sha256']
    key=os.environ.get('LOCAL_API_KEY','EMPTY')
    model=LiteLlm(model='openai/'+spec['model_path'],api_base=spec['base_url'],api_key=key)
    backend=LiteLLMClient()
    guard=RequestGuard(VllmCounter(spec['base_url'],key),backend.acompletion,
        core_issue=task.problem_statement,emit=j.append)
    model.llm_client=GuardedClient(guard)
    models=ModelRegistry(); models.register(spec['model_alias'],model)
    limits,constraints=build_submission_limits()
    cfg=EvalConfig(tasks_path=Path(spec['tasks_path']),snapshots_dir=Path(spec['snapshots_dir']),
        results_dir=directory/'harness',submission_dir=agent_dir,models=models,sandbox='subprocess',
        wheels_dir=Path(spec['wheels_dir']),graph_dir=spec['graph_dir'],embeddings_dir=spec['embeddings_dir'],
        max_time_minutes=budget.agent_seconds/60,max_tool_calls=budget.max_tool_calls,
        timeout_seconds=budget.command_seconds,verification_timeout_seconds=budget.stage_caps['verification'],
        limits=limits,generation_constraints=constraints,concurrency=1,display_mode='quiet',
        enable_sandbox_testing=True,context_cache_config=ContextCacheConfig(min_tokens=2048,ttl_seconds=1800,cache_intervals=10),
        events_compaction_config=EventsCompactionConfig(compaction_interval=5,overlap_size=1,
            token_threshold=8192,event_retention_size=4))
    # Only public operational limits change, identically for both frozen candidates.
    cfg.harness=HarnessLimits(command_timeout_seconds=120,max_stdout_chars=2000,
        max_file_lines=120,max_file_chars=4000,verification_timeout_seconds=300)
    evaluator=DurableEvaluator(cfg,journal=j)
    manager=DurableManager(journal=j,base_dir=directory/'sandbox_tmp',timeout_seconds=120)
    evaluator.docker=evaluator.sandbox=manager
    ctx=DurableContext(journal=j,docker_manager=manager,task=task,budget=cfg.budget,harness=cfg.harness,
        graph_dir=cfg.graph_dir,embeddings_dir=cfg.embeddings_dir)
    manager.context=ctx
    compiled=compile_submission(agent_dir,ctx.create_tools(),models,limits=limits,generation_constraints=constraints)
    assert len(compiled.tools)==6 and not compiled.sub_agents
    assert compiled.generate_content_config.max_output_tokens==16384
    atomic_json(directory/'runtime_config.json',dict(harness_version=VERSION,budget=budget.as_dict(),
        compaction=dict(interval=5,overlap=1,token_threshold=8192,event_retention_size=4),
        operational_limits=dict(max_stdout_chars=2000,max_file_chars=4000,max_file_lines=120),
        max_model_len=32768,output_reserved=16384,safety_tokens=1024,
        model=spec['model_path'],candidate_hashes=spec['candidate_hashes']))
    atomic_json(directory/'incremental_trace_scope.json',dict(
        observer='SwegemmaContext.handle_adk_event',native_trace=False,
        missing='System/task prompt and compaction custom events may only exist in the native boundary Trace'))
    handler=logging.FileHandler(directory/'official_harness.log',encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))
    for name in ('swegemma','adk_submission'):
        logger=logging.getLogger(name); logger.setLevel(logging.INFO); logger.addHandler(handler)
    try:
        result=await evaluator.evaluate_task(task=task,context=ctx)
        j.stage('persist')
        # Native scalar fields remain untouched. The trace object is exported separately.
        raw=result.model_dump(mode='json',exclude={'trace'})
        atomic_json(directory/'official_result.json',raw)
        atomic_bytes(directory/'official_phase2.log',(result.test_output or '').encode())
        j.patch(result.agent_patch or '',source='official_task_result')
        if result.trace is not None:
            atomic_json(directory/'official_trace.json',result.trace.to_dict())
        atomic_json(directory/'official_result_serialization.json',dict(
            method='TaskResult.model_dump(mode=json, exclude={trace})',trace_exported_separately=True))
    except BaseException as exc:
        atomic_json(directory/'worker_exception.json',dict(type=type(exc).__name__,message=str(exc),
            traceback=traceback.format_exc(),official_result_missing=True))
        raise
    finally:
        if ctx.submitted_patch is not None: j.patch(ctx.submitted_patch,source='worker_finally')
        j.stage('cleanup')
        manager.cleanup_all()
        handler.flush(); handler.close()
        # The manager may ignore filesystem deletion failures; verify the directories.
        remaining=list((directory/'sandbox_tmp').glob('swegemma_sandbox_*'))
        atomic_json(directory/'worker_done.json',dict(cleanup_complete=not manager.sandboxes and not remaining,
            remaining_sandbox_directories=[str(p) for p in remaining]))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec',type=Path)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    args.directory.mkdir(parents=True,exist_ok=True)
    # Imports/compile failures also leave an explicit record, never an official failure.
    try:
        Journal(args.directory).stage('prepare_agent',operation='worker_bootstrap')
        asyncio.run(evaluate(json.loads(args.spec.read_text(encoding='utf-8')),args.directory))
    except BaseException as exc:
        atomic_json(args.directory/'worker_top_exception.json',dict(type=type(exc).__name__,message=str(exc),
            traceback=traceback.format_exc()))
        raise


if __name__=='__main__': main()
