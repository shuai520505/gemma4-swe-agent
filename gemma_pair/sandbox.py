"""Minimal recovery wrapper around PR39's unchanged research adapter."""
import json
import shlex

from .sandbox_base import SubprocessManager as Prior
from u_re.v01.experiments.action_priority_01.integrated_cpu_01.CHROOT_TASK_RUNTIME import kill_owned
from egrd.v031.prepare import write
from egrd.v0311.lifecycle import release_owned


class SubprocessManager(Prior):
    def start(self):
        previous = len(self.entries)
        try:
            sid = super().start()
            check = """import os,stat
s=os.lstat('/dev/null')
assert stat.S_ISCHR(s.st_mode) and s.st_rdev==os.makedev(1,3)
assert os.environ['GIT_CONFIG_GLOBAL']=='/dev/null'
with open('/dev/null','w') as f:f.write('not valid git configuration\\n')
with open('/dev/null','rb') as f:assert f.read(16)==b''
print('NULL_CHARACTER_DEVICE_AND_GIT_ENV_PASS')
"""
            result = self.exec(sid, 'python3 -c ' + shlex.quote(check) +
                               ' && git config --global --list', timeout=10)
            write(self.journal.directory / ('DEVICE_GIT_' + sid + '.json'),
                  dict(exit_code=result.exit_code, stdout=result.stdout, stderr=result.stderr))
            assert result.exit_code == 0 and 'NULL_CHARACTER_DEVICE_AND_GIT_ENV_PASS' in result.stdout
            return sid
        except BaseException:
            for entry in self.entries[previous:]:
                if entry['sid'] in self.sandboxes:
                    self.stop(entry['sid'])
                elif __import__('pathlib').Path(entry['lease']).exists():
                    record = release_owned(entry, self.base_dir, kill_owned)
                    self.cleanup_records.append(dict(record, partial_start=True))
            write(self.journal.directory / 'RECOVERY_CLEANUP.json', self.cleanup_records)
            raise

    def stop(self, sid):
        entry = self.sandboxes.get(sid, {}).get('entry')
        super().stop(sid)
        if entry:
            record = release_owned(entry, self.base_dir, kill_owned)
            self.cleanup_records.append(dict(record, recovery_lease_release=True))
            write(self.journal.directory / 'RECOVERY_CLEANUP.json', self.cleanup_records)
