"""Research Sandbox adapter; organizer Runner/tools/Verifier are unchanged."""
import base64
import contextlib
import ctypes
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

from swegemma.sandbox.base import BaseSandboxManager
from adk_eval_core.sandbox import ExecutionResult
from harness_v2.evidence import atomic_json
from ..gpu_readiness_01.chroot_boundary import prepare_runtime


def kill_owned(entry):
    """Only this journal's freshly reserved non-root UID, including setsid."""
    import psutil
    assert 20000<=entry['uid']<60000
    lease=Path(entry['lease']);assert lease.stat().st_uid==0 and lease.stat().st_mode&0o077==0
    assert json.loads(lease.read_bytes())['token']==entry['token'],'Stale UID ownership record'
    killed=[]
    for process in psutil.process_iter(['pid','uids','create_time','status']):
        try:
            if process.info['uids'].real!=entry['uid']:continue
            assert process.info['create_time']>=entry['started_epoch']-2,'UID ownership conflict'
            if process.info['status']!=psutil.STATUS_ZOMBIE:process.kill();killed.append(process.pid)
        except (psutil.NoSuchProcess,ProcessLookupError):pass
    deadline=time.monotonic()+5
    remaining=[]
    while True:
        remaining=[]
        for process in psutil.process_iter(['pid','uids','status']):
            try:
                if process.info['uids'].real!=entry['uid']:continue
                if process.info['status']==psutil.STATUS_ZOMBIE:
                    with contextlib.suppress(ChildProcessError,ProcessLookupError):os.waitpid(process.pid,os.WNOHANG)
                else:remaining.append(process.pid)
            except psutil.NoSuchProcess:pass
        if not remaining or time.monotonic()>deadline:break
        time.sleep(.05)
    assert not remaining,('Owned UID cleanup failed',remaining)
    return killed


def recover(path):
    path=Path(path);assert path.stat().st_uid==0 and path.stat().st_mode&0o077==0
    records=json.loads(path.read_bytes());assert records['kind']=='URE_OWNED_UID_REGISTRY_V1'
    return [dict(uid=e['uid'],killed=kill_owned(e)) for e in records['entries']]


def dependency_copy(root,task_wheels=None,roots=('pytest','httpx','fastapi','setuptools','flit_core','wheel')):
    """Copy installed closure from pinned approved image/wheels; no install/network.

    No host .pth,script,editable path or unknown external file is imported.
    Module content and metadata hashes are recorded for later freeze.
    """
    from packaging.requirements import Requirement
    queue=list(roots);seen=set();rows=[];target=root/'opt/approved';target.mkdir(parents=True)
    while queue:
        name=queue.pop(0)
        try:dist=metadata.distribution(name)
        except metadata.PackageNotFoundError:
            # Offline build backend may be approved but absent from the image.
            import zipfile,email
            from packaging.utils import parse_wheel_filename,canonicalize_name
            from packaging.tags import sys_tags
            compatible=[]
            for p in Path(task_wheels).glob('*.whl') if task_wheels else []:
                pkg,version,_,tags=parse_wheel_filename(p.name)
                if canonicalize_name(pkg)==canonicalize_name(name) and tags&set(sys_tags()):compatible.append((version,p))
            if not compatible:raise RuntimeError('Required approved dependency unavailable: '+name)
            _,wheel=max(compatible);files={}
            with zipfile.ZipFile(wheel) as z:
                info=email.message_from_bytes(z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))))
                for member in z.infolist():
                    rel=Path(member.filename)
                    assert not rel.is_absolute() and '..' not in rel.parts
                    if member.is_dir() or rel.suffix in ('.pyc','.pth'):continue
                    dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);raw=z.read(member);dest.write_bytes(raw);dest.chmod(0o644);files[rel.as_posix()]=hashlib.sha256(raw).hexdigest()
            key=info['Name'].lower().replace('_','-');seen.add(key)
            requires=[]
            for raw in info.get_all('Requires-Dist',[]):
                req=Requirement(raw)
                if req.marker and not req.marker.evaluate({'extra':''}):continue
                queue.append(req.name);requires.append(raw)
            rows.append(dict(name=info['Name'],version=info['Version'],requires=requires,files=files,provider='Approved task wheel',wheel=wheel.name,sha256=hashlib.sha256(wheel.read_bytes()).hexdigest()))
            continue
        key=dist.metadata['Name'].lower().replace('_','-')
        if key in seen:continue
        seen.add(key);files={};base=Path(dist.locate_file('')).resolve()
        for item in dist.files or []:
            rel=Path(str(item))
            if rel.is_absolute() or '..' in rel.parts or rel.suffix in ('.pyc','.pth'):continue
            source=Path(dist.locate_file(item)).resolve()
            if not source.is_relative_to(base) or not source.is_file():continue
            if source.name in ('direct_url.json','RECORD'):continue
            dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
            dest.chmod(0o644);files[rel.as_posix()]=hashlib.sha256(dest.read_bytes()).hexdigest()
        assert files,('Empty dependency distribution',key)
        requires=[]
        for raw in dist.requires or []:
            req=Requirement(raw)
            if req.marker and not req.marker.evaluate({'extra':''}):continue
            installed=metadata.version(req.name)
            assert not req.specifier or installed in req.specifier,(key,raw,installed)
            queue.append(req.name);requires.append(raw)
        rows.append(dict(name=dist.metadata['Name'],version=dist.version,requires=requires,files=files,
            provider='Pinned Kaggle image plus SHA-verified approved official wheel install; no new artifact'))
    return rows


