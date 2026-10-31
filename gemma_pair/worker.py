import asyncio
import json
from pathlib import Path
import sys
import time
import traceback

from harness_v2.evidence import Journal
from harness_v2.official import DurableContext
from swegemma.models import Task
from swegemma.harness.agent_runner import run_agent_sandbox
from s1.infrastructure_recovery.wire import observe_http
from .common import package,config,write,sha
from .sandbox import SubprocessManager
from .evaluate import evaluate

async def run(spec,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);journal=Journal(out);started=time.monotonic()
    binding=spec['binding'];name=spec['candidate'];candidate=out/'candidate'
    registry,limits,constraints,compiled,budget=package(name,candidate,spec['model_path'])
    cfg=config(candidate,registry,limits,constraints,budget,binding['taskfile'],binding['snapshot'],binding['wheels'],out)
    write(out/'CONFIGURATION.json',dict(candidate=name,budget=budget,actual_budget=str(cfg.budget),
        generation=compiled.generate_content_config.model_dump(mode='json',exclude_none=True),
        tools=[t.__name__ for t in compiled.tools],events_compaction=str(cfg.events_compaction_config),
        instruction_sha256=sha(compiled.instruction.encode()),additional_Context_Guard=False,
        serving_equivalence_to_historical_submission='UNVERIFIED'))
    manager=SubprocessManager(journal=journal,base_dir=out/'agent-roots',task_wheels=Path(binding['wheels']),
                              timeout_seconds=budget['timeout_seconds'])
    task=Task(**binding['issue']);assert not task.test_patch and not task.hints_text
    context=DurableContext(journal=journal,docker_manager=manager,task=task,budget=cfg.budget,harness=cfg.harness)
    manager.context=context
    result=dict(task_id=task.instance_id,candidate=name,cleanup=False,official_native_resolved=None,
                canonical_swebench_resolved=None,model_transport='SIMULATED_CPU' if spec.get('CPU_simulation') is True else 'REAL_GEMMA')
    try:
        with observe_http(out/'model_transport'):
            patch,error,trace=await run_agent_sandbox(manager,cfg,task,Path(binding['snapshot']),context=context)
        journal.stage('save_patch')
        if trace is not None:write(out/'native_trace.json',trace.to_dict())
        label='submitted' if context.patch_submitted else 'fallback'
        (out/(label+'.patch')).write_text(patch,encoding='utf8')
        result.update(agent_error=error,patch_submitted=context.patch_submitted,patch_bytes=len(patch.encode()),
            patch_kind=label,patch_sha256=sha(patch.encode()) if patch else None,
            agent_seconds=context.agent_elapsed_seconds,charged_tools=context.tool_calls_used,
            llm_calls=context.llm_calls_used)
        write(out/'AGENT_RESULT.json',result)
        manager.cleanup_all()
        assert not manager.sandboxes and all(not Path(e['lease']).exists() for e in manager.entries)
        journal.stage('verification')
        # Native retained fallback is evaluated too, retaining its separate label.
        checked=evaluate(binding,out/'trusted',patch if patch else None)
        result.update(evaluation=checked,cleanup=checked['cleanup'],worker_seconds=time.monotonic()-started)
        write(out/'SESSION_RESULT.json',result)
        assert checked['cleanup']
        journal.stage('persist');write(out/'worker_done.json',dict(cleanup_complete=True))
    except BaseException as exc:
        write(out/'WORKER_EXCEPTION.json',dict(type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()))
        raise
    finally:
        journal.stage('cleanup');manager.cleanup_all()
        write(out/'AGENT_CLEANUP.json',dict(complete=not manager.sandboxes,
            leases_removed=all(not Path(e['lease']).exists() for e in manager.entries),records=manager.cleanup_records))

if __name__=='__main__':asyncio.run(run(json.loads(Path(sys.argv[1]).read_bytes()),sys.argv[2]))
