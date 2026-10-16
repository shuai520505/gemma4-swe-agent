"""Crash-tolerant append-only journal and content-addressed Patch checkpoints."""
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import uuid


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with tmp.open('xb') as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_json(path, data):
    atomic_bytes(path, (json.dumps(data, indent=2, default=str) + '\n').encode())


def read_events(path):
    if not Path(path).exists():
        return []
    rows=[]
    for line in Path(path).read_bytes().splitlines():
        try:
            rows.append(json.loads(line))
        except (ValueError, UnicodeDecodeError):
            # A killed process may leave only its final append incomplete.
            break
    return rows


class Journal:
    def __init__(self, directory):
        self.directory=Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock=threading.RLock()
        self.state={}

    def append(self, event, filename='events.jsonl'):
        with self.lock:
            row=dict(recorded_monotonic=time.monotonic(), **event)
            with (self.directory/filename).open('ab') as f:
                f.write((json.dumps(row, default=str)+'\n').encode())
                f.flush(); os.fsync(f.fileno())

    def stage(self, name, **details):
        with self.lock:
            now=time.monotonic()
            # Repeated progress updates do not reset the phase deadline.
            if self.state.get('stage') != name:
                self.state.update(stage=name, stage_started_monotonic=now)
            self.state.update(details)
            self.append(dict(kind='stage', stage=name, **details))
            atomic_json(self.directory/'progress.json', self.state)

    def patch(self, text, *, source):
        if text is None:
            return
        data=text.encode('utf-8')
        digest=hashlib.sha256(data).hexdigest()
        with self.lock:
            p=self.directory/'patches'/f'{digest}.patch'
            p.parent.mkdir(exist_ok=True)
            if not p.exists():
                with p.open('xb') as f:
                    f.write(data); f.flush(); os.fsync(f.fileno())
                self.append(dict(kind='patch', source=source, sha256=digest, bytes=len(data)))
            atomic_bytes(self.directory/'latest.patch', data)


def bundle(directory):
    """Never replace an evidence ZIP; include a manifest of stable final files."""
    import zipfile
    directory=Path(directory)
    archive=directory.with_suffix('.zip')
    if archive.exists():
        raise FileExistsError(archive)
    files=[p for p in sorted(directory.rglob('*')) if p.is_file() and not p.is_symlink()
           and 'sandbox_tmp' not in p.relative_to(directory).parts]
    hashes={p.relative_to(directory).as_posix():dict(bytes=p.stat().st_size,
        sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files}
    atomic_json(directory/'evidence_manifest.json', hashes)
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in files+[directory/'evidence_manifest.json']:
            z.write(p,p.relative_to(directory).as_posix())
    return archive