def extra_binaries(root):
    copied={}
    for name in ('sh','ls','wc','tar','gzip','rm','cp','mv','find','head','tail','sed','grep','cat','mkdir','ln','chmod','sleep','timeout','patch','env','uname','xargs'):
        source=shutil.which(name)
        if not source:continue
        paths=[source]
        output=subprocess.check_output(['ldd',source],text=True,stderr=subprocess.STDOUT)
        import re
        paths+=re.findall(r'(?:=>\s*)?(/[^\s()]+)',output)
        for p in paths:
            dest=root/p.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():shutil.copyfile(Path(p).resolve(),dest);dest.chmod(0o755)
        copied[name]=hashlib.sha256(Path(source).read_bytes()).hexdigest()
    return copied


def dependency_libraries(root):
    import re
    copied={}
    for extension in (root/'opt/approved').rglob('*.so'):
        result=subprocess.run(['ldd',str(extension)],capture_output=True,text=True,timeout=20)
        if result.returncode:raise RuntimeError('Cannot inspect approved dependency ELF: '+str(extension))
        assert 'not found' not in result.stdout,('Host ELF dependency unavailable',str(extension))
        for name in re.findall(r'(?:=>\s*)?(/[^\s()]+)',result.stdout):
            source=Path(name);target=root/name.lstrip('/');target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():shutil.copyfile(source.resolve(),target);target.chmod(0o755)
            copied[name]=hashlib.sha256(target.read_bytes()).hexdigest()
    return copied


