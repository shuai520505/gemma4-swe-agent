"""Actual official Compiler/ADK/Runner/tools, scripted HTTP only; native Verifier."""
import asyncio
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
from unittest.mock import patch

from harness_v2.evidence import atomic_json,Journal
from .CHROOT_TASK_RUNTIME import SubprocessManager,recover


CANARY=r'''import os,pathlib,ctypes,errno,socket,subprocess,sys,httpx,fastapi
assert os.getuid()>=20000
assert httpx.__file__.startswith('/opt/approved/') and fastapi.__file__.startswith('/opt/approved/')
for path in TARGETS:
    for p in (path,'../../../../../'+path.lstrip('/')):
        try:pathlib.Path(p).read_bytes()
        except (FileNotFoundError,PermissionError):pass
        else:raise AssertionError('PRIVATE_ESCAPE')
    link=pathlib.Path('escape');link.symlink_to(path)
    try:
        try:link.read_bytes()
        except (FileNotFoundError,PermissionError):pass
        else:raise AssertionError('SYMLINK_ESCAPE')
    finally:link.unlink()
code='import pathlib,sys;\ntry:pathlib.Path(sys.argv[1]).read_bytes()\nexcept (FileNotFoundError,PermissionError):print("DENIED")\nelse:raise AssertionError("DESCENDANT_ESCAPE")'
p=subprocess.run([sys.executable,'-c',code,TARGETS[0]],capture_output=True,text=True)
assert p.returncode==0 and 'DENIED' in p.stdout,p.stderr
for fd in range(3,256):
    try:os.fstat(fd)
    except OSError:continue
    raise AssertionError('FD_ESCAPE')
assert not pathlib.Path('/proc').exists() and not pathlib.Path('/kaggle/input').exists()
libc=ctypes.CDLL(None,use_errno=True);libc.syscall.restype=ctypes.c_long
assert libc.syscall(310,os.getppid(),0,0,0,0,0)==-1 and ctypes.get_errno()==errno.EACCES
try:socket.socket(socket.AF_INET,socket.SOCK_STREAM)
except PermissionError:pass
else:raise AssertionError('NETWORK_ESCAPE')
try:pathlib.Path('/opt/approved/UNAUTHORIZED').write_text('bad')
except PermissionError:pass
else:raise AssertionError('RUNTIME_WRITE')
print('INTEGRATED_CANARY_AND_DEPENDENCIES_OK')
'''


