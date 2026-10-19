"""Research subprocess adapters. Never applied to official scoring or Agent ZIPs."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shlex
import uuid
from unittest.mock import patch

from harness_v2.evidence import atomic_json
from harness_v2.official import DurableManager
from .import_audit import install,classify,shell_prefix


class SubprocessManager(DurableManager):
    """Retain the literal native dispatch name and its normal timeout behavior."""
    def __init__(self,*args,audit_modules=('requests','requests.sessions'),task_wheels=None,**kwargs):
        self.audit_modules=tuple(audit_modules)
        self.task_wheels=Path(task_wheels) if task_wheels else None
        super().__init__(*args,**kwargs)

    def start(self):
        sid=super().start()
        try:
            proof=install(self.sandboxes[sid]['venv'])
            self.journal.append(dict(kind='import_observer_installed',sandbox_id=sid,**proof))
        except BaseException:
            super().stop(sid)
            raise
        return sid

    def exec(self,sandbox_id,command,*,timeout=None):
        identity=uuid.uuid4().hex
        directory=self.journal.directory/'import_audit'/identity
        self.journal.append(dict(kind='audited_command',command_id=identity,sandbox_id=sandbox_id,
            original_command_sha256=hashlib.sha256(command.encode()).hexdigest()))
        try:
            return super().exec(sandbox_id,shell_prefix(directory,self.audit_modules)+command,timeout=timeout)
        finally:
            records=[json.loads(p.read_text()) for p in directory.glob('*.json')] if directory.exists() else []
            workspace=self.sandboxes.get(sandbox_id,{}).get('workspace')
            verdict=classify(records,workspace) if workspace else dict(status='unknown',reason='sandbox gone')
            atomic_json(self.journal.directory/'import_verdicts'/(identity+'.json'),dict(command_id=identity,**verdict))


def install_editable(manager,sandbox_id):
    """Equivalent install flags to the native Docker helper, fail closed locally."""
    if not isinstance(manager,SubprocessManager):
        raise TypeError('Research editable adapter only supports the isolated research manager')
    workspace=manager.sandboxes[sandbox_id]['workspace']
    if not any((workspace/n).exists() for n in ('pyproject.toml','setup.py','setup.cfg')):return
    requirements=[]
    if (workspace/'pyproject.toml').exists():
        import tomllib
        requirements=tomllib.loads((workspace/'pyproject.toml').read_text()).get('build-system',{}).get('requires',[])
    if requirements and manager.task_wheels:
        from .build_dependencies import select
        from s1.util import sha_file
        chosen=[select(req,manager.task_wheels) for req in requirements]
        chosen=[p for p in chosen if p is not None]
        # Explicit wheel paths, no resolver/network, no global pip executable.
        build_command='python3 -m pip install --no-index --no-deps --force-reinstall '+ ' '.join(shlex.quote(str(p)) for p in chosen)
        result=manager.exec(sandbox_id,build_command,timeout=120) if chosen else None
        atomic_json(manager.journal.directory/'build_dependencies'/(sandbox_id+'.json'),dict(
            declared_requirements=requirements,selected_wheels={p.name:sha_file(p) for p in chosen},
            command=build_command,exit_code=result.exit_code if result else 0,
            stdout=result.stdout if result else '',stderr=result.stderr if result else ''))
        if result and result.exit_code:raise RuntimeError('Official cached build dependency installation failed')
    command='python3 -m pip install --no-index --no-build-isolation --no-deps -e /workspace'
    result=manager.exec(sandbox_id,command,timeout=120)
    atomic_json(manager.journal.directory/'editable_installs'/(sandbox_id+'.json'),
        dict(command=command,exit_code=result.exit_code,stdout=result.stdout,stderr=result.stderr))
    if result.exit_code:raise RuntimeError('Research editable installation failed; source provenance unverified')


@contextmanager
def research_environment(*,audit_modules=('requests','requests.sessions'),task_wheels=None):
    # Only in a disposable research worker; restore all bindings on exit. The
    # official verification code, test commands, fixtures and assertions are intact.
    from functools import partial
    with patch('harness_v2.official.DurableManager',partial(SubprocessManager,audit_modules=tuple(audit_modules),task_wheels=task_wheels)),patch(
        'swegemma.harness.agent_runner.install_editable_package',install_editable),patch(
        'swegemma.harness.verification.install_editable_package',install_editable):
        yield
