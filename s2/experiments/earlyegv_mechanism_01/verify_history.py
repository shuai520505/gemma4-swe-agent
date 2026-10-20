"""Read-only baseline-byte audit, allowing only already-recorded CRLF checkouts."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'fce198a25502a8cd05f70d2f8704c21c25be84b2'


def verify():
    old = json.loads((ROOT / 's2/egv_agenttool_t500_early_v01/HISTORICAL_INTEGRITY_FINAL.json').read_text(encoding='utf-8'))
    approved = {row['path']:row['unchanged_raw_SHA256'] for row in old['preexisting_CRLF_checkout_files']}
    tree = subprocess.check_output(['git','-c','core.longpaths=true','ls-tree','-rz','--full-tree',BASE], cwd=ROOT)
    exceptions = []
    mismatches = []
    zips = {}
    count = 0
    total = 0
    for row in tree.split(b'\0'):
        if not row:
            continue
        header, name = row.split(b'\t', 1)
        mode, kind, digest = header.decode().split()
        assert kind == 'blob'
        name = name.decode()
        raw = (ROOT / name).read_bytes()
        git_sha = lambda b: hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        raw_sha = hashlib.sha256(raw).hexdigest()
        if git_sha(raw) != digest:
            if approved.get(name) == raw_sha and git_sha(raw.replace(b'\r\n',b'\n')) == digest:
                exceptions.append(name)
            else:
                mismatches.append(name)
        if name.endswith('.zip'):
            zips[name] = raw_sha
        count += 1
        total += len(raw)
    assert not mismatches, mismatches
    changed = subprocess.check_output(['git','-c','core.longpaths=true','diff','--name-only',BASE], cwd=ROOT, text=True).splitlines()
    assert all(n.startswith('s2/experiments/earlyegv_mechanism_01/') for n in changed), changed
    return dict(passed=True, baseline_commit=BASE, baseline_files=count, baseline_bytes=total,
        known_CRLF_exceptions=exceptions, mismatches=mismatches, old_ZIP_sha256=zips,
        changed_paths_scoped_to_new_experiment=True)


if __name__ == '__main__':
    result = verify()
    with (HERE / 'HISTORICAL_INTEGRITY_CHECK.json').open('x',encoding='utf-8') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print('Historical baseline preserved:',result['baseline_files'],'files,',len(result['old_ZIP_sha256']),'ZIPs')