async def run(output):
    import torch,psutil
    assert sys.platform=='linux' and torch.cuda.device_count()==0
    from u_re.v01 import runner_cases as cases
    from s1.task_identity import find_data
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    wheels=find_data()/'wheels'
    private=output/'owned_research';private.mkdir()
    targets=[]
    for name in ('research','evaluator','other-arm'):
        p=private/(name+'.txt');p.write_text('OWNED_CANARY_'+name);targets.append(str(p))
    before={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in targets}
    fd=os.open(targets[0],os.O_RDONLY);os.set_inheritable(fd,True)
    original_plan=cases.plan
    def plan(case):
        if case!='integrated':return original_plan(case)
        code=CANARY.replace('TARGETS',repr(targets))
        return [cases.call('get_status'),cases.call('read_file',filepath='app.py'),
            cases.call('write_file',filepath='owned_probe.py',content=code),
            cases.call('run_command',command='python3 owned_probe.py'),
            cases.call('run_command',command='ln -s '+shlex.quote(targets[0])+' escape-link'),
            cases.call('read_file',filepath='escape-link'),
            cases.call('write_file',filepath='escape-link',content='UNAUTHORIZED'),
            cases.call('run_command',command='rm owned_probe.py escape-link'),
            cases.edit(cases.BAD,cases.GOOD),cases.call('run_command',command='python3 checks.py && git diff --check && git diff'),
            cases.call('submit_patch'),'Submitted; end.']
    results=[]
    try:
        with patch.object(cases,'DurableManager',partial(SubprocessManager,task_wheels=wheels)),patch.object(cases,'plan',plan):
            for case in ('integrated','exact_tools','external_cancel','deadline'):
                r=await cases.exercise('noegv',case,output/'cases'/case)
                results.append(dict(case=case,tools=r['counted_tools'],edits=r['successful_edits'],submits=r['successful_submits'],error=r['error']))
                boundary=json.loads((output/'cases'/case/'boundary.json').read_bytes())
                assert (boundary['budget_seconds'],boundary['tools_limit'],boundary['command_seconds'])==(300,60,120)
                assert json.loads((output/'cases'/case/'cleanup.json').read_bytes())['complete']
                if case=='integrated':
                    assert r['successful_edits']==1 and r['successful_submits']==1
                    assert any('INTEGRATED_CANARY_AND_DEPENDENCIES_OK' in str(row['result']) and row['result']['status']=='ok' for row in r['command_responses'])
                    assert sorted({e['tool'] for e in cases.tool_events(cases.read_events(output/'cases'/case/'adk_events.jsonl'))})==sorted(['get_status','run_command','read_file','write_file','edit_file','submit_patch'])
                if case=='exact_tools':assert r['counted_tools']==60
                if case=='external_cancel':assert r['external_cancellation_propagated'] and r['HTTP_cancelled']
                if case=='deadline':assert 299<=r['native_agent_seconds']<315 and r['HTTP_cancelled']
        assert before=={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in targets}
    finally:os.close(fd)
    # Normal,background,setsid timeout and cancellation at the execution boundary.
    directory=output/'lifecycle';directory.mkdir();manager=SubprocessManager(journal=Journal(directory),base_dir=directory/'roots',task_wheels=wheels)
    sid=manager.start()
    daemon='import os,time,pathlib; pid=os.fork();\nif pid==0:os.setsid();pathlib.Path("detached.pid").write_text(str(os.getpid()));time.sleep(180)\nelse:pathlib.Path("parent.pid").write_text(str(os.getpid()));time.sleep(180)'
    try:
        result=await asyncio.to_thread(manager.exec,sid,'python3 -c '+shlex.quote(daemon),timeout=120)
        assert result.timed_out and result.duration_seconds>=119
        timed=dict(timed_out=True,seconds=result.duration_seconds)
        job=asyncio.create_task(asyncio.to_thread(manager.exec,sid,'python3 -c '+shlex.quote(daemon),timeout=120))
        await asyncio.sleep(2);await asyncio.to_thread(manager.stop,sid);await job
        atomic_json(directory/'LIFECYCLE.json',dict(command_120=timed,external_abort=True,background_and_new_session_uid_cleanup=True,roots_removed=not manager.sandboxes))
    finally:manager.cleanup_all()
    # Simulate an interrupted Notebook worker,not an actual platform VM restart.
    crash=output/'crash';crash.mkdir()
    p=subprocess.Popen([sys.executable,'-m',__package__+'.acceptance','--crash',str(crash),str(wheels)],start_new_session=True)
    deadline=time.monotonic()+90
    while not (crash/'READY.json').exists():
        assert p.poll() is None,'Crash fixture failed before active tool'
        assert time.monotonic()<deadline,'Crash fixture preparation timeout'
        await asyncio.sleep(.25)
    p.kill();p.wait(timeout=5)
    records=recover(crash/'roots/owned_uids.json')
    atomic_json(crash/'RECOVERY.json',dict(simulated_worker_SIGKILL=True,owned_registry_recovery=records,platform_kernel_restart='NOT_RUN'))
    import shutil
    shutil.rmtree(crash/'roots')
    # Use the existing trusted native Verifier and its passive JUnit observer.
    from swegemma.harness.verification import verify_task
    from swegemma.models import Task
    from swegemma.config import EvalConfig
    from adk_submission import ModelRegistry
    from s1.verifier_v3.environment import SubprocessManager as Trusted,research_environment
    from s1.verifier_v3.audit import audit_verifier
    directory=output/'native';directory.mkdir()
    overlay='diff --git a/test_owned.py b/test_owned.py\nnew file mode 100644\n--- /dev/null\n+++ b/test_owned.py\n@@ -0,0 +1,4 @@\n+import app\n+def test_boundary():\n+    assert app.accepts(0)\n+    assert app.accepts(3) and not app.accepts(-1)\n'
    task=Task(instance_id='ure_integrated_owned',repo='test/ure_toy',base_commit='synthetic',problem_statement='Owned inclusive boundary',test_patch=overlay)
    trusted=Trusted(journal=Journal(directory),base_dir=directory/'roots',audit_modules=['app'],task_wheels=wheels,timeout_seconds=120);trusted.agent_id='trusted_verifier_no_agent'
    cfg=EvalConfig(tasks_path=directory/'unused.jsonl',snapshots_dir=directory,results_dir=directory/'native',submission_dir=cases.HERE/'candidate_noegv',models=ModelRegistry(),sandbox='subprocess',verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
    try:
        with research_environment(audit_modules=['app'],task_wheels=wheels):
            result=await verify_task(trusted,cfg,task,output/'cases/integrated/baseline.tgz',agent_patch=(output/'cases/integrated/returned.patch').read_text(),start_time=time.perf_counter())
        atomic_json(directory/'official_result.json',result.model_dump(mode='json',exclude={'trace'}))
    finally:trusted.cleanup_all()
    audit=audit_verifier(directory);atomic_json(directory/'audit.json',audit)
    assert result.resolved and result.test_exit_code==0 and not audit['infrastructure_stop'] and (directory/'phase2.junit.xml').is_file()
    atomic_json(directory/'cleanup.json',dict(complete=not trusted.sandboxes))
    remaining=[dict(pid=p.pid,name=p.name()) for p in psutil.Process().children(recursive=True) if p.is_running() and p.status()!=psutil.STATUS_ZOMBIE]
    assert not remaining,remaining
    atomic_json(output/'CPU_ACCEPTANCE.json',dict(status='INTEGRATED_RUNNER_CPU_PASS',official_Compiler_ADK_Runner=True,official_six_tools=True,
        chroot_canaries=True,third_party_dependencies=True,cases=results,command_timeout_120=True,external_abort=True,detached_child_cleanup=True,worker_crash_recovery=True,
        actual_platform_kernel_restart='NOT_RUN',native_TaskResult=True,native_JUnit=True,native_resolved=True,cleanup=True,model='SCRIPTED_HTTP_ONLY',real_Gemma=0,GPU=False))
    print('INTEGRATED_RUNNER_CPU_PASS',flush=True)


def crash_worker(out,wheels):
    out=Path(out);m=SubprocessManager(journal=Journal(out),base_dir=out/'roots',task_wheels=wheels);sid=m.start()
    code='import os,pathlib,time;\nif os.fork()==0:os.setsid();time.sleep(300)\nelse:pathlib.Path("active").write_text("owned");time.sleep(300)'
    def signal_ready():
        import threading
        def observe():
            while not (m.sandboxes[sid]['workspace']/'active').exists():time.sleep(.05)
            atomic_json(out/'READY.json',dict(sid=sid,uid=m.sandboxes[sid]['uid']))
        threading.Thread(target=observe,daemon=True).start()
    signal_ready();m.exec(sid,'python3 -c '+shlex.quote(code),timeout=300)


if __name__=='__main__':
    if sys.argv[1:2]==['--crash']:crash_worker(sys.argv[2],sys.argv[3])
    else:asyncio.run(run(sys.argv[1]))
