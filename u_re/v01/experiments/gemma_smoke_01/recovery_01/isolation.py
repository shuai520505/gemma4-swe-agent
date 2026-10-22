"""External process-creation boundary around unchanged official tools/commands.

No preexec_fn: a clean stdlib launcher process applies kernel restrictions then
execs the original bash argv. Thread-local dispatch supports overlapping tools.
"""
import base64
from contextlib import contextmanager
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import uuid
from unittest.mock import patch
from .landlock_exec import RO,RW,READ,WRITE,WRITE_ONLY,TRUNCATE,probe

LOCAL=threading.local()
SYSTEM_DIRS=('/usr','/bin','/sbin','/lib','/lib64')
SYSTEM_FILES=('/etc/ld.so.cache','/etc/localtime','/etc/nsswitch.conf','/etc/passwd',
              '/etc/group','/etc/hosts','/etc/resolv.conf','/dev/urandom','/dev/random')
ENV_ALLOW={'PATH','LANG','LC_ALL','LC_CTYPE','TZ','VIRTUAL_ENV','PYTHONPATH','PYTHONIOENCODING',
           'PYTHONUNBUFFERED','PYTHONNOUSERSITE','PYTHONDONTWRITEBYTECODE',
           'OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','TMPDIR','TMP','TEMP',
           'PIP_NO_INDEX','PIP_CONFIG_FILE','PIP_DISABLE_PIP_VERSION_CHECK'}
TOOL_UID=65534;TOOL_GID=65534

def policy_for(paths):
    rules=[];seen=set()
    def add(path,access):
        path=Path(path)
        if not path.exists():return
        real=str(path.resolve())
        if (real,access) not in seen:rules.append(dict(path=real,access=access));seen.add((real,access))
    for path in SYSTEM_DIRS:add(path,RO)
    for path in SYSTEM_FILES:add(path,READ)
    add('/dev/null',READ|WRITE|TRUNCATE)
    for name in ('workspace','tmp'):add(paths[name],RW)
    for name in ('venv','wheels'):add(paths[name],RO)
    return rules

def wrap_popen(original,args,kwargs,scope):
    if kwargs.get('shell') or not isinstance(args,(list,tuple)) or list(args[:2])!=['/bin/bash','-c'] or len(args)!=3:
        raise RuntimeError('Unrecognized tool process; refuse unconstrained execution')
    if kwargs.get('pass_fds') or kwargs.get('preexec_fn'):raise RuntimeError('Unexpected inherited fds/preexec callback')
    rules=policy_for(scope['paths'])
    match=re.search(r'^export S1_IMPORT_AUDIT_DIR_B64=([A-Za-z0-9+/=]+);',args[2])
    if match:
        sink=Path(base64.b64decode(match[1],validate=True).decode()).resolve()
        parent=(scope['journal'].directory/'import_audit').resolve()
        if sink.parent!=parent or not re.fullmatch('[a-f0-9]{32}',sink.name):raise RuntimeError('Import audit sink outside registered observer')
        sink.mkdir(parents=True,exist_ok=True)
        os.chown(sink,TOOL_UID,TOOL_GID);sink.chmod(0o300)
        rules.append(dict(path=str(sink),access=WRITE_ONLY))
    target=scope['root']/(uuid.uuid4().hex+'.json')
    raw=(json.dumps(dict(rules=rules,uid=TOOL_UID,gid=TOOL_GID),sort_keys=True)+'\n').encode()
    with target.open('xb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
    env={k:v for k,v in kwargs.get('env',{}).items() if k in ENV_ALLOW or k.startswith('LC_')}
    env.update(GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
    kwargs.update(env=env,close_fds=True)
    if kwargs.get('stdin') is None:kwargs['stdin']=subprocess.DEVNULL
    scope['journal'].append(dict(kind='filesystem_policy_launch',policy_sha256=hashlib.sha256(raw).hexdigest(),
        original_command_sha256=hashlib.sha256(args[2].encode()).hexdigest(),
        allowed_roots=[r['path'] for r in rules],kernel_enforced=True,original_argv_preserved=True))
    return original([sys.executable,'-I','-S',str(Path(__file__).with_name('landlock_exec.py')),str(target),*args],**kwargs)

@contextmanager
def dispatch_boundary():
    original=subprocess.Popen
    def dispatch(args,*positional,**kwargs):
        scope=getattr(LOCAL,'scope',None)
        if scope:
            if positional:raise RuntimeError('Unexpected Popen positional flags')
            return wrap_popen(original,args,kwargs,scope)
        return original(args,*positional,**kwargs)
    with patch('subprocess.Popen',dispatch):yield

def manager_class():
    from s1.verifier_v3.environment import SubprocessManager as Parent
    class SubprocessManager(Parent):
        def __init__(self,*args,policy_root=None,**kwargs):
            super().__init__(*args,**kwargs)
            self.policy_root=Path(policy_root or self.journal.directory/'private_policy')
            self.policy_root.mkdir(parents=True,exist_ok=True)
            self.policy_setup_failed=False
            self.prepared_agent_roots=set()
        def exec(self,sandbox_id,command,*,timeout=None):
            context=getattr(self,'context',None)
            # Continue protecting native diff/submit/fallback after Agent stop:
            # repository .git/config and hooks are untrusted too.
            active=sandbox_id==self.agent_id and getattr(context,'agent_start_time',None) is not None
            previous=getattr(LOCAL,'scope',None)
            if active:
                if os.geteuid()!=0:raise RuntimeError('UID-separated tool host requires privileged preparation')
                paths=self.sandboxes[sandbox_id]
                if sandbox_id not in self.prepared_agent_roots:
                    paths['root'].chmod(0o711)
                    for key in ('workspace','tmp'):
                        root=paths[key];os.chown(root,TOOL_UID,TOOL_GID)
                        for directory,names,files in os.walk(root,followlinks=False):
                            for name in names+files:os.chown(Path(directory)/name,TOOL_UID,TOOL_GID,follow_symlinks=False)
                    self.prepared_agent_roots.add(sandbox_id)
                LOCAL.scope=dict(paths=self.sandboxes[sandbox_id],journal=self.journal,root=self.policy_root)
            try:
                result=super().exec(sandbox_id,command,timeout=timeout)
                if active and 'ISOLATION_SETUP_FAILED' in (result.stderr or ''):
                    self.policy_setup_failed=True
                    raise RuntimeError('Tool filesystem confinement failed; do not continue inference')
                return result
            finally:LOCAL.scope=previous
    return SubprocessManager

@contextmanager
def isolated_environment(*,policy_root=None,audit_modules=('app',),task_wheels=None):
    probe()
    from s1.verifier_v3.environment import research_environment
    cls=manager_class()
    with research_environment(audit_modules=audit_modules,task_wheels=task_wheels),dispatch_boundary():
        with patch('harness_v2.official.DurableManager',partial(cls,policy_root=policy_root,
                    audit_modules=audit_modules,task_wheels=task_wheels)):
            yield cls
