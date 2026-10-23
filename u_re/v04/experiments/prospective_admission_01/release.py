"""Final raw-evidence, history and public-payload checks. No network writes."""
import ast,base64,io,json,re,subprocess,zipfile
from pathlib import Path
from .common import HERE,ROOT,PRIOR,BASE,sha,write
from .acceptance import audit
from .audit import bind,screen
from .normalize import normalize

def seal():
    proof=json.loads((HERE/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
    assert proof==audit(proof['raw_archive_path'],proof['attempt']) and proof['status']=='V04_EGR_GPU_READY'
    selected_raw=(HERE/'SELECTED_TASKS.json').read_bytes()
    source=json.loads(selected_raw)['tasks'][0]['source_archive']
    screen(source['private_path']);normalize(source['private_path'])
    assert (HERE/'SELECTED_TASKS.json').read_bytes()==selected_raw,'Final admission cannot be a manual eligibility flag'
    changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    prefix=HERE.relative_to(ROOT).as_posix()+'/'
    assert all(n.startswith(prefix) for n in changed),'Historical tracked file modified'
    manifest=json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())
    assert sha((HERE/'payload.zip').read_bytes())==manifest['payload_sha256']==proof['payload_sha256']
    with zipfile.ZipFile(PRIOR/'payload.zip') as old:
        for n,h in manifest['files'].items():
            raw=(ROOT/n).read_bytes() if n.startswith(prefix) else old.read(n)
            assert sha(raw)==h,('Final accepted source drift',n)
    historical=json.loads((PRIOR/'INTEGRITY_MANIFEST.json').read_bytes())['candidates']
    for row in historical.values():
        raw=(ROOT/row['path']).read_bytes();assert sha(raw)==row['sha256']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None and {n:sha(z.read(n)) for n in z.namelist()}==row['members']
    claims=list(HERE.rglob('dispatch.claim'));assert len(claims)==3
    for claim in claims:assert len(list((claim.parent/'events').glob('*DISPATCH_STARTED.json')))==1
    assert not json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())['GPU_authorized']
    archives=[]
    for path,attempt in [(source['private_path'],'screen01'),(json.loads((HERE/'CPU_E2E02_ACCEPTANCE.json').read_bytes())['raw_archive_path'],'cpu-e2e02'),(proof['raw_archive_path'],proof['attempt'])]:
        record=bind(path,attempt);p=Path(path)
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            entries=[dict(file=n,bytes=z.getinfo(n).file_size,CRC32=format(z.getinfo(n).CRC,'08x'),sha256=sha(z.read(n))) for n in z.namelist() if not z.getinfo(n).is_dir()]
        write(p.parent/'ARCHIVE_FILES_SHA256.json',dict(files=entries));record['file_index_private_path']=str(p.parent/'ARCHIVE_FILES_SHA256.json');archives.append(record)
    write(HERE/'RAW_ARCHIVES.json',dict(CPU=archives,raw_contents_public=False,unexecuted_build='Private u_re_v04_unexecuted_cpu_build01; zero dispatch, excluded from actual Notebook count'))
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
    for secret in inventory()[-1]:
        if len(secret)>12:assert not any(secret.encode() in b for b in decoded.values()),'Credential publication blocked'
    for line in (ROOT.parent/'official-inputs/tasks.jsonl').read_text(encoding='utf8').splitlines():
        overlay=(json.loads(line).get('test_patch') or '').encode()
        if len(overlay)>80:assert not any(overlay in b for b in decoded.values()),'Evaluator overlay publication blocked'
    forbidden=('phase2.junit.xml','adk_events.jsonl','PRIVATE_BASE_SOURCE.json','final.patch','returned.patch','evaluator_test_text/')
    assert not any(any(f in n for f in forbidden) for n in decoded)
    signed=re.compile(rb'https://[^\s"<>]+[?&](?:X-Goog-Signature|X-Amz-Signature|Signature)=[a-zA-Z0-9%]{12,}')
    assert not any(signed.search(raw) for raw in decoded.values())
    write(HERE/'INTEGRITY_MANIFEST.json',dict(source_base=BASE,historical_tracked_changes=[],candidates=historical,accepted_production_payload_sha256=proof['payload_sha256'],accepted_runtime_sources_unchanged=True,task_selection_sha256=sha(selected_raw),environment_lock_sha256=sha((HERE/'ENVIRONMENT_LOCK.json').read_bytes()),ABBA_lock_sha256=sha((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes()),archives=archives,claims=[p.relative_to(HERE).as_posix() for p in claims],execution_totals=dict(CPU_Notebooks=3,CPU_SaveKernel=3,new_tasks_screened=3,native_baseline_rechecks=4,owned_scripted_sessions=4,scripted_HTTP=28,GPU_Notebooks=0,real_Gemma_requests=0,formal_Submissions=0),publication=dict(scanned_files_and_decoded_members=len(decoded),known_credential_matches=0,full_evaluator_overlay_matches=0,signed_URL_matches=0,raw_evaluator_or_trajectory_files_added=0,limit='Bounded known-secret/full-overlay/pattern checks plus source and role review, not universal leakage proof'),files={n:dict(bytes=len(raw),sha256=sha(raw)) for n,raw in files.items()},self_hash_excluded=True))
    print(json.dumps(dict(status='INTEGRITY_PUBLICATION_PASS',scanned=len(decoded),historical_changes=0,CPU_dispatches=3,GPU_dispatches=0)))

if __name__=='__main__':seal()
