"""First mandatory real-kernel gate, before SDK installation or Agent execution."""
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

from egrd.v031.device_runtime import install_null_device
from egrd.v031.prepare import write


def verify_node(path):
    info = path.lstat()
    assert not stat.S_ISLNK(info.st_mode), 'Null path is a symlink'
    assert stat.S_ISCHR(info.st_mode), 'Null path is not a character device'
    assert info.st_rdev == os.makedev(1, 3), 'Null device number mismatch'
    return {'character_device': True, 'major': os.major(info.st_rdev),
            'minor': os.minor(info.st_rdev), 'symlink': False,
            'regular_file': False, 'mode': oct(stat.S_IMODE(info.st_mode))}


def run(output):
    output = Path(output)
    root = output / 'device-gate-root'
    root.mkdir(mode=0o755)
    (root / 'dev').mkdir(mode=0o755)
    record = {'status': 'NOT_COMPLETE', 'GPU': 0, 'real_Gemma_requests': 0,
              'fallback_executed': False, 'cleanup': False}
    try:
        record['install'] = install_null_device(root)
        null = root / 'dev/null'
        record['stat'] = verify_node(null)
        with null.open('wb', buffering=0) as stream:
            assert stream.write(b'invalid git configuration\n') == 26
        with null.open('rb', buffering=0) as stream:
            assert stream.read(16) == b''
        record['host_read_write'] = True
        # Child drops UID/GID before opening the device. No inherited host file
        # descriptor or regular-file substitute is supplied.
        program = """import os,sys,stat
os.setgroups([]);os.setgid(59999);os.setuid(59999)
p=sys.argv[1];s=os.lstat(p)
assert stat.S_ISCHR(s.st_mode) and s.st_rdev==os.makedev(1,3)
with open(p,'wb',buffering=0) as f:assert f.write(b'child')==5
with open(p,'rb',buffering=0) as f:assert f.read(1)==b''
print('NONROOT_NULL_READ_WRITE_PASS')
"""
        child = subprocess.run([sys.executable, '-I', '-S', '-c', program, str(null)],
                               capture_output=True, timeout=10)
        record['child'] = {'returncode': child.returncode,
                           'stdout': child.stdout.decode(errors='replace'),
                           'stderr': child.stderr.decode(errors='replace')}
        assert child.returncode == 0, 'Non-root null device access failed'
        record['status'] = 'NULL_DEVICE_PASS'
    except BaseException as exc:
        record.update(status='NULL_DEVICE_UNAVAILABLE', error_type=type(exc).__name__,
                      errno=getattr(exc, 'errno', None), error=str(exc))
        raise
    finally:
        shutil.rmtree(root)
        record['cleanup'] = not root.exists()
        write(output / 'DEVICE_ACCEPTANCE.json', record)
    return record
