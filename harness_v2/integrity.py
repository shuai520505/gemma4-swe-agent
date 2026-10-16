"""Protect prior evidence, registered Pilot 01 protocol, and both candidates."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def verify_baseline(root=ROOT):
    data=json.loads((root/'harness_v2/frozen_baseline.json').read_text(encoding='utf-8'))
    for name,digest in data['files'].items():
        p=root/name
        if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Frozen baseline changed: {name}')
    from experiments.prepare import verify_frozen
    verify_frozen(root)
    return len(data['files'])
