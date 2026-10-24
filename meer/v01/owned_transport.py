"""CPU-only model boundary and researcher-owned fixture; EXCLUDED from GPU payload."""
import hashlib,json,subprocess,tarfile,threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from harness_v2.evidence import atomic_json

class CPUTransport:
    model_path='gemma-4-31b-it-qat-w4a16-ct-CPU-SCRIPTED-ONLY'
    active=0
    cleaned=False
    def start(self,data,output):
        owner=self
        toy=output/'owned';repo=toy/'repo';repo.mkdir(parents=True);(repo/'fastapi').mkdir()
        (repo/'fastapi/__init__.py').write_text('')
        bad='def accepts(value):\n    return value > 0\n';good=bad.replace('> 0','>= 0')
        (repo/'fastapi/owned.py').write_text(bad)
        (repo/'checks.py').write_text('from pathlib import Path\nimport fastapi.owned as impl\nassert Path(impl.__file__).resolve()==Path("fastapi/owned.py").resolve()\nassert impl.accepts(0) and impl.accepts(3) and not impl.accepts(-1)\n')
        for args in (['init','-q'],['config','user.email','owned@example.invalid'],['config','user.name','Owned'],['add','.'],['commit','-qm','owned baseline']):subprocess.run(['git',*args],cwd=repo,check=True)
        base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
        snapshots=toy/'snapshots';snapshots.mkdir()
        with tarfile.open(snapshots/'ure_gpu03_owned.tgz','w:gz') as t:
            for p in sorted(repo.iterdir()):t.add(p,arcname=p.name)
        overlay='diff --git a/test_owned.py b/test_owned.py\nnew file mode 100644\n--- /dev/null\n+++ b/test_owned.py\n@@ -0,0 +1,3 @@\n+from fastapi.owned import accepts\n+def test_owned():\n+    assert accepts(0) and accepts(3) and not accepts(-1)\n'
        record=dict(instance_id='ure_gpu03_owned',repo='test/ure_toy',base_commit=base,problem_statement='Accept zero and positive values in fastapi/owned.py while rejecting negatives.',test_patch=overlay)
        (toy/'tasks.jsonl').write_text(json.dumps(record)+'\n');(toy/'wheels').symlink_to(data/'wheels',target_is_directory=True)
        baseline=toy/'baseline.json';atomic_json(baseline,dict(eligible=True,production_source_hashes={'fastapi/owned.py':hashlib.sha256(bad.encode()).hexdigest()},scope='OWNED_SYNTHETIC_CONTROL_ONLY'))
        actions=iter([('get_status',{}),('read_file',dict(filepath='fastapi/owned.py')),
            ('edit_file',dict(filepath='fastapi/owned.py',old_string=bad,new_string=good)),
            ('run_command',dict(command='python3 checks.py && git diff --check && git diff')),('submit_patch',{}),'End.'])
        calls=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                if self.path=='/metrics':
                    raw=('vllm:num_requests_running '+str(owner.active)+'\nvllm:num_requests_waiting 0\n').encode()
                elif self.path=='/health':raw=b'{}'
                else:raise ValueError('Unexpected CPU health path')
                self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                assert overlay not in json.dumps(body)
                if self.path=='/tokenize':reply=dict(count=100,max_model_len=32768)
                else:
                    assert self.path=='/v1/chat/completions';calls.append(body);action=next(actions,'End.')
                    if isinstance(action,tuple):
                        name,args=action;message=dict(role='assistant',content=None,tool_calls=[dict(id='owned_'+str(len(calls)),type='function',function=dict(name=name,arguments=json.dumps(args)))]);finish='tool_calls'
                    else:message=dict(role='assistant',content=action);finish='stop'
                    reply=dict(id='CPU_SCRIPTED_'+str(len(calls)),object='chat.completion',created=1,model=body['model'],choices=[dict(index=0,message=message,finish_reason=finish)],usage=dict(prompt_tokens=100,completion_tokens=8,total_tokens=108))
                raw=json.dumps(reply).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        self.calls=calls;self.data=toy;self.baseline=baseline
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base_url='http://127.0.0.1:'+str(self.server.server_port)+'/v1'
        return self
    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=5)
        self.cleaned=not self.thread.is_alive()
    def verify(self,output,records):
        assert len(records)==1 and records[0]['worker']['allow_next_run']
        d=Path(output)/'runs/01-ure_gpu03_owned-A'
        native=json.loads((d/'official_result.json').read_bytes());done=json.loads((d/'worker_done.json').read_bytes())
        agent=json.loads((d/'agent/agent_result.json').read_bytes());http=json.loads((d/'HTTP_AUDIT.json').read_bytes())
        assert native['resolved'] and native['test_exit_code']==0 and done['cleanup_complete'] and done['integrity_complete']
        assert agent['patch_submitted'] and agent['patch_bytes']>0 and http['passed'] and http['requests']==6
        assert (d/'verifier/phase2.junit.xml').is_file()
        assert any(m.get('role')=='tool' for request in self.calls for m in request['messages'])
        atomic_json(Path(output)/'CPU_TRANSPORT_PROOF.json',dict(CPU_MODEL='SCRIPTED_ONLY',HTTP_requests=len(self.calls),tool_results_returned_to_model=True,real_Gemma_requests=0,owned_patch_bytes=agent['patch_bytes']))
