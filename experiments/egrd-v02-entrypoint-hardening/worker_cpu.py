"""Scripted public Requests plumbing; comment-only patch is not repair evidence."""
import asyncio,http.server,json,tarfile,threading
from pathlib import Path
from pilot_worker import run
from result_contract import dump,native_execution_check
D=Path(__file__).resolve().parent
async def main(out):
 plan=json.loads((D/'SMOKE_TASK_LOCK.json').read_bytes());lock=plan['tasks'][0]
 issue=next(r for r in json.loads((D/'ISSUES.agent.json').read_bytes()) if r['instance_id']==lock['instance_id'])
 root=next((p for p in [Path('/kaggle/input/competitions/gemma-4-developer-agent'),Path('/kaggle/input/gemma-4-developer-agent')] if (p/'tasks.jsonl').is_file()),None)
 assert root
 snapshot=root/'snapshots'/lock['snapshot_file']
 with tarfile.open(snapshot) as t:
  member=next(m for m in t.getmembers() if m.name.endswith('/requests/__init__.py'))
  file=member.name.removeprefix('./');original=t.extractfile(member).read().decode();first=''.join(original.splitlines(keepends=True)[:4]);assert original.count(first)==1
 init=dict(op='init',issue_id=issue['instance_id'],original=issue['problem_statement'],model_id='SIMULATED_CPU_NO_MODEL',requirements=[dict(id='R1',text=issue['problem_statement'].splitlines()[0],status='OBSERVED')])
 for field in ['expected_behavior','actual_behavior','inputs_outputs','boundaries','acceptance_criteria','unresolved_questions']:init[field]=[dict(text='Not established in this comment-only fixture.',status='UNVERIFIED')]
 actions=[('load_skill',dict(skill_name='egrd-repair')),('run_skill_script',dict(skill_name='egrd-repair',file_path='scripts/egrd.py',args=dict(request=json.dumps(init)))),('edit_file',dict(filepath=file,old_string=first,new_string='# CPU transport marker, not an Issue repair.\n'+first)),('submit_patch',{}),'End.'];calls=[]
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_POST(self):
   body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));assert body['model']=='SIMULATED_CPU_NO_MODEL';i=len(calls);calls.append(i);action=actions[i] if i<len(actions) else 'End.'
   if isinstance(action,tuple):message=dict(role='assistant',content=None,tool_calls=[dict(id='cpu'+str(i),type='function',function=dict(name=action[0],arguments=json.dumps(action[1])))])
   else:message=dict(role='assistant',content=action)
   response=dict(id='cpu'+str(i),object='chat.completion',created=1,model=body['model'],choices=[dict(index=0,message=message,finish_reason='tool_calls' if isinstance(action,tuple) else 'stop')],usage=dict(prompt_tokens=1,completion_tokens=1,total_tokens=2));raw=json.dumps(response).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',8000),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  import r2a_runtime
  spec=dict(candidate='B',model_alias='gemma-4-12b-it-qat-w4a16-ct',model_path='SIMULATED_CPU_NO_MODEL',real_Gemma=False,CPU_simulation=True,binding=dict(issue=issue,snapshot=str(snapshot),wheels=str(r2a_runtime.HERE/'assets/wheels'),agent_tasks=str(D/'ISSUES.agent.json'),public_tasks=str(root/'tasks.jsonl'),test_patch_sha256=lock['public_evaluator_test_patch_sha256']))
  await run(spec,out);row=json.loads((Path(out)/'SESSION_RESULT.json').read_bytes())
  assert row['model_transport']=='CPU_SCRIPTED_NOT_REPAIR_EVIDENCE' and row['native_resolved'] is False and row['patch_submitted'] and row['patch_bytes']>0
  assert row['activation']['activated'] and row['activation']['state_issue_hash_matches']
  assert json.loads((Path(out)/'CLEANUP.json').read_bytes())['complete']
  integrity=native_execution_check(Path(out)/'trusted/NATIVE_RESULT.json')
  dump(Path(out)/'NATIVE_EXECUTION_INTEGRITY.json',integrity)
  assert integrity['passed'],'Native setup errors are not a valid negative repair control'
  dump(Path(out)/'WORKER_CPU_ACCEPTANCE.json',dict(status='PASS_PLUMBING_ONLY',negative_control_comment_patch_resolved=False,scripted_requests=len(calls),real_Gemma_requests=0,GPU=0))
 finally:server.shutdown();server.server_close();thread.join(timeout=5)
if __name__=='__main__':
 import sys
 asyncio.run(main(sys.argv[1]))
