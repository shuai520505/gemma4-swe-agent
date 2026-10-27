"""Read-only historical checks and isolated recovery paths; never rebuild S0."""
import json
from pathlib import Path
import subprocess
import zipfile

from egrd.v031.prepare import ROOT, S0_SHA, sha, write, arm_input

HERE = Path(__file__).resolve().parent
OLD = ROOT / 'egrd/v031'
PRIVATE = ROOT.parent / 'private-evidence/egrd_v0311'
PRIOR = ROOT.parent / 'private-evidence/egrd_v031'
BASE = '017bb9039c666ae50dcb3447cc8dcdc1f72d8149'
REF = 'wudangdexiaodoashi/egrd-v0311-cpu-runner-recovery'


def verify_history():
    manifest = json.loads((OLD / 'INTEGRITY_MANIFEST.json').read_bytes())
    for name, digest in manifest['public_files'].items():
        assert sha((OLD / name).read_bytes()) == digest, name
    for name, digest in manifest['historical_references'].items():
        assert sha((ROOT / name).read_bytes()) == digest, name
    assert sha((ROOT / 'candidates/s0/submission.zip').read_bytes()) == S0_SHA
    for row in json.loads((OLD / 'RAW_ARCHIVES.json').read_bytes())['archives']:
        with zipfile.ZipFile(row['path']) as archive:
            assert sha(Path(row['path']).read_bytes()) == row['sha256']
            assert archive.testzip() is None
    original = json.loads((PRIOR / 'original_task.json').read_bytes())
    receipt = json.loads((OLD / 'EVIDENCE_RECEIPT.json').read_bytes())
    expected = json.loads((OLD / 'GPU_EXECUTION_LOCK.json').read_bytes())['input_build']['inputs']
    for arm in ('A', 'B'):
        body = arm_input(original['problem_statement'], receipt, arm).encode()
        assert sha(body) == expected[arm]['sha256'] and len(body) == expected[arm]['bytes']
        assert body == (PRIOR / f'input_{arm}.txt').read_bytes()
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
    assert all(p.startswith('egrd/v0311/') for p in changed), changed
    return {'S0': S0_SHA, 'inputs': expected, 'history': 'UNCHANGED'}
