"""Bind targeted CPU outputs to the sealed, shared production worker bytes."""
import io
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from .prepare import HERE, sha, put


def audit(private_root, read):
    evidence=Path(private_root)/read/'evidence_confirmed'
    receipt=json.loads((HERE/'cpu-binding01/execution/HTTP_RECEIPT.json').read_bytes())
    identity=json.loads((evidence/'RESOURCE_IDENTITY.json').read_bytes())
    manifest=json.loads((evidence/'OUTPUT_MANIFEST.json').read_bytes())
    assert identity['state']=='IDENTITY_CONFIRMED'
    assert identity['metadata']['id']==receipt['Notebook_id']
    assert identity['metadata']['enable_gpu'] is False
    assert manifest['status']=='COMPLETE' and manifest['version_bound_before_after']
    entry=next(r for r in manifest['files'] if r['file']=='meer-v01-cpu-binding01.zip')
    path=evidence/'output'/entry['file'];raw=path.read_bytes()
    assert sha(raw)==entry['sha256'] and len(raw)==entry['bytes'] and entry['version']==1
    build=json.loads((HERE/'cpu-binding01/BUILD.json').read_bytes())
    shared=json.loads((HERE/'PAYLOAD_BUILD.json').read_bytes())
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        payload=json.loads(z.read('PAYLOAD_IDENTITY.json'))
        assert payload['payload_sha256']==build['payload_sha256']
        for n,h in build['payload_members'].items():assert sha(z.read('source/'+n))==h,n
        for n,h in shared['payload_members'].items():assert sha(z.read('source/'+n))==h,n
        acceptance=json.loads(z.read('validation/CPU_ACCEPTANCE.json'))
        assert acceptance['status']=='MEER_GPU_WORKER_CPU_PASS'
        assert acceptance['CPU_MODEL']=='SCRIPTED_ONLY' and acceptance['real_Gemma_requests']==0
        assert [r['arm'] for r in acceptance['records']]==['A','B','C']
        for row in acceptance['records']:
            base='validation/'+row['arm']+'/'
            result=z.read(base+'worker/official_result.json')
            junit=z.read(base+'worker/verifier/phase2.junit.xml')
            assert sha(result)==row['TaskResult_sha256'] and sha(junit)==row['JUnit_sha256']
            assert sha(z.read(base+'worker/final.patch'))==row['patch_sha256']
            assert json.loads(result)['resolved'] is True
            xml=ET.fromstring(junit)
            assert list(xml.iter('testcase')) and not list(xml.iter('failure')) and not list(xml.iter('error'))
            assert json.loads(z.read(base+'TRANSPORT_CLEANUP.json'))['complete']
            done=json.loads(z.read(base+'worker/worker_done.json'))
            assert done['integrity_complete'] and done['cleanup_complete']
            assert len(row['schema'])==(6 if row['arm']=='A' else 10)
        assert acceptance['records'][1]['mechanism_verdicts']==['CONTRADICTED','SUPPORTED','OBSERVED']
        assert acceptance['records'][2]['mechanism_verdicts']==['UNKNOWN']*3
    value=dict(acceptance,Notebook_id=receipt['Notebook_id'],version=1,platform_status='COMPLETE',
        payload_sha256=build['payload_sha256'],shared_GPU_payload_sha256=shared['payload_sha256'],
        all_shared_members_verified=len(shared['payload_members']),
        private_archive_path=str(path.resolve()),archive_sha256=sha(raw),archive_bytes=len(raw),CRC_valid=True,
        limitation='Targeted production worker/Guard/Skill CPU acceptance; GPU coordinator/model/resource execution NOT_RUN')
    put('CPU_BINDING_ACCEPTANCE.json',value)
    print(json.dumps({k:value[k] for k in ('status','Notebook_id','shared_GPU_payload_sha256','archive_sha256')}))
    return value


if __name__=='__main__':
    import sys
    audit(*sys.argv[1:])
