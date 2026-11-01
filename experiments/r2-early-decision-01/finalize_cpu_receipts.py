"""Validate actual completed CPU archive, retain raw limitations, freeze identities."""
import hashlib,json,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent
archive=D/'cpu-final-download/r2a-final-cpu-overlay.zip';evidence=D/'cpu-final-download/evidence';evidence.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    names=('CPU_FINAL_SUMMARY.json','RUNTIME_OVERLAY_IDENTITIES.json','TASK_RUNTIME_311_IDENTITIES.json','SDK_SNAPSHOT_IDENTITIES.json','SOURCE_TREE_VERIFICATION.json')
    for n in names:(evidence/n).write_bytes(z.read(n))
    summary=json.loads(z.read(names[0]));assert summary['status']=='PASS'
    assert summary['admission']['status']=='PASS' and len(summary['admission']['rows'])==4
    assert summary['plumbing_replay']['status']=='PASS_PLUMBING_ONLY'
    assert summary['real_Gemma_requests']==0 and summary['GPU_sessions']==0
    checks=[]
    for n in z.namelist():
        if not (n.startswith('admission/') or n.startswith('replay/')):continue
        if '/ISOLATION_' in n and n.endswith('.json'):
            r=json.loads(z.read(n));assert r['exit_code']==0 and 'NONROOT_CHROOT_NETWORK_DENIED' in r['stdout'] and '3.11.9' in r['stdout'];checks.append(n)
        if n.endswith('/CLEANUP.json'):
            r=json.loads(z.read(n));assert r['complete'] is True
        if n.endswith('/VERIFICATION_SOURCE_GUARD.json'):assert json.loads(z.read(n))['unchanged'] is True
    assert len(checks)==6,checks
    replay=json.loads(z.read('replay/SESSION_RESULT.json'))
    assert replay['evidence_complete'] and replay['patch_submitted'] and replay['patch_bytes']>0
    assert replay['sdk_native_resolved'] is False and replay['independent_test_pass'] is False
    compiled=json.loads(z.read('admission/COMPILE_RESULTS.json'))
    assert {k:v for k,v in compiled['R2'].items() if k!='instruction_sha256'}=={k:v for k,v in compiled['A'].items() if k!='instruction_sha256'}
    receipt=dict(status='CPU_INTEGRATION_PASS_WITH_DECLARED_METADATA_LIMITATIONS',archive_sha256=sha(archive.read_bytes()),archive_bytes=archive.stat().st_size,
        evidence_files={n:sha(z.read(n)) for n in names},isolation_checks=checks,Compiler=compiled,
        tasks=[dict(task=r['task'],admission=r['status'],raw_positive_controls_passed=r['junit_summary']['positive_controls_passed'],raw_all_positive_nodes_confirmed=r['junit_summary']['raw_all_positive_nodes_confirmed'],infrastructure_controls=r['infrastructure_controls']) for r in summary['admission']['rows']],
        replay=summary['plumbing_replay'],repair_capability_evidence=False,real_Gemma_requests=0,GPU_devices=0)
(D/'CPU_FROZEN_RECEIPT_MANIFEST.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(status=receipt['status'],archive_sha256=receipt['archive_sha256'],isolation_checks=len(checks))))
