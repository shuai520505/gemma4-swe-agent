"""Actual CPU preflight functions+owned synthetic worker;never real Gemma/SWE repair."""
import asyncio
import hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import threading

from harness_v2.evidence import atomic_json

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];PRIOR=HERE.parent/'integrated_cpu_01'

async def run(output):
    import torch
    assert torch.cuda.device_count()==0
    from ..real_gemma_abba01.session import native_baseline
    from ..real_gemma_abba01.worker import evaluate
    from s1.task_identity import find_data,identify
    from swegemma.models import load_tasks
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    data=find_data();lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes());tasks={t.instance_id:t for t in load_tasks(data/'tasks.jsonl')}
    identities=identify(data,[f['instance_id'] for f in lock['tasks']]);results=[]
    for f in lock['tasks']:
        for key in ('repo','base_commit','issue_sha256','task_record_sha256','test_patch_sha256','input_files'):assert identities[f['instance_id']][key]==f[key]
        baseline=await native_baseline(data,tasks[f['instance_id']],f,output/'baselines'/f['instance_id'])
        assert baseline['eligible'];results.append(dict(instance_id=f['instance_id'],expected_counts=f['native_baseline_counts'],native_preflight_pass=True))
    # Exact production worker entry,with ONLY the local model boundary scripted.
    # This owned project is not a benchmark task or an additional study sample.
    toy=output/'owned';repo=toy/'repo';repo.mkdir(parents=True);(repo/'fastapi').mkdir()
    (repo/'fastapi/__init__.py').write_text('')
    bad='def accepts(value):\n    return value > 0\n';good=bad.replace('> 0','>= 0')
    (repo/'fastapi/owned.py').write_text(bad)
    (repo/'checks.py').write_text('from pathlib import Path\nimport fastapi.owned as impl\nassert Path(impl.__file__).resolve()==Path("fastapi/owned.py").resolve()\nassert impl.accepts(0) and impl.accepts(3) and not impl.accepts(-1)\n')
    for args in (['init','-q'],['config','user.email','owned@example.invalid'],['config','user.name','Owned'],['add','.'],['commit','-qm','owned baseline']):subprocess.run(['git',*args],cwd=repo,check=True)
    base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    snapshots=toy/'snapshots';snapshots.mkdir()
    with tarfile.open(snapshots/'ure_gpu02_owned.tgz','w:gz') as t:
        for p in sorted(repo.iterdir()):t.add(p,arcname=p.name)
    overlay='diff --git a/test_owned.py b/test_owned.py\nnew file mode 100644\n--- /dev/null\n+++ b/test_owned.py\n@@ -0,0 +1,3 @@\n+from fastapi.owned import accepts\n+def test_owned():\n+    assert accepts(0) and accepts(3) and not accepts(-1)\n'
    record=dict(instance_id='ure_gpu02_owned',repo='test/ure_toy',base_commit=base,problem_statement='Accept zero and positive values in fastapi/owned.py while rejecting negatives.',test_patch=overlay)
    (toy/'tasks.jsonl').write_text(json.dumps(record)+'\n');(toy/'wheels').symlink_to(data/'wheels',target_is_directory=True)
    baseline=toy/'baseline.json';atomic_json(baseline,dict(eligible=True,production_source_hashes={'fastapi/owned.py':hashlib.sha256(bad.encode()).hexdigest()},scope='OWNED_SYNTHETIC_CONTROL_ONLY'))
    actions=iter([('get_status',{}),('read_file',dict(filepath='fastapi/owned.py')),
        ('edit_file',dict(filepath='fastapi/owned.py',old_string=bad,new_string=good)),
        ('run_command',dict(command='python3 checks.py && git diff --check && git diff')),('submit_patch',{}),'End.'])
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
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
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        await evaluate(dict(instance_id=record['instance_id'],data=str(toy),agent_dir=str(ROOT/'u_re/v01/candidate_noegv'),
            model_path='gemma-4-31b-it-qat-w4a16-ct-CPU-SCRIPTED-ONLY',base_url='http://127.0.0.1:'+str(server.server_port)+'/v1',baseline_capture=str(baseline)),output/'synthetic')
    finally:server.shutdown();server.server_close();thread.join(timeout=5)
    native=json.loads((output/'synthetic/official_result.json').read_bytes());done=json.loads((output/'synthetic/worker_done.json').read_bytes())
    assert native['resolved'] is True and native['test_exit_code']==0 and done['cleanup_complete'] and done['integrity_complete']
    assert (output/'synthetic/verifier/phase2.junit.xml').is_file() and calls
    atomic_json(output/'CPU_ACCEPTANCE.json',dict(status='CPU_IMPORT_AND_ENTRYPOINT_REPAIR_PASS',real_native_baseline_rechecks=results,
        owned_synthetic_worker=dict(native_resolved=True,JUnit=True,real_official_tools=True,chroot=True,cleanup=True,scripted_HTTP_requests=len(calls)),
        real_Gemma_requests=0,GPU=False,synthetic_Agent_sessions=1,real_SWE_Agent_sessions=0,
        caveat='Synthetic worker runtime_config real_model flag is generic/hardcoded;only CPU scripted boundary used,not GPU or algorithm evidence'))
    print('CPU_IMPORT_AND_ENTRYPOINT_REPAIR_PASS',flush=True)

if __name__=='__main__':asyncio.run(run(sys.argv[1]))
