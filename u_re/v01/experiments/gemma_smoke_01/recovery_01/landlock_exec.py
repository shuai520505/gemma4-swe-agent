"""Linux x86-64 tool-child confinement, stdlib only; unsupported kernels fail closed.

Not a VM/kernel exploit defence. Filesystem data access is enforced by Landlock;
seccomp blocks cross-process/handle/mount escapes and external socket connects.
"""
import ctypes as C
import errno
import json
import os
from pathlib import Path
import platform
import sys

EXECUTE=1; WRITE=2; READ=4; READDIR=8; REFER=1<<13; TRUNCATE=1<<14
HANDLED=(1<<15)-1
RO=EXECUTE|READ|READDIR
RW=HANDLED & ~((1<<6)|(1<<11))  # no device-node creation
WRITE_ONLY=WRITE|TRUNCATE|(1<<7)|(1<<8)
SYS_CREATE=444;SYS_ADD=445;SYS_RESTRICT=446

class Ruleset(C.Structure):_fields_=[('handled_access_fs',C.c_uint64)]
class Beneath(C.Structure):
    _pack_=1
    _fields_=[('allowed_access',C.c_uint64),('parent_fd',C.c_int32)]
class Filter(C.Structure):_fields_=[('code',C.c_ushort),('jt',C.c_ubyte),('jf',C.c_ubyte),('k',C.c_uint)]
class Program(C.Structure):_fields_=[('length',C.c_ushort),('filter',C.POINTER(Filter))]
class CapHeader(C.Structure):_fields_=[('version',C.c_uint32),('pid',C.c_int)]
class CapData(C.Structure):_fields_=[('effective',C.c_uint32),('permitted',C.c_uint32),('inheritable',C.c_uint32)]

def library():
    if sys.platform!='linux' or platform.machine()!='x86_64':raise RuntimeError('Require Linux x86_64')
    libc=C.CDLL(None,use_errno=True);libc.syscall.restype=C.c_long;return libc

def checked(value,operation):
    if value<0:raise OSError(C.get_errno(),operation)
    return value

def probe():
    libc=library()
    abi=checked(libc.syscall(SYS_CREATE,0,0,1),'Landlock ABI unavailable')
    if abi<3:raise RuntimeError('Require Landlock ABI>=3 including REFER/TRUNCATE')
    return dict(abi=abi,architecture=platform.machine(),minimum_abi=3)

def seccomp(libc):
    # Verify audit architecture and reject x32-numbered syscalls before checking x86-64 numbers.
    code=[Filter(0x20,0,0,4),Filter(0x15,1,0,0xc000003e),Filter(0x06,0,0,0x80000000),
          Filter(0x20,0,0,0),Filter(0x35,0,1,0x40000000),Filter(0x06,0,0,0x80000000)]
    deny=(42,101,155,161,165,166,167,168,169,175,176,246,272,298,300,301,303,304,
          308,310,311,313,321,323,425,426,427,428,429,430,431,432,438,440,442,448)
    for nr in deny:code.extend((Filter(0x15,0,1,nr),Filter(0x06,0,0,0x00050000|errno.EACCES)))
    # AF_UNIX socketpair remains available for asyncio self-pipes; TCP/IPv6 creation is denied.
    code.extend((Filter(0x15,0,4,41),Filter(0x20,0,0,16),Filter(0x15,1,0,2),
                 Filter(0x15,0,1,10),Filter(0x06,0,0,0x00050000|errno.EACCES),Filter(0x06,0,0,0x7fff0000)))
    array=(Filter*len(code))(*code);program=Program(len(code),array)
    checked(libc.prctl(22,2,C.byref(program),0,0),'Seccomp install failed')

def apply(rules):
    probe();libc=library()
    checked(libc.prctl(38,1,0,0,0),'no_new_privs failed')
    attr=Ruleset(HANDLED)
    fd=checked(libc.syscall(SYS_CREATE,C.byref(attr),C.sizeof(attr),0),'Landlock ruleset failed')
    try:
        for item in rules:
            path=Path(item['path']).resolve(strict=True)
            allowed=int(item['access'])&HANDLED
            if not path.is_dir():allowed &= EXECUTE|READ|WRITE|TRUNCATE
            opened=os.open(path,os.O_PATH|os.O_CLOEXEC)
            try:
                beneath=Beneath(allowed,opened)
                checked(libc.syscall(SYS_ADD,fd,1,C.byref(beneath),0),'Landlock add rule failed')
            finally:os.close(opened)
        checked(libc.syscall(SYS_RESTRICT,fd,0),'Landlock restrict failed')
    finally:os.close(fd)
    seccomp(libc)

def main():
    if len(sys.argv)<4:raise RuntimeError('Policy and original executable/arguments required')
    policy=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    command=sys.argv[2:]
    if command[:2]!=['/bin/bash','-c'] or len(command)!=3:raise RuntimeError('Unexpected organizer exec shape')
    # Drop to a separate OS identity with no capabilities before executing untrusted code.
    if os.geteuid()!=0:raise RuntimeError('Trusted host must support explicit UID separation')
    os.setgroups([]);os.setresgid(policy['gid'],policy['gid'],policy['gid'])
    os.setresuid(policy['uid'],policy['uid'],policy['uid'])
    header=CapHeader(0x20080522,0);data=(CapData*2)()
    checked(library().capset(C.byref(header),C.byref(data)),'Capability drop failed')
    # Policy file and launcher live outside the tool-visible roots. No private fds survive exec.
    apply(policy['rules'])
    os.execve(command[0],command,os.environ.copy())

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        print('ISOLATION_SETUP_FAILED',type(exc).__name__,getattr(exc,'errno',None),file=sys.stderr)
        sys.exit(126)