class SubprocessManager(BaseSandboxManager):
    """Literal organizer dispatch name; tools operate only via confined children."""
    def __init__(self,*,journal,base_dir,timeout_seconds=120,task_wheels=None,**unused):
        self.journal=journal;self.base_dir=Path(base_dir);self.base_dir.mkdir(parents=True,exist_ok=True)
        self.timeout_seconds=timeout_seconds;self.task_wheels=Path(task_wheels) if task_wheels else None
        self._sandboxes={};self.context=None;self.agent_id=None;self._lock=threading.RLock()
        self.registry=self.base_dir/'owned_uids.json';self.entries=[];self.closed=set();self.popens={}
        self.cleanup_records=[]
        libc=ctypes.CDLL(None,use_errno=True)
        assert libc.prctl(36,1,0,0,0)==0,'Subreaper unavailable'
    def initialize(self,files=None):
        if not self._sandboxes:self.start()
        for name,content in (files or {}).items():self.write_file(name,content)
    def run_command(self,command,timeout=120,work_dir=None):
        self.initialize();sid=next(iter(self._sandboxes))
        return self.exec(sid,('cd '+shlex.quote(work_dir)+' && ' if work_dir else '')+command,timeout=timeout)
    def write_file(self,path,content):
        self.initialize();sid=next(iter(self._sandboxes));target=path if str(path).startswith('/') else '/workspace/'+str(path)
        _,error,code,_,_=self._process(sid,'write',target,data=content.encode() if isinstance(content,str) else content)
        if code:raise OSError(error.decode(errors='replace'))
    def read_file(self,path):
        self.initialize();sid=next(iter(self._sandboxes));target=path if str(path).startswith('/') else '/workspace/'+str(path)
        raw,error,code,_,_=self._process(sid,'read',target)
        if code:raise OSError(error.decode(errors='replace'))
        return raw.decode()
    def reset(self):self.cleanup_all()
    def close(self):self.cleanup_all()
    @property
    def sandboxes(self):return dict(self._sandboxes)
    @property
    def work_dir(self):return '/workspace'
    def start(self):
        import psutil
        occupied={p.info['uids'].real for p in psutil.process_iter(['uids']) if p.info['uids']}
        used=occupied|{e['uid'] for e in self.entries}
        leases=Path('/tmp/ure_owned_uid_leases');leases.mkdir(mode=0o700,exist_ok=True)
        assert leases.stat().st_uid==0 and leases.stat().st_mode&0o077==0
        uid=next(n for n in range(20000,60000) if n not in used and not (leases/str(n)).exists())
        sid=uuid.uuid4().hex[:12];root=self.base_dir/sid
        entry=dict(uid=uid,started_epoch=time.time(),sid=sid,root=str(root.resolve()),token=uuid.uuid4().hex,lease=str(leases/str(uid)))
        with (leases/str(uid)).open('x') as stream:json.dump(entry,stream);stream.flush();os.fsync(stream.fileno())
        (leases/str(uid)).chmod(0o600)
        self.entries.append(entry);atomic_json(self.registry,dict(kind='URE_OWNED_UID_REGISTRY_V1',entries=self.entries));self.registry.chmod(0o600)
        runtime=prepare_runtime(root);runtime['extra_binaries']=extra_binaries(root)
        if not (root/'bin/sh').exists():(root/'bin/sh').symlink_to('/usr/bin/sh')
        # Kaggle host instrumentation is not part of task dependencies and must
        # not execute in the Agent interpreter. Preserve its identity only.
        removed=[]
        for name in ('sitecustomize.py','usercustomize.py'):
            for p in list(root.rglob(name)):
                removed.append(dict(path=str(p.relative_to(root)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()));p.unlink()
        runtime['excluded_host_python_customization']=removed
        dependencies=dependency_copy(root,self.task_wheels)
        runtime['dependency_ELF_libraries']=dependency_libraries(root)
        for name in ('workspace','tmp'):os.chown(root/name,uid,uid)
        if self.task_wheels:
            (root/'wheels').mkdir()
            for p in self.task_wheels.glob('*.whl'):shutil.copyfile(p,root/'wheels'/p.name)
        bin=root/'usr/local/bin';bin.mkdir(parents=True,exist_ok=True)
        for name in ('pytest','py.test'):
            p=bin/name;p.write_text('#!/bin/sh\nexec python3 -m pytest "$@"\n');p.chmod(0o755)
        self._sandboxes[sid]=dict(root=root,workspace=root/'workspace',tmp=root/'tmp',venv=root/'opt/approved',wheels=root/'wheels',uid=uid,entry=entry)
        self.popens[sid]=set()
        if self.agent_id is None:self.agent_id=sid
        atomic_json(self.journal.directory/('runtime_'+sid+'.json'),dict(runtime=runtime,dependencies=dependencies,uid=uid))
        return sid
    def _process(self,sid,mode,argument,data=None,timeout=None):
        helper=Path(__file__).with_name('chroot_child.py');paths=self._sandboxes[sid]
        argv=[sys.executable,'-I','-S',str(helper),str(paths['root']),str(paths['uid']),mode,argument]
        with self._lock:
            assert sid not in self.closed,'Sandbox closing'
            p=subprocess.Popen(argv,cwd=paths['root'],env={'PATH':'/usr/local/bin:/usr/bin:/bin'},stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True,start_new_session=True)
            self.popens[sid].add(p)
        begin=time.monotonic();timed=False
        try:
            try:stdout,stderr=p.communicate(data,timeout=timeout or self.timeout_seconds)
            except subprocess.TimeoutExpired:
                timed=True
                if p.poll() is None:
                    with contextlib.suppress(ProcessLookupError):os.killpg(p.pid,signal.SIGKILL)
                kill_owned(paths['entry']);stdout,stderr=p.communicate(timeout=5)
            return stdout,stderr,p.returncode,timed,time.monotonic()-begin
        finally:
            if p.poll() is None:
                with contextlib.suppress(ProcessLookupError):os.killpg(p.pid,signal.SIGKILL)
            killed=kill_owned(paths['entry'])
            with self._lock:self.popens[sid].discard(p)
            self.journal.append(dict(kind='chroot_process_cleanup',sid=sid,wrapper_pid=p.pid,killed_owned_uid_pids=killed))
    def exec(self,sid,command,*,timeout=None):
        stdout,stderr,code,timed,elapsed=self._process(sid,'exec',command,timeout=timeout)
        out=stdout.decode(errors='replace');err=stderr.decode(errors='replace')
        self.journal.append(dict(kind='chroot_exec',sid=sid,command_sha256=hashlib.sha256(command.encode()).hexdigest(),exit_code=code,timed_out=timed))
        if 'CHROOT_SETUP_FAILED' in err:raise RuntimeError(err)
        return ExecutionResult(status='timeout' if timed else 'ok' if code==0 else 'error',exit_code=124 if timed else code,
            stdout=out,stderr=err,duration_seconds=elapsed)
    def copy_to(self,sid,src,dst):
        source=Path(src);assert source.is_file(),'Trusted directory transfer not required: wheels pre-staged'
        target=str(dst).rstrip('/')+'/'+source.name if str(dst) in ('/tmp','/workspace','/wheels') or str(dst).endswith('/') else str(dst)
        _,error,code,_,_=self._process(sid,'write',target,data=source.read_bytes())
        if code:raise OSError(error.decode(errors='replace'))
    def copy_from(self,sid,src,dst):
        raw,error,code,_,_=self._process(sid,'read',str(src))
        if code:raise OSError(error.decode(errors='replace'))
        Path(dst).write_bytes(raw)
    def stop(self,sid):
        if sid not in self._sandboxes:return
        with self._lock:
            self.closed.add(sid)
            for p in self.popens[sid]:
                if p.poll() is None:
                    with contextlib.suppress(ProcessLookupError):os.killpg(p.pid,signal.SIGKILL)
            entry=self._sandboxes[sid]['entry']
        killed=kill_owned(entry)
        for p in list(self.popens[sid]):
            with contextlib.suppress(subprocess.TimeoutExpired):p.wait(timeout=5)
        root=self._sandboxes[sid]['root'];shutil.rmtree(root)
        self._sandboxes.pop(sid)
        self.cleanup_records.append(dict(sid=sid,uid=entry['uid'],root_removed=not root.exists(),killed=killed))
        atomic_json(self.journal.directory/'chroot_cleanup.json',self.cleanup_records)
    def cleanup_all(self):
        for sid in list(self._sandboxes):self.stop(sid)
