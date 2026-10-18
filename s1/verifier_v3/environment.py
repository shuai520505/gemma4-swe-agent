"""Read native JUnit bytes before native sandbox cleanup; command/result unchanged."""
from contextlib import contextmanager
from functools import partial
import hashlib
from pathlib import Path
import re
import shlex
from unittest.mock import patch
from harness_v2.evidence import atomic_bytes,atomic_json
from s1.infrastructure_recovery.environment import SubprocessManager as RecoveryManager, research_environment as recovery_environment


class SubprocessManager(RecoveryManager):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.junit_paths={}

    def start(self):
        sid=super().start()
        try:
            from s1.infrastructure_recovery.import_audit import install
            proof=install(self.sandboxes[sid]['venv'])
            runtime=Path(__file__).with_name('import_runtime.py').read_bytes()
            target=Path(proof['site'])/'_s1_import_audit.py'
            atomic_bytes(target,runtime)
            self.journal.append(dict(kind='import_observer_v3',sandbox_id=sid,
                sha256=hashlib.sha256(runtime).hexdigest(),scope='All imported submodules of registered audit prefixes'))
        except BaseException:
            super().stop(sid);raise
        return sid

    def capture(self,sandbox_id,phase):
        target=self.junit_paths.get(sandbox_id)
        if not target:return
        directory=self.journal.directory
        try:
            paths=self.sandboxes[sandbox_id];tmp=paths['tmp'].resolve()
            file=(tmp/Path(target).name).resolve()
            assert file.is_relative_to(tmp) and not file.is_symlink()
            metadata=dict(sandbox_id=sandbox_id,original_junit_path=target,
                sandbox_exists_at_capture=True,capture_phase=phase,workspace_realpath=str(paths['workspace'].resolve()),
                raw_file_present=file.is_file(),status='missing')
            if file.is_file():
                raw=file.read_bytes();assert len(raw)<=16*1024*1024
                atomic_bytes(directory/'phase2.junit.xml',raw)
                metadata.update(status='captured',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
                assert (directory/'phase2.junit.xml').read_bytes()==raw
            # Full source hashes aid conservative error attribution. This is a
            # passive read of evaluator workspace bytes, not a new Agent tool.
            metadata['production_source_hashes']={p.relative_to(paths['workspace']).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in paths['workspace'].rglob('*.py') if not {'tests','test','.git','.venv','__pycache__'}.intersection(p.relative_to(paths['workspace']).parts)}
            atomic_json(directory/'phase2_junit_capture.json',metadata)
            self.journal.append(dict(kind='native_JUnit_capture',**{k:v for k,v in metadata.items() if k!='production_source_hashes'}))
        except Exception as exc:
            # Never mask native execution exceptions/cancellation. Missing or
            # invalid durable capture fails the external evidence gate instead.
            try:atomic_json(directory/'phase2_junit_capture.json',dict(status='capture_error',error=repr(exc)))
            except OSError:pass

    def exec(self,sandbox_id,command,*,timeout=None):
        native_test=sandbox_id!=self.agent_id and ' -m pytest ' in command
        if native_test:
            tokens=shlex.split(command)
            junit=[t.split('=',1)[1] for t in tokens if t.startswith('--junitxml=')]
            if len(junit)==1 and re.fullmatch(r'/tmp/_swegemma_junit_[a-f0-9]+\.xml',junit[0]):
                self.junit_paths[sandbox_id]=junit[0]
            atomic_json(self.journal.directory/'phase2_command.json',dict(command=command,
                command_sha256=hashlib.sha256(command.encode()).hexdigest(),native_command_unchanged=True,sandbox_id=sandbox_id))
        try:return super().exec(sandbox_id,command,timeout=timeout)
        finally:
            if native_test:self.capture(sandbox_id,'after_native_pytest_return')

    def stop(self,sandbox_id):
        self.capture(sandbox_id,'before_native_sandbox_stop')
        return super().stop(sandbox_id)


@contextmanager
def research_environment(*,audit_modules=('rich',),task_wheels=None):
    with recovery_environment(audit_modules=audit_modules,task_wheels=task_wheels):
        with patch('harness_v2.official.DurableManager',partial(SubprocessManager,
            audit_modules=tuple(audit_modules),task_wheels=task_wheels)):
            yield
