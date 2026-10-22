"""Normalize stale preregistration fields only from independently checked native bytes."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'integrated_cpu_01'
ROOT=HERE.parents[4]
KEYS=('instance_id','repo','base_commit','issue_sha256','input_files','task_record_sha256','test_patch_sha256')

def sha(raw):return hashlib.sha256(raw).hexdigest()

def normalize(ledger,selected,read):
    assert ledger['status']=='TWO_TASKS_ADMITTED' and ledger['checked']==4 and ledger['stop'] is None
    rows={r['instance_id']:r for r in ledger['rows']}
    output=[]
    for frozen in selected['tasks']:
        r=rows[frozen['instance_id']]
        assert r['status']=='BASELINE_ELIGIBLE' and r['eligible'] is True
        assert all(r['identity'][k]==frozen[k] for k in KEYS)
        prefix='validation/'+r['raw_evidence']+'/'
        native=read(prefix+'official_result.json');junit=read(prefix+'phase2.junit.xml')
        assert sha(native)==frozen['native_TaskResult_sha256'] and sha(junit)==frozen['JUnit_sha256']==r['JUnit_sha256']
        result=json.loads(native);xml=ET.fromstring(junit);cases=list(xml.iter('testcase'))
        counts=dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),
            errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
        assert counts==r['counts']==frozen['native_baseline_counts']
        assert counts['failures']>0 and counts['errors']==0 and result['resolved'] is False and result['test_exit_code']==1
        identity=json.loads(read(prefix+'task_identity.json'))
        assert all(identity[k]==frozen[k] for k in KEYS)
        assert json.loads(read(prefix+'cleanup.json'))['complete'] is True
        assert json.loads(read(prefix+'source_provenance.json'))['verified'] is True
        assert r['workspace_files_unchanged'] and r['cleanup'] and r['source_provenance_verified']
        output.append(dict(**{k:frozen[k] for k in KEYS},admission='BASELINE_ELIGIBLE',baseline='EXECUTED',eligible=True,
            counts=counts,native_exit_code=1,native_resolved=False,
            snapshot_sha256=next(iter(frozen['input_files'].values())),evaluator_overlay_sha256=frozen['test_patch_sha256'],
            JUnit_sha256=sha(junit),native_TaskResult_sha256=sha(native),cleanup=True,source_provenance_verified=True,
            original_stale_fields={k:r.get(k) for k in ('admission','baseline','snapshot_sha256','evaluator_overlay_sha256')}))
    assert [r['instance_id'] for r in output]==['fastapi_9425','fastapi_14786']
    return dict(status='EVIDENCE_RECONCILED_TWO_TASKS_ADMITTED',tasks=output,
        meaning='Original admission/baseline/null top-level identity fields are stale pre-screen placeholders. This view requires actual native bytes, not a manual eligible flag.',
        original_ledger_modified=False,CPU_baseline_repeated=False)

def run():
    archive=ROOT.parent/'private-evidence/u_re_integrated_screen01/read-02/evidence_confirmed/output/u_re_integrated_screen01.zip'
    selected=json.loads((PRIOR/'SELECTED_TASKS.json').read_bytes())
    assert sha(archive.read_bytes())==selected['archive_sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        raw=z.read('validation/TASK_ADMISSION_LEDGER.json')
        assert raw==(PRIOR/'TASK_ADMISSION_LEDGER.json').read_bytes()
        result=normalize(json.loads(raw),selected,z.read)
    result.update(original_ledger_sha256=sha(raw),selected_sha256=sha((PRIOR/'SELECTED_TASKS.json').read_bytes()),
        archive_sha256=selected['archive_sha256'],source_Notebook_id=140218227,version=1,
        original_ABBA_lock_sha256=sha((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes()))
    (HERE/'ADMISSION_RECONCILIATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])

if __name__=='__main__':run()
