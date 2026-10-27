"""Research-only filesystem adapter; native Runner/tools and S0 remain unchanged.

Reuse the accepted non-root chroot helper. Replace its generic task dependency
surface with the exact three pinned Django development wheels, not host packages.
This is not competitor-side orchestration, a callback, or a model controller.
"""
import json
from pathlib import Path
import shutil
import subprocess
import re
import os
import time
import uuid
import zipfile

from u_re.v01.experiments.action_priority_01.integrated_cpu_01.CHROOT_TASK_RUNTIME import (
    SubprocessManager as Accepted,prepare_runtime,extra_binaries,dependency_libraries)
from .prepare import sha,write
from .device_runtime import install_null_device


class SubprocessManager(Accepted):
    def start(self):
        import psutil
        occupied={p.info['uids'].real for p in psutil.process_iter(['uids']) if p.info['uids']}
        leases=Path('/tmp/ure_owned_uid_leases');leases.mkdir(mode=0o700,exist_ok=True)
        assert leases.stat().st_uid==0 and leases.stat().st_mode&0o077==0
        used=occupied|{e['uid'] for e in self.entries}
        uid=next(n for n in range(20000,60000) if n not in used and not (leases/str(n)).exists())
        sid=uuid.uuid4().hex[:12];root=self.base_dir/sid
        owned=dict(uid=uid,started_epoch=time.time(),sid=sid,root=str(root.resolve()),
            token=uuid.uuid4().hex,lease=str(leases/str(uid)))
        with (leases/str(uid)).open('x') as stream:json.dump(owned,stream);stream.flush();os.fsync(stream.fileno())
        (leases/str(uid)).chmod(0o600);self.entries.append(owned)
        write(self.registry,dict(kind='URE_OWNED_UID_REGISTRY_V1',entries=self.entries));self.registry.chmod(0o600)
        try:
            runtime=prepare_runtime(root)
            runtime['null_device']=install_null_device(root)
            runtime['extra_binaries']=extra_binaries(root)
            if not (root/'bin/sh').exists():(root/'bin/sh').symlink_to('/usr/bin/sh')
            removed=[]
            for name in ('sitecustomize.py','usercustomize.py'):
                for p in root.rglob(name):
                    removed.append(dict(path=str(p.relative_to(root)),sha256=sha(p.read_bytes())));p.unlink()
            runtime['excluded_host_python_customization']=removed
            target=root/'opt/approved';target.mkdir(parents=True)
            supplied=[]
            for wheel in sorted(self.task_wheels.glob('*.whl')):
                with zipfile.ZipFile(wheel) as archive:
                    assert archive.testzip() is None
                    for info in archive.infolist():
                        name=Path(info.filename)
                        assert not name.is_absolute() and '..' not in name.parts
                        if info.is_dir() or name.suffix in ('.pth','.pyc'):continue
                        dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True)
                        dest.write_bytes(archive.read(info));dest.chmod(0o644)
                supplied.append(dict(name=wheel.name,sha256=sha(wheel.read_bytes())))
            assert len(supplied)==3
            runtime['dependency_ELF_libraries']=dependency_libraries(root)
            # The native workspace-layout command uses these ordinary Unix
            # programs; the old minimal adapter did not include them.
            for name in ('awk','sort','cut'):
                binary=shutil.which(name);assert binary,name
                linked=subprocess.check_output(['ldd',binary],text=True,stderr=subprocess.STDOUT)
                for item in [binary,*re.findall(r'(?:=>\s*)?(/[^\s()]+)',linked)]:
                    dest=root/str(item).lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
                    if not dest.exists():shutil.copyfile(Path(item).resolve(),dest);dest.chmod(0o755)
            for name in ('workspace','tmp'):os.chown(root/name,uid,uid)
            (root/'wheels').mkdir()
            for wheel in self.task_wheels.glob('*.whl'):shutil.copyfile(wheel,root/'wheels'/wheel.name)
            self._sandboxes[sid]=dict(root=root,workspace=root/'workspace',tmp=root/'tmp',
                venv=target,wheels=root/'wheels',uid=uid,entry=owned)
            self.popens[sid]=set()
            if self.agent_id is None:self.agent_id=sid
            write(self.journal.directory/('django_runtime_'+sid+'.json'),dict(wheels=supplied,runtime=runtime,
                generic_FastAPI_dependency_staging_not_executed=True,host_mounts=[],proc_mounted=False,
                trusted_dataset_not_mounted=True,original_child_confinement=True))
            return sid
        except BaseException:
            if sid in self._sandboxes:self.stop(sid)
            elif root.exists():
                assert root.resolve().parent==self.base_dir.resolve() and not root.is_symlink()
                shutil.rmtree(root)
                self.cleanup_records.append(dict(sid=sid,uid=uid,root_removed=not root.exists(),killed=[],partial_start=True))
            raise
