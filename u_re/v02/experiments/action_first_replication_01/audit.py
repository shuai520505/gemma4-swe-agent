"""Offline evidence derivation; no model inputs or execution controls."""
import json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from .selection import HERE,ROOT,ID,sha,write

def counts(raw):
    cases=list(ET.fromstring(raw).iter('testcase'))
    return dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))

def bound_archive(archive,attempt):
    archive=Path(archive).resolve();assert not archive.is_relative_to(ROOT)
    cpu=HERE/attempt;receipt=json.loads((cpu/'execution/HTTP_RECEIPT.json').read_bytes())
    m=json.loads(sorted((cpu/'read_observations').glob('read-*/OUTPUT_MANIFEST.json'))[-1].read_bytes())
    assert m['status']=='COMPLETE' and m['version_bound_before_after']
    item=next(f for f in m['files'] if f['file']=='v02-'+attempt+'.zip')
    assert item['Notebook_id']==receipt['Notebook_id'] and item['version']==receipt['accepted_version']==1 and item['complete']
    assert sha(archive.read_bytes())==item['sha256']
    return dict(Notebook_id=receipt['Notebook_id'],version=1,platform_status=m['status'],path=str(archive),sha256=item['sha256'],bytes=archive.stat().st_size,CRC_valid=True,attempt=attempt)

def screen(archive,attempt='screen01'):
    binding=bound_archive(archive,attempt)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        load=lambda n:json.loads(z.read(n))
        build=json.loads((HERE/attempt/'BUILD.json').read_bytes())
        for n,h in build['payload_members'].items():assert sha(z.read('source/'+n))==h,n
        ledger=load('validation/TASK_ADMISSION_LEDGER.json')
        pool=json.loads((HERE/'TASK_POOL_FREEZE.json').read_bytes())
        assert [r['instance_id'] for r in ledger['rows']]==[r['instance_id'] for r in pool['next_max16_in_order']]
        assert not ledger['screening_in_progress'] and ledger['checked']<=16
        selected=[]
        for row in ledger['rows']:
            if row['status']=='NOT_RUN':continue
            ident=row['instance_id'];p='validation/'+row['raw_evidence']+'/'
            native=load(p+'official_result.json');junit=z.read(p+'phase2.junit.xml');clean=load(p+'cleanup.json')
            assert counts(junit)==row['counts'] and sha(junit)==row['JUnit_sha256']
            assert native['resolved']==row['native_resolved'] and native['test_exit_code']==row['native_exit_code']
            assert clean['complete']==row['cleanup']
            if row['status']=='BASELINE_ELIGIBLE':
                assert row['eligible'] and row['cleanup'] and row['source_provenance_verified'] and row['workspace_files_unchanged']
                assert row['counts']['failures']>0 and row['counts']['errors']==0 and row['native_exit_code']==1 and not row['native_resolved']
                assert z.read(p+'before_pytest_files.json')==z.read(p+'after_pytest_files.json')
                selected.append(dict(**row['identity'],rank=row['rank'],native_baseline_counts=row['counts'],native_baseline_exit_code=row['native_exit_code'],JUnit_sha256=sha(junit),native_TaskResult_sha256=sha(z.read(p+'official_result.json')),cleanup=True,source_provenance_verified=True,evaluator_material='PRIVATE_ONLY',issue_failure_relation='REQUIRES_OFFLINE_CONTRACT_REVIEW'))
        assert len(selected)==len(ledger['selected'])
        alias=load('validation/SNAPSHOT_ALIAS_CHECK.json') if 'validation/SNAPSHOT_ALIAS_CHECK.json' in z.namelist() else None
        assert alias and alias['checked_before_baselines'] and alias['conflicts']==[]
    write(HERE/'TASK_ADMISSION_LEDGER.json',dict(**ledger,source_archive=binding,preregistration_commit='c3cfb75',legacy_status_fields='No inherited admission/baseline placeholders; status is final observed classification'))
    write(HERE/'SELECTED_TASKS.json',dict(experiment_id=ID,status='FOUR_TASKS_ADMITTED_PENDING_CONTRACT_REVIEW' if len(selected)==4 else 'TASKS_INSUFFICIENT' if not ledger['stop'] else 'TASK_ADMISSION_STOPPED',selected_count=len(selected),tasks=selected,source_archive=binding))
    write(HERE/'RAW_ARCHIVES.json',dict(archives=[binding]))
    print(json.dumps(dict(checked=ledger['checked'],selected=[t['instance_id'] for t in selected],stop=ledger['stop'])))

if __name__=='__main__':
    import sys
    if sys.argv[1]=='screen':screen(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'screen01')
