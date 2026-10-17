"""Verify raw study02 archives, frozen study01 and registered runtime/candidates."""
import hashlib
import io
import json
from pathlib import Path
import zipfile
from cure.build import write_new
from cure.runner import require_gate
from harness_v2.integrity import verify_baseline


def verify():
    repo=Path(__file__).resolve().parents[2];study=repo/'cure/gpu-study-02-c1'
    sha=lambda b:hashlib.sha256(b).hexdigest()
    old=json.loads((repo/'cure/gpu-study-01/delivery-manifest.json').read_text(encoding='utf-8'))
    for name,digest in old.items():assert sha((repo/name).read_bytes())==digest,name
    original=json.loads((repo/'cure/results/delivery-manifest.json').read_text(encoding='utf-8'))
    for name,digest in original.items():assert sha((repo/name).read_bytes())==digest,name
    gate=require_gate(repo/'cure/results/cpu-r03/cpu_gate.json',repo)
    plan=json.loads((study/'protocol.json').read_text(encoding='utf-8'))
    for name,digest in plan['runtime_source_hashes'].items():assert sha((repo/name).read_bytes())==digest,name
    assert sha((study/'protocol.json').read_bytes())=='c47ef237d0b95089ee117cee75c8b0c836270bcb93d350fc2c34bdb32a28864c'
    cpu_gate=study/'results/cpu/full_runner_cpu_gate.json'
    cpu=json.loads(cpu_gate.read_text(encoding='utf-8'))
    assert cpu['passed'] and cpu['registration_sha256']==sha((study/'runner-registration.json').read_bytes())
    for arm,n in [('checklist',1),('cure_v01_c1',1),('cure_v01',0),('cure_v01-double-braces',0)]:
        assert cpu['cases'][arm]['HTTP_requests']==n
    archives=[]
    def check_zip(z):
        assert z.testzip() is None
        native=json.loads(z.read('evidence_manifest.json'))
        for name,meta in native.items():
            raw=z.read(name);assert len(raw)==meta['bytes'] and sha(raw)==meta['sha256'],name
    for kind in ('cpu','smoke'):
        d=study/'results'/kind
        collection=json.loads((d/'collection.json').read_text(encoding='utf-8'))
        assert sha((d/'evidence.zip').read_bytes())==collection['archive_sha256']
        with zipfile.ZipFile(d/'evidence.zip') as z:
            check_zip(z)
            inventory=json.loads((d/'archive-members.json').read_text(encoding='utf-8'))
            for name,meta in inventory.items():
                raw=z.read(name);assert len(raw)==meta['bytes'] and sha(raw)==meta['sha256'],name
                if (d/name).is_file():assert (d/name).read_bytes()==raw,name
            assert z.read('source/study/protocol.json')==(study/'protocol.json').read_bytes()
            for name,digest in plan['runtime_source_hashes'].items():
                assert sha(z.read('source/'+name))==digest,name
            if kind=='smoke':
                assert z.read('source/study/full_runner_cpu_gate.json')==cpu_gate.read_bytes()
                for name in z.namelist():
                    if name.startswith('runs/') and name.endswith('.zip'):
                        with zipfile.ZipFile(io.BytesIO(z.read(name))) as nested:check_zip(nested)
        archives.append(collection)
    smoke=study/'results/smoke'
    assert json.loads((smoke/'model_identity.json').read_text())['files']==plan['expected_model_files']
    assert json.loads((smoke/'wheel_hashes.json').read_text())==plan['wheel_hashes']
    patches=[]
    for row in plan['batches']['smoke']:
        d=smoke/'runs'/f"{row['index']:02d}-{row['task_id']}-{row['arm']}"
        specname=f"{row['index']:02d}-{row['task_id']}-{row['arm']}.json"
        with zipfile.ZipFile(smoke/'evidence.zip') as z:
            spec=json.loads(z.read('specs/'+specname))
        assert spec['base_commit']==plan['tasks'][0]['base_commit']
        assert spec['problem_sha256']==plan['tasks'][0]['problem_sha256']
        assert spec['research_config']==plan['research_config']
        audit=json.loads((d/'mechanism_audit.json').read_text(encoding='utf-8'))
        assert audit['infrastructure_passed'] is True
        assert all(audit['checks'].values())
        patches.append((d/'latest.patch').read_bytes())
        for name,digest in plan['candidates'][row['arm']]['members'].items():
            assert sha((repo/'cure/candidates'/row['arm']/name).read_bytes())==digest
    assert patches[0]==patches[1]
    old_prompt=(repo/'cure/candidates/cure_v01/prompts/system.md').read_bytes()
    new_prompt=(repo/'cure/candidates/cure_v01_c1/prompts/system.md').read_bytes()
    assert new_prompt==old_prompt.replace(b'<cure>{JSON}</cure>',b'<cure>JSON object</cure>')
    result=dict(passed=True,old_study_delivery_files_unchanged=len(old),original_cure_files_unchanged=len(original),
        frozen_baseline_files_verified=verify_baseline(),original_cpu_source_hashes_verified=len(gate['source_hashes']),
        current_registered_runtime_files_verified=len(plan['runtime_source_hashes']),archives=archives,
        raw_member_hashes_CRC_and_nested_manifests_verified=True,exposed_copies_byte_equal_to_raw=True,
        matching_full_runner_gate_verified=True,same_clean_snapshot_and_parameters=True,
        identical_final_patch_sha256=sha(patches[0]),formal_submission=False)
    write_new(study/'integrity-audit.json',(json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps(result,indent=2))


if __name__=='__main__':verify()
