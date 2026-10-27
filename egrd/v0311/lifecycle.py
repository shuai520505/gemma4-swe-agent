"""Finish only journal-owned partial roots and UID leases; no host-wide cleanup."""
import json
from pathlib import Path
import shutil

from egrd.v031.prepare import write


def release_owned(entry, base_dir, kill):
    base = Path(base_dir).resolve()
    root = Path(entry['root'])
    lease = Path(entry['lease'])
    assert not root.is_symlink() and root.resolve().parent == base
    owner = json.loads(lease.read_bytes())
    assert owner['token'] == entry['token'] and owner['uid'] == entry['uid']
    killed = kill(entry)
    if root.exists():
        shutil.rmtree(root)
    lease.unlink()
    return {'sid': entry['sid'], 'uid': entry['uid'], 'root_removed': not root.exists(),
            'lease_removed': not lease.exists(), 'killed': killed}


def finish_session(transport, manager, output):
    try:
        write(Path(output) / 'SCRIPTED_HTTP_REQUESTS.json', transport.calls)
    finally:
        try:
            if manager:
                manager.cleanup_all()
        finally:
            transport.stop()
            write(Path(output) / 'TRANSPORT_CLEANUP.json', {'complete': transport.cleaned})
