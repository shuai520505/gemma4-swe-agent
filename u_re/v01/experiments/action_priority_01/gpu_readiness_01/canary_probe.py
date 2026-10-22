"""Real official six-tool filesystem denial tests; owned synthetic data only."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys

from .chroot_boundary import ChrootToolBoundary


def main(out):
    from swegemma.context import SwegemmaContext
    from swegemma.tools import create_tools
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    private=out/'owned_private';private.mkdir()
    targets=[]
    for name in ('research','evaluator','other-arm'):
        f=private/(name+'.txt');f.write_text('OWNED_SYNTHETIC_'+name);targets.append(f)
    original={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in targets}
    assert all(p.read_text().startswith('OWNED_SYNTHETIC_') for p in targets)
    manager=None;result=dict(experiment_id='U-RE-ACTION-FIRST-ISOLATION-CANARY01',started_utc=datetime.now(timezone.utc).isoformat(),
        GPU=False,Gemma_calls=0,Agent_runs=0,task_baselines=0,checks={},isolation_verified=False)
    fd=os.open(targets[0],os.O_RDONLY);os.set_inheritable(fd,True)
    try:
        manager=ChrootToolBoundary(out/'chroot',out/'tool_processes.json')
        context=SwegemmaContext(docker_manager=manager,container_id='owned-chroot',repo='test/owned-isolation',
            max_tool_calls=60,max_time_minutes=5,max_exec_seconds=120)
        context.start_agent_session()
        tools=create_tools(context)
        names=('get_status','run_command','read_file','edit_file','write_file','submit_patch')
        events=[]
        def call(name,**kwargs):
            value=tools[name](**kwargs);events.append(dict(tool=name,args=kwargs,result=value))
            (out/'official_tool_events.json').write_text(json.dumps(events,indent=2)+'\n')
            return value
        def ok(name,**kwargs):
            value=call(name,**kwargs);assert value['status']=='ok',(name,value);return value
        status=ok('get_status');assert status['max_tool_calls']==60 and status['max_time_minutes']==5 and status['command_timeout_seconds']==120
        ok('write_file',filepath='app.py',content='def accepts(n):\n    return n > 0\n')
        ok('read_file',filepath='app.py')
        ok('run_command',command='git init -q && git config user.email cpu@example.invalid && git config user.name CPU && git add . && git commit -qm baseline && git tag _swegemma_baseline')
        result['checks']['workspace_read_write']=True
        for target in targets:
            code='from pathlib import Path; p=Path('+repr(str(target))+');\ntry:p.read_bytes()\nexcept (FileNotFoundError,PermissionError):print("DENIED")\nelse:raise AssertionError("HOST_READ_ESCAPE")'
            response=ok('run_command',command='python3 -c '+shlex.quote(code));assert 'DENIED' in str(response)
        result['checks']['absolute_research_evaluator_other_arm_denied']=True
        probe=r'''import os,pathlib,subprocess,sys,ctypes,errno,socket
targets=TARGETS
assert os.geteuid()==65534
def denied(path):
    try:pathlib.Path(path).read_bytes()
    except (FileNotFoundError,PermissionError):return
    raise AssertionError('ESCAPE '+str(path))
for p in targets:
    denied('../../../../../../'+p.lstrip('/'))
    link=pathlib.Path('escape');link.symlink_to(p)
    try:denied(link)
    finally:link.unlink()
code='import pathlib,sys; p=pathlib.Path(sys.argv[1]);\ntry:p.read_bytes()\nexcept (FileNotFoundError,PermissionError):print("CHILD_DENIED")\nelse:raise AssertionError("CHILD_ESCAPE")'
r=subprocess.run([sys.executable,'-c',code,targets[0]],capture_output=True,text=True)
assert r.returncode==0 and 'CHILD_DENIED' in r.stdout,r.stderr
for fd in range(3,256):
    try:os.fstat(fd)
    except OSError:continue
    raise AssertionError('INHERITED_FD '+str(fd))
assert not pathlib.Path('/proc').exists() and not pathlib.Path('/kaggle/input').exists()
libc=ctypes.CDLL(None,use_errno=True);libc.syscall.restype=ctypes.c_long
assert libc.syscall(310,os.getppid(),0,0,0,0,0)==-1 and ctypes.get_errno()==errno.EACCES
try:socket.socket(socket.AF_INET,socket.SOCK_STREAM)
except PermissionError:pass
else:raise AssertionError('EXTERNAL_SOCKET_ALLOWED')
pathlib.Path('positive').write_text('workspace');assert pathlib.Path('positive').read_text()=='workspace';pathlib.Path('positive').unlink()
print('CHROOT_CANARY_OK')
'''.replace('TARGETS',repr([str(p) for p in targets]))
        response=ok('run_command',command='python3 -c '+shlex.quote(probe));assert 'CHROOT_CANARY_OK' in str(response)
        for key in ('traversal_denied','symlink_denied','subprocess_denied','inheritable_fd_closed','proc_not_exposed','parent_memory_denied','network_denied'):
            result['checks'][key]=True
        # Exercise official read_file path through a symlink, including its real
        # copy_from boundary. No host-side shutil.copyfile follows that symlink.
        ok('run_command',command='python3 -c '+shlex.quote('from pathlib import Path;Path("escape-link").symlink_to('+repr(str(targets[0]))+')'))
        denied=call('read_file',filepath='escape-link');assert denied['status']=='error'
        result['checks']['official_read_file_symlink_denied']=True
        ok('run_command',command='python3 -c '+shlex.quote('from pathlib import Path;Path("escape-link").unlink()'))
        ok('edit_file',filepath='app.py',old_string='return n > 0',new_string='return n >= 0')
        ok('run_command',command='python3 -c '+shlex.quote('import app;assert app.accepts(0);assert not app.accepts(-1);print("TARGET_OLD_OK")')+' && git diff --check && git diff')
        ok('submit_patch');assert context.submitted_patch and 'return n >= 0' in context.submitted_patch
        result['checks']['six_official_tools_edit_test_diff_submit']=True
        result['tool_names_exercised']=sorted({e['tool'] for e in events});assert result['tool_names_exercised']==sorted(names)
        result['charged_tools']=context.tool_calls_used;result['runtime']=manager.runtime
        result['checks']['host_canaries_unchanged']=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in original.items())
        assert all(result['checks'].values())
        result['isolation_verified']=True
        result['scope']='Actual CPU deployment synthetic official tools only; no full task dependencies,ADK/GPU integration or kernel exploit containment claim'
    finally:
        os.close(fd)
        if manager:manager.cleanup()
        result['cleanup_complete']=not (out/'chroot').exists()
        result['ended_utc']=datetime.now(timezone.utc).isoformat()
        (out/'CANARY_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main(sys.argv[1])
