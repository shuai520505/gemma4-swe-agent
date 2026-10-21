"""Offline validation of already downloaded CPU02 evidence; never executes it."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import xml.etree.ElementTree as ET
import zipfile

from .recover import HERE, CPU02, write, digest, utc


def validate_archive(z):
    names=z.namelist()
    assert len(names)==len(set(names)) and len(names)<=2000
    assert sum(x.file_size for x in z.infolist())<=100*1024*1024
    for item in z.infolist():
        p=PurePosixPath(item.filename)
        assert not p.is_absolute() and '..' not in p.parts and '\\' not in item.filename and ':' not in item.filename
        assert not stat.S_ISLNK(item.external_attr>>16)
    assert z.testzip() is None,'ZIP CRC error'
    manifest=json.loads(z.read('evidence_manifest.json'))
    assert set(manifest)==set(names)-{'evidence_manifest.json'},'Archive membership mismatch'
    for n,entry in manifest.items():
        raw=z.read(n)
        assert len(raw)==entry['bytes'] and digest(raw)==entry['sha256'],n
    return manifest


def run():
    evidence=HERE/'evidence_confirmed'
    download=json.loads((evidence/'OUTPUT_MANIFEST.json').read_bytes())
    assert download['version_bound_before_after'] and download['status']=='COMPLETE'
    for record in download['files']:
        raw=(evidence/'output'/record['file']).read_bytes()
        assert len(raw)==record['bytes'] and digest(raw)==record['sha256']
    records=[x for x in download['files'] if x['file'].endswith('.zip')]
    assert len(records)==1
    archive=evidence/'output'/records[0]['file']
    target=HERE/'native_evidence';target.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        manifest=validate_archive(z)
        # Verify all frozen code/protocol members without executing any downloaded code.
        nb=json.loads((CPU02/'notebook/study.ipynb').read_bytes())
        first=nb['cells'][0]['source'];first=''.join(first) if isinstance(first,list) else first
        prefix="payload=__import__('base64').b64decode("
        line=next(x for x in first.splitlines() if x.startswith(prefix))
        raw=base64.b64decode(ast.literal_eval(line[len(prefix):-1]),validate=True)
        with zipfile.ZipFile(io.BytesIO(raw)) as frozen:
            for n in frozen.namelist():assert frozen.read(n)==z.read('source/'+n),'Payload source drift:'+n
            source_members=len(frozen.namelist())
        # Extract only native evidence/logs;research source and model candidates stay inside raw ZIP.
        for n in z.namelist():
            if n.startswith('validation/') or n in ('cpu.log','installation.log','wheel_hashes.json','task_wheel_hashes.json','evidence_manifest.json'):
                p=target/n;p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as f:f.write(z.read(n))
    ledger=json.loads((target/'validation/TASK_SCREENING_LEDGER.json').read_bytes())
    assert ledger==json.loads((target/'validation/cpu_gate.json').read_bytes())
    pilot=CPU02.parents[1]
    ranked=json.loads((pilot/'RANKED_POOL.json').read_bytes())['rows']
    protocol=json.loads((pilot/'SELECTION_PROTOCOL.json').read_bytes())
    assert len(ledger['rows'])==len(ranked)==50
    assert ledger['protocol_sha256']==digest((pilot/'SELECTION_PROTOCOL.json').read_bytes())
    assert ledger['checked']<=8 and ledger['Agent_runs']==0 and ledger['model_calls']==0 and ledger['GPU'] is False
    entered=[r for r in ledger['rows'] if r['cpu_entered']]
    assert len(entered)==ledger['checked']
    checks=[]
    for i,row in enumerate(ledger['rows']):
        rank=ranked[i]
        assert row['instance_id']==rank['instance_id'] and row['repo']==rank['repo']
        assert row['base_commit']==rank['base_commit'] and row['issue_sha256']==rank['issue_sha256']
        if not row['cpu_entered']:continue
        assert row['check_number']==i+1,'Screened order is not the original prefix'
        d=target/'validation'/row['evidence']
        ident=json.loads((d/'task_identity.json').read_bytes())
        assert ident['base_commit']==rank['base_commit'] and ident['issue_sha256']==rank['issue_sha256']
        result=json.loads((d/'official_result.json').read_bytes())
        execution=json.loads((d/'phase2_execution.json').read_bytes())
        audit=json.loads((d/'structured_verifier.json').read_bytes())
        capture=json.loads((d/'phase2_junit_capture.json').read_bytes())
        junit=(d/'phase2.junit.xml').read_bytes()
        assert capture['sha256']==row['JUnit_sha256']==digest(junit)
        assert capture['status']=='captured' and capture['capture_phase']=='before_native_sandbox_stop'
        assert result['test_exit_code']==execution['exit_code']==row['native_test_exit_code']
        xml=ET.fromstring(junit);cases=list(xml.iter('testcase'))
        counts=dict(tests=len(cases),failures=sum(x.find('failure') is not None for x in cases),
                    errors=sum(x.find('error') is not None for x in cases),skipped=sum(x.find('skipped') is not None for x in cases))
        assert counts==audit['counts']==row['counts']
        cleanup=json.loads((d/'cleanup.json').read_bytes())
        source=json.loads((d/'source_provenance.json').read_bytes())
        assert cleanup['complete'] and not cleanup['new_remaining_processes']
        assert source['verified']==row['source_provenance_verified']
        checks.append(dict(instance_id=row['instance_id'],status=row['status'],admitted=False,
            classification=audit['category'],native_resolved=result['resolved'],test_exit_code=result['test_exit_code'],
            counts=counts,setup_errors=row['setup_errors'],collection_errors=row['collection_errors'],
            JUnit_sha256=digest(junit),TaskResult_sha256=digest((d/'official_result.json').read_bytes()),
            cleanup_complete=cleanup['complete'],source_provenance_verified=source['verified'],identity=ident,
            attribution='Two scope keyword collection errors may represent an unfixed task API contract; inline_snapshot is independently missing. No Agent ran. Do not classify this as an algorithm failure.'))
    assert ledger['status']=='TASK_ADMISSION_BLOCKED' and ledger['selected']==[]
    assert entered and entered[-1]['decision']=='STOP'
    write(HERE/'ARCHIVE_AUDIT.json',dict(audited_at_utc=utc(),archive_sha256=digest(archive.read_bytes()),
        archive_bytes=archive.stat().st_size,archive_CRC_passed=True,manifest_members_verified=len(manifest),
        frozen_payload_source_members_verified=source_members,all_source_protocol_bytes_equal=True,
        checked=len(checks),selected=[],native_checks=checks,status='CPU_TASK_ADMISSION_BLOCKED',
        original_ledger_status=ledger['status'],remaining_tasks='NOT_RUN_BY_FROZEN_STOP_RULE',
        JUnit_and_TaskResult_consistent=True,GPU_authorized=False))
    write(HERE/'TASK_SCREENING_LEDGER.json',ledger)
    print(json.dumps(dict(status='CPU_TASK_ADMISSION_BLOCKED',checked=len(checks),eligible=0,
        CRC=True,source_members_verified=source_members,counts=checks[0]['counts'])))


if __name__=='__main__':run()
