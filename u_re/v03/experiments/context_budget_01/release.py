"""Reused publication checks and immutable historical fingerprints; offline only."""
import ast,base64,io,json,re,subprocess,zipfile
from pathlib import Path
from .common import HERE,ROOT,BASE,write,sha
from .notebook import verify_cpu
def seal():
    proof=verify_cpu();prefix='u_re/v03/'
    changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    assert all(n.startswith(prefix) for n in changed),'Historical files changed'
    prior=ROOT/'u_re/v02/experiments/env_recovery_admission_01/HISTORY_INTEGRITY.json'
    candidates=json.loads(prior.read_bytes())['candidates']
    for row in candidates.values():
        raw=(ROOT/row['path']).read_bytes();assert sha(raw)==row['sha256']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None and {n:sha(z.read(n)) for n in z.namelist()}==row['members']
    files={p.relative_to(HERE).as_posix():p.read_bytes() for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='INTEGRITY_MANIFEST.json'}
    decoded=dict(files)
    for n,raw in files.items():
        if n.endswith('.ipynb'):
            nb=json.loads(raw);line=next(s for s in nb['cells'][0]['source'].splitlines() if s.startswith("payload=__import__('base64').b64decode("))
            data=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
        elif n.endswith('.zip'):data=raw
        else:continue
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            assert z.testzip() is None;decoded.update({n+'::'+p:z.read(p) for p in z.namelist()})
    from u_re.v01.experiments.fastapi_pilot_01.auth_diagnose import inventory
    for value in inventory()[-1]:
        if len(value)>12:assert not any(value.encode() in b for b in decoded.values()),'Known credential publication blocked'
    for line in (ROOT.parent/'official-inputs/tasks.jsonl').read_text(encoding='utf8').splitlines():
        overlay=(json.loads(line).get('test_patch') or '').encode()
        if len(overlay)>80:assert not any(overlay in b for b in decoded.values()),'Evaluator overlay publication blocked'
    forbidden=('phase2.junit.xml','adk_events.jsonl','PRIVATE_BASE_SOURCE.json','final.patch','returned.patch','evaluator_test_text/')
    assert not any(any(f in n for f in forbidden) for n in decoded)
    pattern=re.compile(rb'https://[^\s"<>]+[?&](?:X-Goog-Signature|X-Amz-Signature|Signature)=[a-zA-Z0-9%]{12,}')
    assert not any(pattern.search(b) for b in decoded.values())
    claims=list(HERE.rglob('dispatch.claim'));assert len(claims)==2
    for claim in claims:assert len(list((claim.parent/'events').glob('*DISPATCH_STARTED.json')))==1
    assert sum('/gpu01/' in p.as_posix() for p in claims)==1
    archives=[]
    for row in [dict(path=proof['raw_archive_path'],sha256=proof['raw_archive_sha256'])]+(json.loads((HERE/'RAW_ARCHIVES.json').read_bytes()).get('GPU',[]) if (HERE/'RAW_ARCHIVES.json').exists() else []):
        path=Path(row['path']);assert sha(path.read_bytes())==row['sha256']
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            entries=[dict(file=n,bytes=z.getinfo(n).file_size,CRC32=format(z.getinfo(n).CRC,'08x'),sha256=sha(z.read(n))) for n in z.namelist() if not z.getinfo(n).is_dir()]
        write(path.parent/'ARCHIVE_FILES_SHA256.json',dict(files=entries))
        archives.append(dict(path=str(path),sha256=row['sha256'],bytes=path.stat().st_size,CRC_valid=True))
    write(HERE/'INTEGRITY_MANIFEST.json',dict(base_commit=BASE,historical_tracked_changes=[],candidates=candidates,production_payload_sha256=sha((HERE/'payload.zip').read_bytes()),CPU_acceptance_raw_sha256=proof['raw_archive_sha256'],policy_sha256=sha((HERE/'CONTEXT_POLICY_FREEZE.json').read_bytes()),authorization_sha256=sha((HERE/'GPU_AUTHORIZATION_RECORD.json').read_bytes()),claims=[p.relative_to(HERE).as_posix() for p in claims],archives=archives,publication=dict(scanned_files_and_decoded_members=len(decoded),known_credential_matches=0,full_evaluator_overlay_matches=0,signed_URL_matches=0,raw_trace_or_evaluator_files_added=0,limit='Known credential/full overlay/pattern scan plus role review; not a universal secret detector'),files={n:dict(bytes=len(b),sha256=sha(b)) for n,b in files.items()},self_hash_excluded=True))
    print(json.dumps(dict(status='INTEGRITY_PUBLICATION_PASS',scanned=len(decoded),claims=len(claims),historical_changes=0)))
if __name__=='__main__':seal()
