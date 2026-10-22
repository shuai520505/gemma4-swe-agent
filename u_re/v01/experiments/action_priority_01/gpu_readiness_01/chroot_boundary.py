"""Small synthetic research adapter for unchanged organizer tool functions.

All untrusted read/write/command paths run inside the same chroot. This copies a
minimal stdlib runtime, not a general task dependency image or GPU deployment.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import sysconfig


def prepare_runtime(root):
    root=Path(root);root.mkdir(mode=0o755)
    copied={}
    def copy_binary(path):
        path=Path(path);target=root/str(path).lstrip('/');target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            shutil.copyfile(path.resolve(),target);target.chmod(0o755)
            copied[str(path)]=hashlib.sha256(target.read_bytes()).hexdigest()
        output=subprocess.check_output(['ldd',str(path)],text=True,stderr=subprocess.STDOUT)
        for dep in re.findall(r'(?:=>\s*)?(/[^\s()]+)',output):
            source=Path(dep);dest=root/str(source).lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():shutil.copyfile(source.resolve(),dest);dest.chmod(0o755)
    for binary in ('/bin/bash','/usr/bin/git','/usr/bin/mkdir','/usr/bin/cat',sys.executable):copy_binary(binary)
    stdlib=Path(sysconfig.get_path('stdlib'))
    destination=root/str(stdlib).lstrip('/')
    shutil.copytree(stdlib,destination,dirs_exist_ok=True,symlinks=False,
        ignore=shutil.ignore_patterns('site-packages','dist-packages','__pycache__','test','tests','idlelib','tkinter','ensurepip'))
    for extension in destination.rglob('*.so'):
        # Dependencies of stdlib extensions must also exist in the new root.
        original=Path('/')/extension.relative_to(root)
        copy_binary(original)
    python_path=str(Path(sys.executable))
    alias=root/'usr/bin/python3';alias.parent.mkdir(parents=True,exist_ok=True)
    if not alias.exists():alias.symlink_to(python_path)
    for name,mode in (('workspace',0o755),('tmp',0o777),('dev',0o755)):
        (root/name).mkdir(exist_ok=True);(root/name).chmod(mode)
    os.chown(root/'workspace',65534,65534)
    (root/'dev/null').touch();(root/'dev/null').chmod(0o666)
    # No /proc,host input,data,history,credentials,device nodes,sockets or mounts.
    return dict(binary_sha256=copied,stdlib_source=str(stdlib),host_mounts=[],proc_mounted=False)


class ChrootToolBoundary:
    def __init__(self,root,journal):
        self.root=Path(root);self.journal=Path(journal);self.calls=[]
        self.runtime=prepare_runtime(self.root)
    def exec(self,container_id,command,*,timeout=None):
        from adk_eval_core.sandbox import execute_subprocess_command
        assert container_id=='owned-chroot'
        helper=Path(__file__).with_name('chroot_exec.py')
        result=execute_subprocess_command([sys.executable,'-I','-S',str(helper),str(self.root),command],
            cwd=self.root,env={'PATH':'/usr/local/bin:/usr/bin:/bin','LANG':'C.UTF-8'},timeout=timeout or 120,shell=False)
        self.calls.append(dict(command_sha256=hashlib.sha256(command.encode()).hexdigest(),exit_code=result.exit_code,
            stdout=result.stdout,stderr=result.stderr,timeout=timeout or 120))
        self.journal.write_text(json.dumps(self.calls,indent=2)+'\n')
        if 'CHROOT_SETUP_FAILED' in result.stderr:raise RuntimeError('Mandatory chroot child setup failed')
        return result
    def copy_from(self,container_id,src,dest):
        # Do NOT resolve/copy an attacker-controlled symlink from the host.
        code='import base64,pathlib;print(base64.b64encode(pathlib.Path('+repr(str(src))+').read_bytes()).decode())'
        r=self.exec(container_id,'python3 -c '+shlex.quote(code))
        if r.exit_code:raise OSError('Confined read rejected: '+r.stderr)
        Path(dest).write_bytes(base64.b64decode(r.stdout.strip(),validate=True))
    def copy_to(self,container_id,src,dest):
        source=Path(src);assert source.is_file(),'Synthetic adapter accepts trusted single files only'
        target=str(dest)+source.name if str(dest).endswith('/') else str(dest)
        data=base64.b64encode(source.read_bytes()).decode()
        code='import base64,pathlib;pathlib.Path('+repr(target)+').write_bytes(base64.b64decode('+repr(data)+'))'
        r=self.exec(container_id,'python3 -c '+shlex.quote(code))
        if r.exit_code:raise OSError('Confined write rejected: '+r.stderr)
    def cleanup(self):
        assert self.root.name=='chroot' and self.root.parent.is_dir()
        shutil.rmtree(self.root)
