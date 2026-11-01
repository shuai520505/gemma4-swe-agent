"""Genuine official SDK + nonroot Linux, scripted localhost only; no repairs."""
import asyncio,http.server,json,shlex,threading
from pathlib import Path
from unittest.mock import patch
import r2a_runtime
from hardened_runtime import SubprocessManager,DurableContext
from stop_policy import admission
from swegemma.models import Task
from swegemma.harness.agent_runner import run_agent_sandbox
from harness_v2.evidence import Journal

async def main(out):
    import torch
    assert torch.cuda.device_count()==0
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    issue=next(x for x in json.loads((r2a_runtime.HERE/'ISSUES.agent.json').read_bytes()) if x['repo']=='sphinx-doc/sphinx')
    snapshot=r2a_runtime.HERE/'assets/snapshots'/(issue['instance_id']+'.tgz')
    rows=[]
    fixtures=[('ordinary_assertion',"python3 -c "+shlex.quote("raise AssertionError('CPU ordinary failure fixture')"),False),
      ('missing_cli',"PATH=/definitely-absent sphinx-build --version",True),
      ('invalid_locale',"LC_ALL=definitely_invalid_locale python3 -c "+shlex.quote("import locale;locale.setlocale(locale.LC_ALL,'')"),True),
      ('preflight_missing_cli',None,True)]
    for label,command,stop in fixtures:
        directory=out/label;directory.mkdir();calls=[]
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));assert body['model']=='SIMULATED_CPU_NO_MODEL'
                k=len(calls);calls.append(dict(index=k,model=body['model']))
                if k==0:name,args='run_command',dict(command=command)
                else:name,args='run_command',dict(command='printf CPU_CONTINUATION_REACHED')
                message=dict(role='assistant',content=None,tool_calls=[dict(id='cpu_'+str(k),type='function',function=dict(name=name,arguments=json.dumps(args)))])
                raw=json.dumps(dict(id='cpu-response-'+str(k),object='chat.completion',created=1,model='SIMULATED_CPU_NO_MODEL',choices=[dict(index=0,message=message,finish_reason='tool_calls')],usage=dict(prompt_tokens=1,completion_tokens=1,total_tokens=2))).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        server=http.server.ThreadingHTTPServer(('127.0.0.1',8000),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        cfg,_=r2a_runtime.context_config('R2',directory,snapshot,r2a_runtime.HERE/'ISSUES.agent.json',r2a_runtime.HERE/'assets/wheels','SIMULATED_CPU_NO_MODEL')
        manager=SubprocessManager(journal=Journal(directory),base_dir=directory/'roots',task_wheels=r2a_runtime.HERE/'assets/wheels',timeout_seconds=240,project_version='7.1')
        class FixtureContext(DurableContext):
            def handle_adk_event(self,event,agent_name=None):
                super().handle_adk_event(event,agent_name=agent_name)
                for part in (event.model_dump(mode='json',exclude_none=True).get('content') or {}).get('parts',[]):
                    response=part.get('function_response') or {}
                    body=response.get('response') or {}
                    if 'CPU_CONTINUATION_REACHED' in str(body.get('stdout','')):
                        raise RuntimeError('CPU_CONTROL_TERMINAL_AFTER_CONFIRMED_CONTINUATION')
        ctx=FixtureContext(journal=manager.journal,docker_manager=manager,task=Task(**issue),budget=cfg.budget,harness=cfg.harness);manager.context=ctx
        # Negative admission fixture removes only the newly generated wrapper
        # from this owned sandbox, before source admission. No task source edits.
        original_start=manager.start
        def broken_start():
            sid=original_start();(manager.sandboxes[sid]['root']/'usr/local/bin/sphinx-build').unlink();return sid
        try:
            with patch.object(manager,'start',broken_start if command is None else original_start):
                patch_text,error,trace=await run_agent_sandbox(manager,cfg,Task(**issue),snapshot,context=ctx)
            assert not patch_text,'CPU fixture must not modify production'
            receipt=ctx.stop_receipt();assert receipt['stopped']==stop,(label,receipt,error)
            assert len(calls)==(0 if command is None else 1 if stop else 2),(label,calls)
            assert not ctx.patch_submitted,(label,'unexpected submit')
            from r2a_coordinator import admission as legacy
            row=dict(infrastructure_stop=receipt)
            actual=admission(row,{},lambda r,o:'CONTINUE');assert actual==('STOP' if stop else 'CONTINUE')
            # Real deployment admission blocks suffix and preserves NOT_RUN;
            # do not start the synthetic second-session callback after STOP.
            dispatched=[label];not_run=[]
            if actual=='STOP':not_run=['synthetic_suffix']
            else:dispatched.append('synthetic_suffix')
            if trace is not None:r2a_runtime.write(directory/'native_trace.json',trace.to_dict())
            rows.append(dict(case=label,status='PASS',stop_latched=stop,localhost_scripted_requests=len(calls),next_model_request_blocked=stop,preflight_blocked_before_requests=command is None,explicit_submit=ctx.patch_submitted,agent_error=error,patch_bytes=len(patch_text),suffix_not_run=not_run,source_changes=[e for e in manager.production_observations if e['changed_files']],receipt=receipt))
        finally:
            manager.cleanup_all();server.shutdown();server.server_close();thread.join(timeout=5)
            assert not manager.sandboxes and all(not Path(e['lease']).exists() for e in manager.entries)
            r2a_runtime.write(directory/'CLEANUP.json',dict(complete=True,records=manager.cleanup_records))
    # Host composition test executes actual composed entry, intercepting only
    # GPU-owning parent call; never starts a model server on CPU.
    import hardened_coordinator,gemma_pair.coordinator as prior,r12_final_cpu
    async def parent_probe(out,started,plan):
        assert plan['worker_module']=='hardened_worker'
        assert r12_final_cpu.admission(dict(infrastructure_stop=dict(coverage='LIVE_ADK_TOOL_RESPONSES_V1',stopped=True)),dict(allow_next_run=True))=='STOP'
    import time
    with patch.object(prior,'run',parent_probe):await hardened_coordinator.run(out/'coordinator-composition',time.monotonic())
    r2a_runtime.write(out/'CPU_INTEGRATION_RESULTS.json',dict(status='PASS',GPU_devices=0,real_model_requests=0,repair_capability_evidence=False,rows=rows,coordinator_composition='PASS',scope='Scripted SDK plumbing + actual source CLI and nonroot environment, not candidate repair rerun'))
    print('CPU_HARDENING_PASS',flush=True)
if __name__=='__main__':
    import sys
    asyncio.run(main(sys.argv[1]))
