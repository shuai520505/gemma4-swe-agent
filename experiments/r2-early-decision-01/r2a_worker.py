"""Independent Session using existing official Runner, wire observer and cleanup."""
import asyncio,json,sys,time,traceback
from pathlib import Path
from harness_v2.evidence import Journal
from harness_v2.official import DurableContext
from swegemma.models import Task
from swegemma.harness.agent_runner import run_agent_sandbox
from s1.infrastructure_recovery.wire import observe_http,audit_requests
from r2a_runtime import HERE,SubprocessManager,context_config,native_verify,sha,write

async def run(spec,out):
    simulation=spec.get('CPU_simulation') is True
    if simulation:
        import torch
        assert torch.cuda.device_count()==0 and spec['model_path']=='SIMULATED_CPU_NO_MODEL'
    else:assert spec['new_explicit_GPU_authorization'] is True
    out=Path(out);out.mkdir(parents=True,exist_ok=True);journal=Journal(out)
    binding=spec['binding'];issue=binding['issue'];name=spec['candidate'];start=time.monotonic()
    cfg,agent=context_config(name,out,binding['snapshot'],HERE/'ISSUES.agent.json',binding['wheels'],spec['model_path'])
    write(out/'CONFIGURATION.json',dict(candidate=name,instruction_sha256=sha(agent.instruction.encode()),generation=agent.generate_content_config.model_dump(mode='json',exclude_none=True),tools=[t.__name__ for t in agent.tools],budget=str(cfg.budget)))
    manager=SubprocessManager(journal=journal,base_dir=out/'roots',task_wheels=Path(binding['wheels']),timeout_seconds=240,project_version=binding['version'])
    task=Task(**issue);assert not task.patch and not task.test_patch and not task.hints_text
    context=DurableContext(journal=journal,docker_manager=manager,task=task,budget=cfg.budget,harness=cfg.harness);manager.context=context
    result=dict(task_id=task.instance_id,candidate=name,model_transport='CPU_SCRIPTED_NOT_REPAIR_EVIDENCE' if simulation else 'REAL_GEMMA',official_native_resolved=None,canonical_swebench_resolved=None)
    try:
        with observe_http(out/'model_transport'):
            patch,error,trace=await run_agent_sandbox(manager,cfg,task,Path(binding['snapshot']),context=context)
        journal.stage('save_patch')
        if trace is not None:write(out/'native_trace.json',trace.to_dict())
        label='submitted' if context.patch_submitted else 'fallback';(out/(label+'.patch')).write_text(patch,encoding='utf8')
        result.update(agent_error=error,patch_submitted=context.patch_submitted,patch_bytes=len(patch.encode()),patch_kind=label,patch_sha256=sha(patch.encode()) if patch else None,agent_seconds=context.agent_elapsed_seconds,charged_tools=context.tool_calls_used,llm_calls=context.llm_calls_used)
        manager.cleanup_all();assert not manager.sandboxes and all(not Path(e['lease']).exists() for e in manager.entries)
        deadline=str(error or '').startswith('Agent exceeded session timeout') and context.agent_elapsed_seconds>=479
        http_audit=audit_requests(out/'model_transport',deadline_evidence=dict(official_agent_deadline=deadline,cleanup_verified=True,cutoff_monotonic=context.agent_start_time+480 if deadline else None))
        expected_files=('events.jsonl','adk_events.jsonl','native_trace.json',label+'.patch','model_transport/http_wire.jsonl','model_transport/http_lifecycle.jsonl')
        missing=[n for n in expected_files if not (out/n).is_file()]
        reasons=[r for r in http_audit['reasons'] if not (simulation and r=='missing_response_usage')]
        evidence_complete=not missing and not reasons
        write(out/'HTTP_EVIDENCE_AUDIT.json',dict(http_audit,CPU_simulation=simulation,missing_files=missing,missing_usage='UNKNOWN' if not http_audit['usage_complete'] else None,evidence_complete=evidence_complete))
        journal.stage('verification')
        trusted=next(t for t in json.loads((HERE/'TRUSTED_TEST_SPEC.private.json').read_bytes()) if t['instance_id']==task.instance_id)
        checked=await native_verify(issue,trusted,binding['snapshot'],binding['wheels'],out/'trusted',patch)
        result.update(sdk_native_resolved=checked['resolved'],independent_test_pass=checked.get('independent_exact',{}).get('status')=='INDEPENDENT_TEST_PASS' and bool((checked.get('verification_source_guard') or {}).get('unchanged')),evidence_complete=evidence_complete,http_audit=http_audit,semantic_review='PENDING',cleanup=True,worker_seconds=time.monotonic()-start,
            evaluation=dict(sdk_native=checked,scoped_development_pass=None,legacy_field_not_a_repair_claim=True))
        write(out/'SESSION_RESULT.json',result);journal.stage('persist');write(out/'worker_done.json',dict(cleanup_complete=True))
    except BaseException as exc:
        write(out/'WORKER_EXCEPTION.json',dict(type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()));raise
    finally:
        journal.stage('cleanup');manager.cleanup_all()
        write(out/'AGENT_CLEANUP.json',dict(complete=not manager.sandboxes,leases_removed=all(not Path(e['lease']).exists() for e in manager.entries),records=manager.cleanup_records))

if __name__=='__main__':asyncio.run(run(json.loads(Path(sys.argv[1]).read_bytes()),sys.argv[2]))
