"""Bind pip commands to the organizer's per-sandbox Python, including fallback venvs."""
import json
from pathlib import Path
import shlex
import subprocess


def prepare_pip_entrypoints(venv_dir):
    venv_dir=Path(venv_dir)
    python=venv_dir/'bin/python3'
    probe=subprocess.run([str(python),'-c',
        'import json,sys,pip; print(json.dumps(dict(prefix=sys.prefix,pip_module=pip.__file__,python_version=f"{sys.version_info.major}.{sys.version_info.minor}")))'],
        text=True,capture_output=True,timeout=30,check=True)
    result=json.loads(probe.stdout)
    if Path(result['prefix']).resolve()!=venv_dir.resolve():
        raise RuntimeError('Sandbox Python does not use its registered virtual environment; installation forbidden')
    # A fallback venv can import shared pip but have no local pip executable.
    # PATH would then select the host's pip shebang and mutate shared packages.
    # These local launchers retain sys.prefix=venv even when pip itself is shared.
    script='#!/bin/sh\nexec '+shlex.quote(str(python))+' -m pip "$@"\n'
    for name in ('pip','pip3','pip'+result['python_version']):
        path=venv_dir/'bin'/name
        if path.is_symlink():
            path.unlink()  # Never follow an inherited executable link when writing.
        path.write_text(script,encoding='utf-8',newline='\n')
        path.chmod(0o755)
    # Shared pytest executables also carry a host Python shebang. Keep bare
    # pytest commands on the same interpreter as the per-sandbox installation.
    for name in ('pytest','py.test'):
        path=venv_dir/'bin'/name
        if path.is_symlink(): path.unlink()
        path.write_text('#!/bin/sh\nexec '+shlex.quote(str(python))+' -m pytest "$@"\n',encoding='utf-8',newline='\n')
        path.chmod(0o755)
    return dict(**result,entrypoints_bound=True)
