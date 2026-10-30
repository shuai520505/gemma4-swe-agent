"""Trusted clean helper; untrusted paths/files are opened after confinement."""
import ctypes
import importlib.util
import os
from pathlib import Path
import sys


def main():
    spec=importlib.util.spec_from_file_location('owned_seccomp',Path(__file__).with_name('landlock_exec.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    root=Path(sys.argv[1]).resolve(strict=True);uid=int(sys.argv[2]);mode=sys.argv[3];argument=sys.argv[4]
    assert os.geteuid()==0 and 20000<=uid<60000 and mode in ('exec','read','write')
    libc=m.library();os.chroot(root);os.chdir('/workspace')
    os.setgroups([]);os.setresgid(uid,uid,uid);os.setresuid(uid,uid,uid)
    m.checked(libc.capset(ctypes.byref(m.CapHeader(0x20080522,0)),ctypes.byref((m.CapData*2)())),'drop capabilities')
    m.checked(libc.prctl(38,1,0,0,0),'no_new_privs');m.seccomp(libc);os.closerange(3,65536)
    if mode=='read':sys.stdout.buffer.write(Path(argument).read_bytes());return
    if mode=='write':Path(argument).write_bytes(sys.stdin.buffer.read());return
    os.close(0);assert os.open('/dev/null',os.O_RDONLY)==0
    env=dict(PATH='/usr/local/bin:/usr/bin:/bin',HOME='/tmp',LANG='C.UTF-8',PYTHONPATH='/workspace:/opt/approved',
        PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',TMPDIR='/tmp',
        GIT_AUTHOR_NAME='Research',GIT_AUTHOR_EMAIL='cpu@example.invalid',GIT_COMMITTER_NAME='Research',GIT_COMMITTER_EMAIL='cpu@example.invalid',PIP_NO_INDEX='1',
        LD_LIBRARY_PATH=':'.join(str(p) for p in Path('/opt/approved').glob('*.libs') if p.is_dir()))
    os.execve('/bin/bash',['/bin/bash','-c',argument],env)


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        print('CHROOT_SETUP_FAILED',type(exc).__name__,getattr(exc,'errno',None),file=sys.stderr);sys.exit(126)
