"""Fail-closed null device for the research chroot, not an Agent feature."""
import os
import stat


def install_null_device(root):
    null=root/'dev/null'
    assert not null.is_symlink(),'Unexpected device symlink'
    if null.exists():null.unlink()
    # A regular file is not a /dev/null substitute: shell redirections persist
    # bytes and corrupt Git's GIT_CONFIG_GLOBAL=/dev/null input in the child.
    os.mknod(null,stat.S_IFCHR | 0o666,os.makedev(1,3))
    null.chmod(0o666)
    observed=null.stat()
    assert stat.S_ISCHR(observed.st_mode) and observed.st_rdev==os.makedev(1,3)
    return dict(kind='CHAR_DEVICE',major=1,minor=3,regular_file_fallback=False)
