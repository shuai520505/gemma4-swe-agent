"""Offline integrity/publication seal; no experiment, model or network calls."""
import ast,base64,io,json,re,subprocess,zipfile
from pathlib import Path
from .notebook import HERE,ROOT,PREP,BASE,sha,verify_shared
from .results import write

def run():
    lock,proof=verify_shared();prefix=HERE.relative_to(ROOT).as_posix()+'/'
    changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    assert all(n.startswith(prefix) for n in changed),'Historical tracked files changed'
    candidates=json.loads((PREP/'HISTORY_INTEGRITY.json').read_bytes())['candidates']
    for name,row in candidates.items():
        raw=(ROOT/row['path']).read_bytes();assert sha(raw)==row['sha256']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None and {n:sha(z.read(n)) for n in z.namelist()}==row['members']
    files={p.relative_to(HERE).as_posix():p.read_bytes() for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='INTEGRITY_MANIFEST.json'}
    decoded=dict(files)
    for n,raw in files.items():
        if not n.endswith('.ipynb'):continue
        nb=json.loads(raw)
        line=next(s for s in nb['cells'][0]['source'].splitlines() if s.startswith("payload=__import__('base64').b64decode("))
        payload=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
        assert sha(payload)==proof['payload_sha256']
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            assert z.testzip() is None
            decoded.update({n+'::'+p:z.read(p) for p in z.namelist()})
    from u_re.v01.experiments.fastapi_pilot_01.auth_diagnose import inventory
    for value in inventory()[-1]:
        if len(value)>12:assert not any(value.encode() in b for b in decoded.values()),'Known credential publication blocked'
    for line in (ROOT.parent/'official-inputs/tasks.jsonl').read_text(encoding='utf8').splitlines():
        overlay=(json.loads(line).get('test_patch') or '').encode()
        if len(overlay)>80:assert not any(overlay in b for b in decoded.values()),'Raw competition overlay publication blocked'
    forbidden=('phase2.junit.xml','adk_events.jsonl','PRIVATE_BASE_SOURCE.json','final.patch','returned.patch','evaluator_test_text/')
    assert not any(any(f in n for f in forbidden) for n in decoded),'Raw evidence file publication blocked'
    pattern=re.compile(rb'https://[^\s"<>]+[?&](?:X-Goog-Signature|X-Amz-Signature|Signature)=[a-zA-Z0-9%]{12,}')
    assert not any(pattern.search(raw) for raw in decoded.values()),'Signed URL publication blocked'
    dispatches={}
    for claim in HERE.rglob('dispatch.claim'):
        states=list((claim.parent/'events').glob('*DISPATCH_STARTED.json'));assert len(states)==1
        dispatches[claim.relative_to(HERE).as_posix()]=1
    assert len(dispatches)<=2
    if (HERE/'RAW_ARCHIVES.json').exists():
        for row in json.loads((HERE/'RAW_ARCHIVES.json').read_bytes())['archives']:
            path=Path(row['private_archive']);assert sha(path.read_bytes())==row['archive_sha256']
            with zipfile.ZipFile(path) as z:
                assert z.testzip() is None
                index=[dict(file=n,bytes=z.getinfo(n).file_size,CRC32=format(z.getinfo(n).CRC,'08x'),sha256=sha(z.read(n))) for n in z.namelist() if not z.getinfo(n).is_dir()]
            write(path.parent/'ARCHIVE_FILES_SHA256.json',dict(Notebook_id=row['Notebook_id'],version=1,files=index))
    write(HERE/'INTEGRITY_MANIFEST.json',dict(base_commit=BASE,historical_tracked_changes=[],CPU_acceptance_raw_archive_sha256=proof['raw_archive_sha256'],shared_payload_sha256=proof['payload_sha256'],candidates=candidates,task_lock_sha256=sha((PREP/'production/ABBA_EXPERIMENT_LOCK.json').read_bytes()),environment_lock_sha256=sha((PREP/'V02B_ENVIRONMENT_LOCK.json').read_bytes()),authorization_sha256=sha((HERE/'GPU_AUTHORIZATION_RECORD.json').read_bytes()),dispatches=dispatches,publication=dict(scanned_files_and_decoded_members=len(decoded),known_credential_matches=0,signed_URL_matches=0,full_competition_overlay_matches=0,raw_evaluator_trace_or_patch_files_added=0,limit='Known-secret/overlay-pattern scan plus file-role review; raw evidence remains outside Git.'),files={n:dict(bytes=len(raw),sha256=sha(raw)) for n,raw in files.items()},self_hash_excluded=True))
    print(json.dumps(dict(status='INTEGRITY_PUBLICATION_PASS',dispatches=len(dispatches),historical_changes=0,scanned=len(decoded))))

if __name__=='__main__':run()
