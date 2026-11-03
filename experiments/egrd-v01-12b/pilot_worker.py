"""One fresh official SDK context/workspace, then independent native verification."""
import asyncio,json,sys,time
from pathlib import Path
import runtime_adapter
runtime_adapter.install()
from hardened_runtime import SubprocessManager,DurableContext as ParentContext
from harness_v2.evidence import Journal
from swegemma.models import Task
from swegemma.harness.agent_runner import run_agent_sandbox
from s1.infrastructure_recovery.wire import observe_http,audit_requests
from r2a_runtime import context_config,native_verify,write,sha,HERE
class Context(ParentContext):
    def stop_agent_session(self):
        super().stop_agent_session();box=self.docker.sandboxes.get(self.container_id)
        if box:
            state=box['root']/'tmp/egrd-v01/state.json'
            if state.is_file() and not state.is_symlink() and state.resolve().is_relative_to(box['root'].resolve()) and state.stat().st_size<=8*1024*1024:
                write(self.journal.directory/'EGRD_STATE.json',json.loads(state.read_bytes()))
async def run(spec,out):
    start=time.monotonic();out=Path(out);out.mkdir(parents=True,exist_ok=True);binding=spec['binding'];issue=binding['issue'];journal=Journal(out)
    simulation=spec.get('CPU_simulation') is True
    if simulation:
        import torch
        assert torch.cuda.device_count()==0 and spec['model_path']=='SIMULATED_CPU_NO_MODEL' and not spec['real_Gemma']
    else:assert spec['real_Gemma'] and spec['authorized_GPU_pilot']
    cfg,agent=context_config(spec['candidate'],out,binding['snapshot'],HERE/'ISSUES.agent.json',binding['wheels'],spec['model_path'])
    write(out/'CONFIGURATION.json',dict(candidate=spec['candidate'],model_alias=spec['model_alias'],model_path=spec['model_path'],generation=agent.generate_content_config.model_dump(mode='json',exclude_none=True),main_agents=1,base_tools=[getattr(t,'__name__',type(t).__name__) for t in agent.tools],instruction_sha256=sha(agent.instruction.encode()),budget_seconds=300,tools=60,turns=80))
    manager=SubprocessManager(journal=journal,base_dir=out/'roots',task_wheels=Path(binding['wheels']),timeout_seconds=120,project_version=binding['version'])
    task=Task(**issue);assert not task.patch and not task.test_patch and not task.hints_text
    ctx=Context(journal=journal,docker_manager=manager,task=task,budget=cfg.budget,harness=cfg.harness);manager.context=ctx
    try:
        with observe_http(out/'model_transport'):patch,error,trace=await run_agent_sandbox(manager,cfg,task,Path(binding['snapshot']),context=ctx)
        journal.stage('save_patch');write(out/'native_trace.json',trace.to_dict() if trace else {})
        label='submitted' if ctx.patch_submitted else 'fallback';(out/(label+'.patch')).write_text(patch)
        manager.cleanup_all();assert not manager.sandboxes and all(not Path(e['lease']).exists() for e in manager.entries)
        deadline=str(error or '').startswith('Agent exceeded session timeout') and ctx.agent_elapsed_seconds>=299
        audit=audit_requests(out/'model_transport',deadline_evidence=dict(official_agent_deadline=deadline,cleanup_verified=True,cutoff_monotonic=ctx.agent_start_time+300 if deadline else None))
        journal.stage('verification')
        trusted=next(t for t in json.loads((HERE/'TRUSTED_TEST_SPEC.private.json').read_bytes()) if t['instance_id']==task.instance_id)
        native=await native_verify(issue,trusted,binding['snapshot'],binding['wheels'],out/'trusted',patch)
        row=dict(task_id=task.instance_id,candidate=spec['candidate'],model_alias=spec['model_alias'],model_transport='CPU_SCRIPTED_NOT_REPAIR_EVIDENCE' if simulation else 'REAL_GEMMA',patch_bytes=len(patch.encode()),patch_submitted=ctx.patch_submitted,patch_kind=label,agent_seconds=ctx.agent_elapsed_seconds,agent_error=error,charged_tools=ctx.tool_calls_used,llm_calls=ctx.llm_calls_used,http_audit=audit,evidence_complete=audit['passed'],cleanup=True,worker_seconds=time.monotonic()-start,infrastructure_stop=ctx.stop_receipt(),evaluation=dict(sdk_native=native),native_resolved=native['resolved'],semantic_review='REQUIRED_SEPARATELY',EGRD_state_recorded=(out/'EGRD_STATE.json').exists())
        write(out/'SESSION_RESULT.json',row);journal.stage('persist');write(out/'worker_done.json',dict(cleanup_complete=True))
    finally:
        manager.cleanup_all();journal.stage('cleanup');write(out/'CLEANUP.json',dict(complete=not manager.sandboxes,records=manager.cleanup_records))
if __name__=='__main__':asyncio.run(run(json.loads(Path(sys.argv[1]).read_bytes()),sys.argv[2]))
