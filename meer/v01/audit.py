"""Independent acceptance from exact downloaded raw bytes; no remote mutation."""
import hashlib
import io
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from .build import HERE,ROOT,sha


def inspect_archive(attempt,raw,*,require_bypass=False):
    spec=json.loads((HERE/attempt/'BUILD.json').read_bytes())
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        identity=json.loads(z.read('PAYLOAD_IDENTITY.json'))
        assert identity['payload_sha256']==spec['payload_sha256']
        assert identity['files']==spec['payload_members']
        for name,h in spec['payload_members'].items():
            assert sha(z.read('source/'+name))==h,name
        lock=json.loads(z.read('source/meer/v01/CANDIDATE_MANIFEST.json'))
        assert lock==json.loads((HERE/'CANDIDATE_MANIFEST.json').read_bytes())
        for arm,r in lock['arms'].items():
            archive=z.read('source/meer/v01/submission_'+arm+'.zip')
            assert sha(archive)==r['ZIP_sha256']
            with zipfile.ZipFile(io.BytesIO(archive)) as candidate:
                assert candidate.testzip() is None
                assert set(candidate.namelist())==set(r['members'])
                for n,h in r['members'].items():assert sha(candidate.read(n))==h
        acceptance=json.loads(z.read('validation/CPU_ACCEPTANCE.json'))
        assert acceptance['status']=='MEER_CPU_ENGINEERING_PASS' and acceptance['CPU_MODEL']=='SCRIPTED_ONLY'
        assert acceptance['real_Gemma_requests']==0
        tests=json.loads(z.read('validation/MECHANISM_TESTS.json'))
        assert tests==dict(tests=12,failures=0,errors=0,skipped=0)
        records=acceptance['records']
        assert [r['arm'] for r in records]==(['A','B','C','B_BYPASS'] if require_bypass else ['A','B','C'])
        for r in records:
            prefix='validation/'+r['arm']+'/'
            result=z.read(prefix+'TaskResult.json');junit=z.read(prefix+'verifier/phase2.junit.xml')
            assert sha(result)==r['TaskResult_sha256'] and sha(junit)==r['JUnit_sha256']
            assert sha(z.read(prefix+'final.patch'))==r['patch_sha256']
            native=json.loads(result);xml=ET.fromstring(junit)
            assert native['resolved'] and native['test_exit_code']==0
            assert len(list(xml.iter('testcase')))>=1 and not list(xml.iter('failure')) and not list(xml.iter('error'))
            assert json.loads(z.read(prefix+'agent/cleanup.json'))['complete']
            assert json.loads(z.read(prefix+'TRANSPORT_CLEANUP.json'))['complete']
            assert r['explicit_submit'] and r['empty_state_compile'] and r['cleanup_complete']
        b=records[1];c=records[2]
        assert b['schemas']==c['schemas'] and b['compiled'][0]['generation']==c['compiled'][0]['generation']
        assert [v['verdict'] for v in b['mechanism_evidence']]==['CONTRADICTED','SUPPORTED','OBSERVED']
        assert [v['subprocess_invocations'] for v in b['mechanism_evidence']]==[1,1,0]
        assert all(v['verdict']=='UNKNOWN' for v in c['mechanism_evidence'])
        if require_bypass:
            bypass=records[3]
            assert bypass['direct_submit_without_relevant_check'] and bypass['repeated_searches_actually_executed']==2
            assert bypass['unverified_success_claim_not_intercepted'] and not bypass['mechanism_evidence']
        return dict(status='MEER_CPU_ENGINEERING_PASS',CPU_MODEL='SCRIPTED_ONLY',attempt=attempt,
            payload_sha256=spec['payload_sha256'],archive_sha256=sha(raw),archive_bytes=len(raw),
            CRC_valid=True,source_members_verified=len(spec['payload_members']),records=records,
            mechanism_tests=tests,real_Gemma_requests=0,global_gate_claimed=False)


def audit(attempt,private_root,read):
    evidence=Path(private_root)/read/'evidence_confirmed'
    identity=json.loads((evidence/'RESOURCE_IDENTITY.json').read_bytes())
    manifest=json.loads((evidence/'OUTPUT_MANIFEST.json').read_bytes())
    receipt=json.loads((HERE/attempt/'execution/HTTP_RECEIPT.json').read_bytes())
    assert identity['state']=='IDENTITY_CONFIRMED' and identity['metadata']['id']==receipt['Notebook_id']
    assert manifest['status']=='COMPLETE' and manifest['version_bound_before_after']
    filename='meer-v01-'+attempt+'.zip';entry=next(f for f in manifest['files'] if f['file']==filename)
    path=evidence/'output'/filename;raw=path.read_bytes()
    assert sha(raw)==entry['sha256'] and len(raw)==entry['bytes'] and entry['version']==1
    value=inspect_archive(attempt,raw,require_bypass=attempt=='cpu03')
    # A deliberately broken raw archive must not be accepted as engineering proof.
    try:inspect_archive(attempt,b'INVALID_ZIP'+raw[20:],require_bypass=attempt=='cpu03')
    except (AssertionError,zipfile.BadZipFile,KeyError,ValueError):pass
    else:raise AssertionError('Corrupt archive accepted')
    value.update(Notebook_id=receipt['Notebook_id'],version=1,platform_status='COMPLETE',
                 raw_archive_path=str(path.resolve()),corrupted_archive_rejected=True)
    (HERE/('CPU_ACCEPTANCE_'+attempt.upper()+'.json')).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:value[k] for k in ('status','Notebook_id','payload_sha256','archive_sha256')}))
    return value


if __name__=='__main__':
    import sys
    audit(*sys.argv[1:])
