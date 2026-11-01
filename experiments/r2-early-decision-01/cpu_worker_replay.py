"""Deterministic localhost tool replay; no real model and no repair-capability evidence."""
import asyncio,http.server,json,tarfile,threading,time
from pathlib import Path
from r2a_runtime import HERE,write

async def run(out):
    import torch
    assert torch.cuda.device_count()==0
    issue=json.loads((HERE/'ISSUES.agent.json').read_bytes())[0]
    ident=issue['instance_id'];snapshot=HERE/'assets/snapshots'/(ident+'.tgz')
    with tarfile.open(snapshot) as t:
        target=next(m for m in t.getmembers() if m.name.endswith('xarray/__init__.py'))
        original=t.extractfile(target).read().decode();relative='xarray/__init__.py'
    sequence=[('edit_file',dict(filepath=relative,old_string=original,new_string=original+'\n# CPU wiring replay marker only; not a repair.\n')),('run_command',dict(command='python3 -m py_compile xarray/__init__.py')),('submit_patch',{})]
    calls=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));assert body['model']=='SIMULATED_CPU_NO_MODEL'
            k=len(calls);calls.append(dict(index=k,model=body['model']))
            if k<len(sequence):
                name,args=sequence[k];message=dict(role='assistant',content=None,tool_calls=[dict(id='cpu_fixture_'+str(k),type='function',function=dict(name=name,arguments=json.dumps(args)))])
                finish='tool_calls'
            else:message=dict(role='assistant',content='CPU wiring replay complete.');finish='stop'
            payload=dict(id='cpu-wiring-'+str(k),object='chat.completion',created=1,model='SIMULATED_CPU_NO_MODEL',choices=[dict(index=0,message=message,finish_reason=finish)])
            raw=json.dumps(payload).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',8000),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        # Pure host-controller boundary contract. No server/model is started.
        from unittest.mock import patch
        import gemma_pair.coordinator as prior
        import harness_v2.supervisor as supervision
        import r2a_coordinator
        async def scheduler_probe(directory,started,plan):
            expected=json.loads((HERE/'EXECUTION_PLAN.json').read_bytes())['sessions']
            assert plan['order']==[(r['task'],r['candidate']) for r in expected] and len(plan['order'])==8
            observed=supervision.supervise('CPU_CONTRACT_ONLY',stage_caps=dict(verification=240))
            assert observed['stage_caps']['verification']==600 and observed['outer_seconds']==1680
        with patch.object(prior,'run',scheduler_probe),patch.object(supervision,'supervise',lambda *a,**k:k):
            await r2a_coordinator.run(Path(out)/'coordinator-contract',time.monotonic())
        from r2a_worker import run as worker
        version=next(r['version'] for r in json.loads((HERE/'TASK_IDENTITY_LOCK.json').read_bytes())['rows'] if r['instance_id']==ident)
        spec=dict(binding=dict(issue=issue,snapshot=str(snapshot),wheels=str(HERE/'assets/wheels'),version=version),candidate='A',model_path='SIMULATED_CPU_NO_MODEL',CPU_simulation=True,new_explicit_GPU_authorization=False)
        await worker(spec,out)
        row=json.loads((Path(out)/'SESSION_RESULT.json').read_bytes())
        events=[json.loads(l) for l in (Path(out)/'events.jsonl').read_text().splitlines()]
        assert row['model_transport']=='CPU_SCRIPTED_NOT_REPAIR_EVIDENCE' and row['patch_submitted'] and row['patch_bytes']>0 and row['cleanup']
        assert row['sdk_native_resolved'] is False
        assert row['independent_test_pass'] is False and row['evidence_complete']
        assert row['evaluation']['sdk_native']['verification_source_guard']['unchanged']
        assert any(e.get('first_production_edit_observed') for e in events)
        write(Path(out)/'CPU_REPLAY_CONTRACT.json',dict(status='PASS_PLUMBING_ONLY',real_Gemma_requests=0,GPU_devices=0,repair_capability_evidence=False,marker_patch_is_not_a_fix=True,native_repair=False,localhost_mock_requests=len(calls),missing_usage='UNKNOWN',source_change_observer=True,submit_capture=True,native_evaluator=True,cleanup=True))
    finally:server.shutdown();server.server_close();thread.join(timeout=5)

if __name__=='__main__':
    import sys
    asyncio.run(run(sys.argv[1]))
