"""Clean tool child: chroot, close descriptors, drop UID/caps, deny escapes."""
import ctypes
import os
from pathlib import Path
import sys


def main():
    # Reuse audited seccomp implementation, never its unavailable Landlock path.
    import importlib.util
    spec=importlib.util.spec_from_file_location('owned_seccomp',Path(__file__).with_name('landlock_exec.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    library,checked,seccomp,CapHeader,CapData=(getattr(module,k) for k in ('library','checked','seccomp','CapHeader','CapData'))
    root=Path(sys.argv[1]).resolve(strict=True);command=sys.argv[2]
    assert os.geteuid()==0 and (root/'workspace').is_dir()
    libc=library()
    os.chroot(root);os.chdir('/workspace')
    os.setgroups([]);os.setresgid(65534,65534,65534);os.setresuid(65534,65534,65534)
    checked(libc.capset(ctypes.byref(CapHeader(0x20080522,0)),ctypes.byref((CapData*2)())),'drop capabilities')
    checked(libc.prctl(38,1,0,0,0),'no_new_privs')
    seccomp(libc)
    # Popen close_fds=True is the normal upstream default; verify no fd>=3
    # survives this helper and disconnect inherited Notebook stdin as well.
    os.closerange(3,65536)
    os.close(0);assert os.open('/dev/null',os.O_RDONLY)==0
    env=dict(PATH='/usr/local/bin:/usr/bin:/bin',HOME='/tmp',LANG='C.UTF-8',
        PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',
        GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',TMPDIR='/tmp')
    os.execve('/bin/bash',['/bin/bash','-c',command],env)


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        print('CHROOT_SETUP_FAILED',type(exc).__name__,getattr(exc,'errno',None),file=sys.stderr);sys.exit(126)
