"""Read-only integrity snapshots of the original checkout and this branch base."""
import argparse
import json
from pathlib import Path
import subprocess
from .util import sha_file,save

ROOT=Path(__file__).resolve().parents[1]


def tracked(directory):
    names=subprocess.check_output(['git','ls-files','-z'],cwd=directory).decode().split('\0')
    return {n:sha_file(directory/n) for n in names if n and not n.startswith('s1/') and (directory/n).is_file()}


def capture(original):
    original=Path(original)
    data=dict(original_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=original).decode().strip(),
        base_head='972d1dd940db3910dd78685d6e37152e96ab514b',
        original_tracked=tracked(original),base_worktree_tracked=tracked(ROOT))
    raw=[p for p in (original/'artifacts/formal-paired-01').rglob('*.zip') if 'files/formal_paired_01' in p.as_posix()]
    raw+=[p for p in (original/'artifacts').glob('cure-gpu-mechanism-*/**/*.zip') if '/output' in p.as_posix() and '/files/' in p.as_posix()]
    data['historical_raw_archives']={p.relative_to(original).as_posix():sha_file(p) for p in raw}
    save(ROOT/'s1/frozen_integrity.json',data)
    return data


def verify(original):
    original=Path(original)
    data=json.loads((ROOT/'s1/frozen_integrity.json').read_text())
    checked=0
    for directory,key in [(original,'original_tracked'),(ROOT,'base_worktree_tracked'),(original,'historical_raw_archives')]:
        for n,digest in data[key].items():
            assert sha_file(directory/n)==digest,n
            checked+=1
    return dict(passed=True,checked=checked,original_head=data['original_head'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['capture','verify']);p.add_argument('original')
    a=p.parse_args();print(json.dumps(capture(a.original) if a.action=='capture' else verify(a.original),indent=2))
