"""Passive Python-source hash observations, not a repair decision mechanism."""
import hashlib
import json
import os
from pathlib import Path
import time


def scan(workspace):
    workspace=Path(workspace);rows={}
    package=workspace/'django'
    if package.is_symlink():return {'django':{'symlink':os.readlink(package)}}
    files=[]
    for directory,dirs,names in os.walk(package,followlinks=False):
        dirs[:]=[n for n in dirs if not (Path(directory)/n).is_symlink()]
        files.extend(Path(directory)/n for n in names if n.endswith('.py'))
    for p in sorted(files):
        name=p.relative_to(workspace).as_posix()
        if p.is_symlink():
            rows[name]={'symlink':__import__('os').readlink(p)};continue
        if not p.is_file():continue
        digest=hashlib.sha256()
        with p.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1048576),b''):digest.update(chunk)
        rows[name]={'sha256':digest.hexdigest(),'bytes':p.stat().st_size}
    return rows


class Tracker:
    def __init__(self,directory,journal,baseline):
        self.directory=Path(directory);self.journal=journal;self.baseline=baseline
        self.previous=None;self.observation=0;self.overhead_seconds=0

    def observe(self,workspace,elapsed,reason):
        start=time.monotonic();current=scan(workspace)
        if self.previous is None:
            assert current==self.baseline,'Agent production source differs before first model request'
            changed=[]
        else:changed=[n for n in sorted(set(current)|set(self.previous)) if current.get(n)!=self.previous.get(n)]
        if changed:
            folder=self.directory/f'{self.observation:04d}';folder.mkdir(parents=True,exist_ok=False)
            for name in changed:
                p=Path(workspace)/name
                if name in current and 'sha256' in current[name] and p.is_file() and not p.is_symlink():
                    assert p.resolve().is_relative_to(Path(workspace).resolve())
                    target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
                    with p.open('rb') as stream:target.write_bytes(stream.read(2*1024*1024))
        self.overhead_seconds+=time.monotonic()-start
        self.journal.append(dict(kind='production_source_observation',observation=self.observation,
            agent_elapsed_seconds=elapsed,reason=reason,changed=changed,
            states={n:current.get(n) for n in changed},
            source_identity=hashlib.sha256(json.dumps(current,sort_keys=True).encode()).hexdigest(),
            observer_cumulative_seconds=self.overhead_seconds,
            coverage='django/**/*.py; observed after actions, not exact edit instant'))
        self.previous=current;self.observation+=1
