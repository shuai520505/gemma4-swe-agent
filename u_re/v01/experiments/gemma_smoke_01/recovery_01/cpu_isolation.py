"""Real six-tool boundary tests with owned canaries; no competition task/model."""
import base64
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import shlex
from unittest.mock import patch
from .isolation import isolated_environment
from .landlock_exec import probe

PROBE=r'''import ctypes,errno,json,os,pathlib,socket,subprocess,sys
targets=json.loads(__import__('base64').b64decode(TARGETS))
assert os.geteuid()==65534, 'UID_NOT_SEPARATED'
assert 'URE_ISOLATION_FAKE_SECRET' not in os.environ
def denied(action):
    try:action()
    except OSError as exc:
        assert exc.errno in (errno.EACCES,errno.EPERM,errno.EXDEV), (type(exc).__name__,exc.errno)
    else:raise AssertionError('PRIVATE_ACCESS_SUCCEEDED')
for filename in targets:
    p=pathlib.Path(filename)
    denied(lambda:p.read_bytes())
    denied(lambda:p.write_text('UNEXPECTED_OWNED_CANARY_WRITE'))
link=pathlib.Path('escape_link')
link.symlink_to(targets[0])
try:denied(lambda:link.read_bytes())
finally:link.unlink()
private=pathlib.Path(targets[0]);relative=os.path.relpath(private,pathlib.Path.cwd())
denied(lambda:pathlib.Path(relative).read_bytes())
code='import pathlib,sys; p=pathlib.Path(sys.argv[1]);\ntry:p.read_bytes()\nexcept PermissionError:print("DESCENDANT_DENIED")\nelse:raise AssertionError("DESCENDANT_ESCAPE")'
child=subprocess.run([sys.executable,'-c',code,targets[0]],capture_output=True,text=True)
assert child.returncode==0 and 'DESCENDANT_DENIED' in child.stdout, child.stderr
denied(lambda:socket.socket(socket.AF_INET,socket.SOCK_STREAM))
libc=ctypes.CDLL(None,use_errno=True);libc.syscall.restype=ctypes.c_long
assert libc.syscall(310,os.getppid(),0,0,0,0,0)==-1 and ctypes.get_errno()==errno.EACCES, 'CROSS_PROCESS_MEMORY_NOT_BLOCKED'
local=pathlib.Path('allowed-write.txt');local.write_text('owned positive control');assert local.read_text()=='owned positive control';local.unlink()
pathlib.Path('owned_probe.txt').unlink()
print('KERNEL_FILESYSTEM_ISOLATION_OK',json.dumps(dict(uid=os.geteuid(),targets_denied=len(targets),symlink_denied=True,traversal_denied=True,descendant_denied=True,parent_memory_denied=True,network_denied=True)))
'''

def command(code):
    return 'python3 -c '+shlex.quote(code)

async def run(output):
    from harness_v2.evidence import atomic_json,read_events
    from u_re.v01 import runner_cases as cases
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    capability=probe();assert os.geteuid()==0,'UID-separated boundary unavailable'
    private=output/'owned_research_private';private.mkdir()
    targets=[];before={}
    for name in ('evaluator-canary.txt','other-arm-canary.txt','credential-canary.txt'):
        f=private/name;f.write_text('OWNED_SYNTHETIC_CANARY_'+name);f.chmod(0o666)
        targets.append(str(f.resolve()));before[name]=hashlib.sha256(f.read_bytes()).hexdigest()
    original_plan=cases.plan
    def negative_plan(case):
        return [cases.call('run_command',command=command('import pathlib; assert pathlib.Path('+repr(targets[0])+').read_text().startswith("OWNED_SYNTHETIC_CANARY"); print("UNRESTRICTED_PRIVATE_READ_CONFIRMED")')),
                *original_plan('basic')]
    with patch.object(cases,'plan',negative_plan):
        control=await cases.exercise('noegv','unrestricted_canary',output/'negative_control')
    assert any('UNRESTRICTED_PRIVATE_READ_CONFIRMED' in str(r['result']) and r['result']['status']=='ok' for r in control['command_responses'])
    encoded=base64.b64encode(json.dumps(targets).encode()).decode()
    script='TARGETS='+repr(encoded)+'\n'+PROBE
    def protected_plan(case):
        return [cases.call('get_status'),cases.call('read_file',filepath='app.py'),
                cases.call('write_file',filepath='owned_probe.txt',content='owned'),
                cases.call('run_command',command=command(script)),
                cases.call('read_file',filepath=targets[0]),
                cases.edit(cases.BAD,cases.GOOD),cases.call('run_command',command='python3 checks.py && git diff --check && git diff'),
                cases.call('submit_patch'),'Submitted; end.']
    saved=os.environ.get('URE_ISOLATION_FAKE_SECRET');os.environ['URE_ISOLATION_FAKE_SECRET']='OWNED_DUMMY_NOT_A_CREDENTIAL'
    try:
        with isolated_environment(policy_root=output/'private_policy',audit_modules=('app',)) as cls:
            with (patch.object(cases,'DurableManager',partial(cls,audit_modules=('app',),policy_root=output/'private_policy')),
                  patch.object(cases,'plan',protected_plan)):
                result=await cases.exercise('noegv','landlock_boundary',output/'protected')
    finally:
        if saved is None:os.environ.pop('URE_ISOLATION_FAKE_SECRET',None)
        else:os.environ['URE_ISOLATION_FAKE_SECRET']=saved
    assert any('KERNEL_FILESYSTEM_ISOLATION_OK' in str(r['result']) and r['result']['status']=='ok' for r in result['command_responses'])
    assert result['successful_edits']==1 and result['successful_submits']==1 and result['HTTP_audit']['passed']
    events=read_events(output/'protected/adk_events.jsonl')
    responses=[part['function_response'] for e in events for part in e.get('event',{}).get('content',{}).get('parts',[]) if part.get('function_response')]
    private_read=[r for r in responses if r['name']=='read_file' and r['response'].get('status')=='error']
    assert private_read,'Official read_file must not disclose the canary'
    after={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in private.iterdir()}
    assert before==after
    cleanup=json.loads((output/'protected/cleanup.json').read_text());assert cleanup['complete']
    policy_events=[e for e in read_events(output/'protected/events.jsonl') if e.get('kind')=='filesystem_policy_launch']
    assert policy_events
    gate=dict(passed=True,kernel=capability,host_uid=os.geteuid(),tool_uid=65534,
        actual_official_tools=True,negative_control_private_read=True,private_canary_hashes_unchanged=True,
        protected_command_probe_passed=True,read_file_denied=True,tool_edit_and_submit_passed=True,
        policy_launches=len(policy_events),cleanup=True,GPU=False,Gemma_inference=False,
        scope='UID separation + Landlock data-access rules + seccomp escape/connection restrictions. Not kernel-exploit containment, not a proof for untested kernels.')
    atomic_json(output/'ISOLATION_GATE.json',gate);return gate
