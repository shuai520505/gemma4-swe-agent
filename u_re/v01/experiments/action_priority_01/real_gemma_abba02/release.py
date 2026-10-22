"""Narrow offline publication/integrity check; no experiment or network requests."""
import ast
import base64
import io
import json
import re
import subprocess
import zipfile
from .notebook import HERE,ROOT,PRIOR,sha

def run():
    base='5598178f4dbf3fdae543ae41e8328f70c0b2b908'
    changed=subprocess.check_output(['git','diff','--name-only',base],cwd=ROOT,text=True).splitlines()
    assert all(n.startswith(HERE.relative_to(ROOT).as_posix()+'/') for n in changed),'Historical tracked file changed'
    candidates={}
    previous=json.loads((HERE.parent/'real_gemma_abba01/INTEGRITY_MANIFEST.json').read_bytes())
    for name,expected in previous['candidates'].items():
        raw=(ROOT/name).read_bytes();assert sha(raw)==expected['sha256']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            members={n:sha(z.read(n)) for n in z.namelist()};assert members==expected['members']
        candidates[name]=dict(sha256=sha(raw),members=members,CRC_valid=True)
    lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    for name,h in lock['source_pins'].items():assert sha((PRIOR/name).read_bytes())==h
    actual=json.loads((HERE/'safe_evidence/results/TASK_IDENTITIES.json').read_bytes())
    for task in lock['tasks']:
        for key in ('repo','base_commit','issue_sha256','task_record_sha256','test_patch_sha256','input_files'):
            assert task[key]==actual[task['instance_id']][key]
    files={p.relative_to(HERE).as_posix():p.read_bytes() for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='INTEGRITY_MANIFEST.json'}
    scan=dict(files);builds={}
    for n,raw in files.items():
        if not n.endswith('.ipynb'):continue
        nb=json.loads(raw);source=nb['cells'][0]['source'];source=''.join(source) if isinstance(source,list) else source
        line=next(x for x in source.splitlines() if x.startswith("payload=__import__('base64').b64decode("))
        payload=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            assert z.testzip() is None;scan.update({n+'::'+m:z.read(m) for m in z.namelist()})
        build_name=n.removesuffix('notebook/study.ipynb')+'BUILD.json';spec=json.loads(files[build_name])
        assert sha(raw)==spec['Notebook_sha256'] and sha(json.dumps(nb).encode())==spec['wire_sha256'] and sha(payload)==spec['payload_sha256']
        builds[n]=dict(Notebook_sha256=sha(raw),payload_sha256=sha(payload))
    from u_re.v01.experiments.fastapi_pilot_01.auth_diagnose import inventory
    for value in inventory()[-1]:
        if len(value)>12:assert not any(value.encode() in b for b in scan.values()),'Known credential found'
    for line in (ROOT.parent/'official-inputs/tasks.jsonl').read_text(encoding='utf-8').splitlines():
        overlay=(json.loads(line).get('test_patch') or '').encode()
        if len(overlay)>80:assert not any(overlay in b for b in scan.values()),'Competition overlay found'
    for raw in scan.values():assert not re.search(rb'https://[^\s"<>]+[?&](?:X-Goog-Signature|X-Amz-Signature|Signature)=[a-zA-Z0-9%]{12,}',raw),'Signed URL found'
    dispatches={}
    for claim in HERE.rglob('dispatch.claim'):
        events=list((claim.parent/'events').glob('*DISPATCH_STARTED.json'));assert len(events)==1
        dispatches[str(claim.relative_to(HERE))]=1
    archives=json.loads((HERE/'RAW_ARCHIVES.json').read_bytes())
    for item in archives.values():
        if not isinstance(item,dict) or 'private_path' not in item:continue
        raw=__import__('pathlib').Path(item['private_path']).read_bytes();assert sha(raw)==item['sha256']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            registration=next((n for n in ('source/gpu_registration.json','source/repair_registration.json') if n in z.namelist()),None)
            if registration:
                for name,h in json.loads(z.read(registration))['files'].items():assert sha(z.read('source/'+name))==h
    result=dict(base_PR22_commit=base,historical_tracked_changes=[],candidates=candidates,
        frozen_tasks=lock['tasks'],actual_GPU_task_hashes_verified=True,frozen_source_pins=lock['source_pins'],builds=builds,dispatches=dispatches,
        raw_archives=archives,publication=dict(scanned_files_and_decoded_members=len(scan),known_credential_matches=0,signed_URL_matches=0,full_competition_overlay_matches=0),
        files={n:dict(bytes=len(b),sha256=sha(b)) for n,b in files.items()},self_hash_excluded=True)
    (HERE/'INTEGRITY_MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status='INTEGRITY_PASS',publication_scanned=len(scan),dispatches=dispatches)))

if __name__=='__main__':run()
