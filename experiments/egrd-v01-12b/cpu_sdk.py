"""Owned fixture through actual official SkillToolset and nonroot sandbox."""
import asyncio,http.server,json,shlex,tarfile,threading,io
from pathlib import Path
from hardened_runtime import SubprocessManager,DurableContext as PriorContext
from harness_v2.evidence import Journal
from swegemma.models import Task
from swegemma.config import EvalConfig,build_submission_limits
from swegemma.harness.agent_runner import run_agent_sandbox
from adk_submission import ModelRegistry
from google.adk.models.lite_llm import LiteLlm
import r2a_runtime
D=Path(__file__).resolve().parent
def write(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
async def main(out):
    import torch
    assert torch.cuda.device_count()==0
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    bad='def f(x):\n    return x > 0\n';good=bad.replace('> 0','>= 0')
    snapshot=out/'owned.tgz'
    with tarfile.open(snapshot,'w:gz') as t:
        for name,text in [('logic.py',bad),('README.md','Owned CPU fixture only.')]:
            b=text.encode();m=tarfile.TarInfo(name);m.size=len(b);m.mode=0o644;t.addfile(m,io.BytesIO(b))
    reqs=[dict(id='R1',text='Accept zero.',status='OBSERVED'),dict(id='R2',text='Negative values remain false.',status='OBSERVED')]
    def skill(op,**kw):return ('run_skill_script',dict(skill_name='egrd-repair',file_path='scripts/egrd.py',args=dict(request=json.dumps(dict(op=op,**kw)))))
    check='from logic import f\nassert f(0)\nassert not f(-1)\n'
    actions=[('load_skill',dict(skill_name='egrd-repair')),
      skill('init',issue_id='owned-zero',original='Accept zero. Negative values remain false.',model_id='SIMULATED_CPU_NO_MODEL',requirements=reqs),
      skill('source',name='logic.py',start=1,end=2,requirements=['R1','R2']),
      skill('hypothesis',location='logic.py:f',mechanism='strict comparison excludes zero',support=['E1'],contradictions=[],prediction='f(0) false before true after',confidence=.8,next_experiment='assert f(0)',requirements=['R1']),
      skill('intent',files=['logic.py'],regions=['f'],behavior='accept zero',requirements=['R1','R2'],support=['E1'],regressions=['negative'],preserve='negative false',discriminating_test='assert f(0) and not f(-1)'),
      ('edit_file',dict(filepath='logic.py',old_string=bad,new_string=good)),skill('record_patch'),
      ('run_command',dict(command='python3 -c '+shlex.quote('from pathlib import Path;Path("/tmp/egrd-check.py").write_text('+repr(check)+')'))),
      skill('check',path='/tmp/egrd-check.py',requirements=['R1','R2'],purpose='TARGET',seconds=5),
      skill('check',path='/tmp/egrd-check.py',requirements=['R1','R2'],purpose='REGRESSION',seconds=5),skill('review'),skill('accept'),
      ('edit_file',dict(filepath='logic.py',old_string=good,new_string=good.replace('>= 0','<= 0'))),skill('accept'),
      ('edit_file',dict(filepath='logic.py',old_string=good.replace('>= 0','<= 0'),new_string=good)),skill('review'),skill('accept'),('submit_patch',{}),'End.']
    calls=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_POST(self):
            b=json.loads(self.rfile.read(int(self.headers['Content-Length'])));assert b['model']=='SIMULATED_CPU_NO_MODEL'
            k=len(calls);calls.append(dict(index=k));a=actions[k] if k<len(actions) else 'End.'
            if isinstance(a,tuple):message=dict(role='assistant',content=None,tool_calls=[dict(id='owned_'+str(k),type='function',function=dict(name=a[0],arguments=json.dumps(a[1])))])
            else:message=dict(role='assistant',content=a)
            payload=dict(id='cpu'+str(k),object='chat.completion',created=1,model=b['model'],choices=[dict(index=0,message=message,finish_reason='tool_calls' if isinstance(a,tuple) else 'stop')],usage=dict(prompt_tokens=1,completion_tokens=1,total_tokens=2))
            raw=json.dumps(payload).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',8000),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    registry=ModelRegistry();registry.register('gemma-4-12b-it-qat-w4a16-ct',LiteLlm(model='openai/SIMULATED_CPU_NO_MODEL',api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
    limits,constraints=build_submission_limits();task=Task(instance_id='owned-zero',repo='test/mock_repo',base_commit='123456',problem_statement='Accept zero. Negative values remain false.')
    cfg=EvalConfig(tasks_path=out/'unused.jsonl',snapshots_dir=out,results_dir=out/'harness',submission_dir=D/'packages/B',models=registry,sandbox='subprocess',wheels_dir=r2a_runtime.HERE/'assets/wheels',max_time_minutes=5,max_tool_calls=60,max_turns=80,timeout_seconds=120,verification_timeout_seconds=300,limits=limits,generation_constraints=constraints,display_mode='quiet')
    manager=SubprocessManager(journal=Journal(out),base_dir=out/'roots',task_wheels=r2a_runtime.HERE/'assets/wheels',timeout_seconds=120,project_version='1.0')
    class Context(PriorContext):
        def stop_agent_session(self):
            super().stop_agent_session()
            box=self.docker.sandboxes.get(self.container_id)
            if box:
                p=box['root']/'tmp/egrd-v01/state.json'
                if p.is_file():write(out/'RECOVERED_STATE.json',json.loads(p.read_bytes()))
    ctx=Context(journal=manager.journal,docker_manager=manager,task=task,budget=cfg.budget,harness=cfg.harness);manager.context=ctx
    try:
        patch,error,trace=await run_agent_sandbox(manager,cfg,task,snapshot,context=ctx)
        if trace:write(out/'native_trace.json',trace.to_dict())
        (out/'owned.patch').write_text(patch)
        state=json.loads((out/'RECOVERED_STATE.json').read_bytes());assert state['phase']=='PATCH_ACCEPTED',state['phase']
        assert any(e['type']=='TEST_RESULT' and e['verification']=='PASS' for e in state['evidence'])
        assert ctx.patch_submitted and 'logic.py' in patch and len(calls)<=len(actions)
        events=[json.loads(l) for l in (out/'adk_events.jsonl').read_text().splitlines()]
        responses=[p['function_response'] for e in events for p in (e['event'].get('content') or {}).get('parts',[]) if p.get('function_response')]
        skill_responses=[r for r in responses if r['name']=='run_skill_script']
        text=json.dumps(skill_responses)
        assert 'LOCAL_CHECKS_SUPPORTED' in text and 'UNKNOWN_OR_REFUSED' in text and 'Patch change has not been recorded' in text
        write(out/'CPU_SKILL_ACCEPTANCE.json',dict(status='PASS',real_model_requests=0,GPU_devices=0,official_SkillToolset=True,source_bound_ledger=True,stale_accept_refused=True,explicit_submission=True,owned_fixture_only=True,native_competition_resolved=None,scripted_requests=len(calls),agent_error=error))
    finally:
        manager.cleanup_all();server.shutdown();server.server_close();thread.join(timeout=5)
        assert not manager.sandboxes and all(not Path(e['lease']).exists() for e in manager.entries)
        write(out/'CLEANUP.json',dict(complete=True,records=manager.cleanup_records))
if __name__=='__main__':
    import sys
    asyncio.run(main(sys.argv[1]))
