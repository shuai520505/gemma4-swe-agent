"""Derive admission from actual source/version-bound private native outputs."""
import json,zipfile,xml.etree.ElementTree as ET
import io
from pathlib import Path
from .common import HERE,ROOT,ID,sha,write
from .identity import conflicts

def native_counts(z,root):
    raw=z.read(root+'phase2.junit.xml');audit=json.loads(z.read(root+'audit.json'))
    actual=counts(raw)
    if actual!=audit['counts']:
        # Use the *already frozen PR26* exact snapshot-pair reader, not a new
        # allowance or mutation of the official XML/verdict.
        from u_re.v02.experiments.env_recovery_admission_01.junit_audit import parse_snapshot_phases
        parsed=parse_snapshot_phases(raw)
        assert parsed['counts']==audit['counts'] and audit['snapshot_assertion_teardown_proven']
        prefix='source/u_re/v02/experiments/env_recovery_admission_01/'
        manifest=json.loads(z.read(prefix+'NEW_DEPENDENCIES.json'))
        row=next(r for r in manifest['packages'] if r['name']=='inline-snapshot')
        wheel=z.read(prefix+'wheels/'+row['filename']);assert sha(wheel)==row['sha256']
        with zipfile.ZipFile(io.BytesIO(wheel)) as source:
            assert sha(source.read('inline_snapshot/pytest_plugin.py'))==audit['plugin_source_sha256']
        return parsed['counts']
    return actual

def counts(raw):
    cases=list(ET.fromstring(raw).iter('testcase'))
    return dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))

def bind(archive,attempt):
    archive=Path(archive).resolve();assert not archive.is_relative_to(ROOT)
    d=HERE/attempt;b=json.loads((d/'BUILD.json').read_bytes())
    receipt=json.loads((d/'execution/HTTP_RECEIPT.json').read_bytes())
    output=json.loads(sorted((d/'read_observations').glob('read-*/OUTPUT_MANIFEST.json'))[-1].read_bytes())
    row=next(r for r in output['files'] if r['file']=='v04adm-'+attempt+'.zip')
    assert output['version_bound_before_after'] and row['complete']
    assert row['Notebook_id']==receipt['Notebook_id'] and row['version']==receipt['accepted_version']==1
    assert row['sha256']==sha(archive.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,h in b['payload_members'].items():assert sha(z.read('source/'+n))==h,n
    return dict(attempt=attempt,Notebook_id=receipt['Notebook_id'],version=1,status=output['status'],private_path=str(archive),sha256=row['sha256'],bytes=archive.stat().st_size,CRC_valid=True,payload_sha256=b['payload_sha256'])

def screen(archive,attempt='screen01'):
    binding=bind(archive,attempt);assert binding['status']=='COMPLETE'
    protocol=json.loads((HERE/'ADMISSION_PROTOCOL_LOCK.json').read_bytes())
    env=json.loads((HERE/'ENVIRONMENT_LOCK.json').read_bytes())
    expected=json.loads((ROOT/'u_re/v02/experiments/env_recovery_admission_01/APPROVED_INPUT_IDENTITIES.json').read_bytes())
    with zipfile.ZipFile(archive) as z:
        load=lambda n:json.loads(z.read(n))
        identity=load('validation/TASK_IDENTITY_LOCK.json')
        assert identity['prospective_ids']==protocol['order'] and identity['checked_before_baselines']
        assert len(identity['all129'])==129
        for ident,row in identity['all129'].items():
            assert {k:v for k,v in row.items() if k not in ('snapshot_tree_sha256','test_overlay_content_sha256')}==expected[ident]
        assert identity['conflicts']==conflicts(identity['all129'],protocol['order'])
        ledger=load('validation/TASK_ADMISSION_RESULTS.json')
        assert ledger['protocol_sha256']==sha((HERE/'ADMISSION_PROTOCOL_LOCK.json').read_bytes())
        assert [r['instance_id'] for r in ledger['rows']]==protocol['order']
        assert load('validation/ENVIRONMENT_BEFORE.json')==load('validation/ENVIRONMENT_AFTER.json')==env['fingerprint']
        assert load('validation/OFFICIAL_VERIFIER_IDENTITIES.json')==env['native_Verifier_source_sha256']
        checked=[r for r in ledger['rows'] if r['status']!='NOT_RUN']
        assert [r['instance_id'] for r in checked]==protocol['order'][:len(checked)] and len(checked)==ledger['checked']<=5
        baselines=[]
        for row in checked:
            root='validation/'+row['raw_directory']+'/'
            assert row['identity']==expected[row['instance_id']]
            if row['TaskResult_sha256'] is not None:assert sha(z.read(root+'official_result.json'))==row['TaskResult_sha256']
            if row['JUnit_sha256'] is not None:
                assert sha(z.read(root+'phase2.junit.xml'))==row['JUnit_sha256']
                actual_counts=native_counts(z,root)
                assert actual_counts==row['counts']
            else:actual_counts=row['counts']
            if row['eligible']:
                assert row['evidence_ok'] and row['cleanup'] and row['source_unchanged'] and row['provenance']
                assert actual_counts['failures']>0 and actual_counts['errors']==0 and row['native_resolved'] is False
                assert z.read(root+'before.json')==z.read(root+'after.json')
                assert load(root+'cleanup.json')['complete'] and load(root+'provenance.json')['verified']
            baselines.append(dict(instance_id=row['instance_id'],rank=row['rank'],counts=actual_counts,native_resolved=row['native_resolved'],native_exit_code=row['native_exit_code'],status=row['status'],category=row['category'],reason=row['reason'],eligible=row['eligible'],identity=row['identity'],cleanup=row['cleanup'],source_unchanged=row['source_unchanged'],provenance=row['provenance'],evidence_ok=row['evidence_ok'],TaskResult_sha256=row['TaskResult_sha256'],JUnit_sha256=row['JUnit_sha256'],seconds=row['seconds']))
    write(HERE/'TASK_IDENTITY_LOCK.json',dict(identity,source_archive=binding))
    write(HERE/'NATIVE_BASELINE_RESULTS.json',dict(experiment_id=ID,source_archive=binding,rows=baselines,environment_lock_sha256=sha((HERE/'ENVIRONMENT_LOCK.json').read_bytes()),Gemma_calls=0,Agent_runs=0))
    safe_rows=[next((b for b in baselines if b['instance_id']==r['instance_id']),dict(instance_id=r['instance_id'],rank=r['rank'],status='NOT_RUN',eligible=None,reason=r['reason'])) for r in ledger['rows']]
    write(HERE/'TASK_ADMISSION_RESULTS.json',dict(experiment_id=ID,status=ledger['status'],checked=len(checked),rows=safe_rows,selected_provisional=ledger['selected_provisional'],stop=ledger['stop'],source_archive=binding,formal_admission='ISSUE_RELATION_REVIEW_REQUIRED',historical_inputs_unchanged=True))
    print(json.dumps(dict(status=ledger['status'],Notebook_id=binding['Notebook_id'],checked=len(checked),provisional=ledger['selected_provisional'],aliases=identity['conflicts'])))

if __name__=='__main__':
    import sys
    screen(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else 'screen01')
