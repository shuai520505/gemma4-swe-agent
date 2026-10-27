"""Source identities and private evidence paths; no candidate reconstruction."""
import json
from pathlib import Path
import subprocess
import zipfile

from egrd.v031.prepare import ROOT, S0_SHA, sha, write, arm_input

HERE=Path(__file__).resolve().parent
BASE='d2a09cb114df4621885f437bf04c4b7d919d47de'
PRIVATE=ROOT.parent/'private-evidence/egrd_v032'
CPU_PRIVATE=ROOT.parent/'private-evidence/egrd_v0311'
INPUT_PRIVATE=ROOT.parent/'private-evidence/egrd_v031'
REF='wudangdexiaodoashi/egrd-v032-real-gemma-evidence-ab'
MODEL_REF='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2'
WINDOW=10000


def verify_history():
    old=ROOT/'egrd/v0311'
    manifest=json.loads((old/'INTEGRITY_MANIFEST.json').read_bytes())
    for name,digest in manifest['public_files'].items():assert sha((old/name).read_bytes())==digest,name
    prior=ROOT/'egrd/v031'
    manifest=json.loads((prior/'INTEGRITY_MANIFEST.json').read_bytes())
    for name,digest in manifest['public_files'].items():assert sha((prior/name).read_bytes())==digest,name
    for name,digest in manifest['historical_references'].items():assert sha((ROOT/name).read_bytes())==digest,name
    raw=json.loads((old/'RAW_ARCHIVES.json').read_bytes())
    path=Path(raw['path']);assert sha(path.read_bytes())==raw['sha256']
    build=json.loads((old/'CPU_BUILD.json').read_bytes())
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        for name,digest in build['members'].items():assert sha(archive.read('source/'+name))==digest,name
        result=json.loads(archive.read('results/CPU_TEST_RESULTS.json'))
        assert result['status']=='CPU_PREFLIGHT_PASS' and result['input_boundary_pass']
        for row in result['records']:
            assert row['full_compiler'] and row['patch_submitted'] and row['agent_cleanup']
            assert row['development_result']['original_failing_probe_still_fails']
    assert sha((ROOT/'candidates/s0/submission.zip').read_bytes())==S0_SHA
    original=json.loads((INPUT_PRIVATE/'original_task.json').read_bytes())['problem_statement']
    receipt=json.loads((prior/'EVIDENCE_RECEIPT.json').read_bytes())
    expected=json.loads((prior/'GPU_EXECUTION_LOCK.json').read_bytes())['input_build']['inputs']
    for arm in ('A','B'):
        body=arm_input(original,receipt,arm).encode()
        assert sha(body)==expected[arm]['sha256'] and len(body)==expected[arm]['bytes']
    changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    assert all(n.startswith('egrd/v032/') for n in changed),changed
    return dict(base_commit=BASE,S0_sha256=S0_SHA,CPU_archive_sha256=raw['sha256'],CPU_payload_sha256=build['payload_sha256'],
                task_inputs=expected,receipt_sha256=sha((prior/'EVIDENCE_RECEIPT.json').read_bytes()),
                CPU_gates=17,historical_evidence_unchanged=True)
