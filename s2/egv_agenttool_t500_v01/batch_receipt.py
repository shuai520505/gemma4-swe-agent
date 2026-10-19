"""Verify batch1 locally; emit only hashes/status for batch2, never its answers."""
import hashlib
import io
import json
from pathlib import Path
import zipfile
from s1.collect import verify_zip
from experiments.prepare import write_new


def seal(archive, protocol, output):
    raw=Path(archive).read_bytes();verify_zip(raw)
    expected=Path(protocol).read_bytes();plan=json.loads(expected)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        gate=json.loads(z.read('batch_gate.json'))
        assert gate['infrastructure_passed'] and not gate['not_run'] and gate['stop_reason'] is None
        assert gate['protocol_sha256']==hashlib.sha256(expected).hexdigest()
        runs=[r for r in plan['runs'] if r['batch']==1]
        assert len(runs)==len(gate['records'])==8
        assert [(r['index'],r['instance_id'],r['arm']) for r in runs]==[(r['index'],r['instance_id'],r['arm']) for r in gate['records']]
        assert json.loads(z.read('server_cleanup.json'))['verified']
        assert json.loads(z.read('model_identity.json'))['files']==plan['model_files']
        assert json.loads(z.read('wheel_hashes.json'))==plan['wheel_hashes']
        assert all(r['audit']['infrastructure_passed'] for r in gate['records'])
    receipt=dict(experiment_id=plan['experiment_id'],protocol_sha256=hashlib.sha256(expected).hexdigest(),
        raw_sha256=hashlib.sha256(raw).hexdigest(),infrastructure_passed=True,complete_pairs=4,
        scope='Trusted local raw archive verification. No outcome, Issue, Trace, Patch or tool content supplied to batch2 Agents.')
    write_new(Path(output),(json.dumps(receipt,indent=2)+'\n').encode())
    return receipt


if __name__=='__main__':
    import sys
    seal(*sys.argv[1:])
