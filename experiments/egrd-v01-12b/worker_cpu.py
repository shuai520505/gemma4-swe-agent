"""One comment-only plumbing session, not a development repair or model result."""
import asyncio,http.server,json,tarfile,threading
from pathlib import Path
import r2a_runtime
from pilot_worker import run
D=Path(__file__).resolve().parent
async def main(out):
    issue=next(i for i in json.loads((r2a_runtime.HERE/'ISSUES.agent.json').read_bytes()) if i['instance_id']=='sympy__sympy-24661')
    snapshot=r2a_runtime.HERE/'assets/snapshots/sympy__sympy-24661.tgz'
    with tarfile.open(snapshot) as t:
        m=next(m for m in t.getmembers() if m.name.endswith('sympy/__init__.py'));original=t.extractfile(m).read().decode();first=''.join(original.splitlines(keepends=True)[:4]);assert original.count(first)==1
    init=dict(op='init',issue_id=issue['instance_id'],original=issue['problem_statement'],model_id='SIMULATED_CPU_NO_MODEL',requirements=[dict(id='R1',text=issue['problem_statement'].splitlines()[0],status='OBSERVED')])
    actions=[('load_skill',dict(skill_name='egrd-repair')),('run_skill_script',dict(skill_name='egrd-repair',file_path='scripts/egrd.py',args=dict(request=json.dumps(init)))),('edit_file',dict(filepath='sympy/__init__.py',old_string=first,new_string='# CPU transport marker only, not a repair.\n'+first)),('submit_patch',{}),'End.']
    calls=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));assert body['model']=='SIMULATED_CPU_NO_MODEL';k=len(calls);calls.append(k);a=actions[k] if k<len(actions) else 'End.'
            if isinstance(a,tuple):message=dict(role='assistant',content=None,tool_calls=[dict(id='worker_cpu_'+str(k),type='function',function=dict(name=a[0],arguments=json.dumps(a[1])))])
            else:message=dict(role='assistant',content=a)
            payload=dict(id='worker_cpu'+str(k),object='chat.completion',created=1,model=body['model'],choices=[dict(index=0,message=message,finish_reason='tool_calls' if isinstance(a,tuple) else 'stop')],usage=dict(prompt_tokens=1,completion_tokens=1,total_tokens=2));raw=json.dumps(payload).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',8000),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        spec=dict(binding=dict(issue=issue,snapshot=str(snapshot),wheels=str(r2a_runtime.HERE/'assets/wheels'),version='1.12'),candidate='B',model_alias='gemma-4-12b-it-qat-w4a16-ct',model_path='SIMULATED_CPU_NO_MODEL',real_Gemma=False,CPU_simulation=True,authorized_GPU_pilot=False)
        await run(spec,out);row=json.loads((Path(out)/'SESSION_RESULT.json').read_bytes())
        assert row['model_transport']=='CPU_SCRIPTED_NOT_REPAIR_EVIDENCE' and not row['native_resolved'] and row['patch_submitted'] and row['patch_bytes'] and row['evidence_complete'] and row['cleanup'] and row['EGRD_state_recorded']
        from stop_policy import admission
        from r2a_coordinator import admission as legacy
        assert admission(row,dict(allow_next_run=True),legacy)=='CONTINUE'
        r2a_runtime.write(Path(out)/'WORKER_CPU_ACCEPTANCE.json',dict(status='PASS_PLUMBING_ONLY',comment_patch_not_a_repair=True,official_SDK_resolved=False,scripted_requests=len(calls),real_Gemma_requests=0,GPU=0))
    finally:server.shutdown();server.server_close();thread.join(timeout=5)
if __name__=='__main__':
    import sys
    asyncio.run(main(sys.argv[1]))
