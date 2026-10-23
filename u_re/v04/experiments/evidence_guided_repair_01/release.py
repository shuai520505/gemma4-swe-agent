"""Accepted runtime immutability and bounded publication checks; no execution."""
import ast,base64,io,json,re,subprocess,zipfile
from pathlib import Path
from .common import HERE,ROOT,BASE,sha,write
from .audit import audit_cpu

def seal():
    recorded=json.loads((HERE/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
    proof=audit_cpu(recorded['raw_archive_path'],recorded['attempt'])
    assert proof==recorded
    changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    assert all(n.startswith('u_re/v04/') for n in changed),'Historical tracked files changed'
    historical=json.loads((ROOT/'u_re/v02/experiments/env_recovery_admission_01/HISTORY_INTEGRITY.json').read_bytes())['candidates']
    candidates=dict(historical)
    build=json.loads((HERE/'CANDIDATE_BUILD_MANIFEST.json').read_bytes())
    candidates['EGR_V04']=dict(path=(HERE/'submission_egr_v04.zip').relative_to(ROOT).as_posix(),sha256=build['treatment_ZIP_sha256'],members=build['members'])
    for row in candidates.values():
        raw=(ROOT/row['path']).read_bytes();assert sha(raw)==row['sha256']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None and {n:sha(z.read(n)) for n in z.namelist()}==row['members']
    production=json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())
    assert sha((HERE/'payload.zip').read_bytes())==production['payload_sha256']==proof['payload_sha256']
    # The inherited builder intentionally synthesizes package initializers,
    # relocated resources and original approved wheel bytes. Those need to
    # match the previously accepted ZIP, not an unrelated working-tree path.
    inherited=ROOT/'u_re/v03/experiments/context_budget_01/payload.zip'
    inherited_manifest=json.loads((inherited.parent/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())
    assert sha(inherited.read_bytes())==inherited_manifest['payload_sha256']
    with zipfile.ZipFile(inherited) as old:
        for name,h in production['files'].items():
            raw=(ROOT/name).read_bytes() if name.startswith('u_re/v04/') else old.read(name)
            assert sha(raw)==h,('Accepted runtime changed after CPU',name)
    files={p.relative_to(HERE).as_posix():p.read_bytes() for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='INTEGRITY_MANIFEST.json'}
    decoded=dict(files)
    for name,raw in files.items():
        if name.endswith('.ipynb'):
            nb=json.loads(raw)
            line=next(s for s in nb['cells'][0]['source'].splitlines() if s.startswith("payload=__import__('base64').b64decode("))
            data=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
        elif name.endswith('.zip'):data=raw
        else:continue
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            assert z.testzip() is None
            decoded.update({name+'::'+p:z.read(p) for p in z.namelist()})
    from u_re.v01.experiments.fastapi_pilot_01.auth_diagnose import inventory
    for secret in inventory()[-1]:
        if len(secret)>12:assert not any(secret.encode() in b for b in decoded.values()),'Known credential publication blocked'
    for line in (ROOT.parent/'official-inputs/tasks.jsonl').read_text(encoding='utf8').splitlines():
        overlay=(json.loads(line).get('test_patch') or '').encode()
        if len(overlay)>80:assert not any(overlay in b for b in decoded.values()),'Evaluator overlay publication blocked'
    forbidden=('phase2.junit.xml','adk_events.jsonl','PRIVATE_BASE_SOURCE.json','final.patch','returned.patch','evaluator_test_text/')
    assert not any(any(f in n for f in forbidden) for n in decoded)
    signed=re.compile(rb'https://[^\s"<>]+[?&](?:X-Goog-Signature|X-Amz-Signature|Signature)=[a-zA-Z0-9%]{12,}')
    assert not any(signed.search(raw) for raw in decoded.values())
    claims=list(HERE.rglob('dispatch.claim'));assert len(claims)==1
    assert len(list((claims[0].parent/'events').glob('*DISPATCH_STARTED.json')))==1
    assert not json.loads((HERE/'GPU_REPLICATION_PROTOCOL.json').read_bytes())['GPU_authorized']
    path=Path(proof['raw_archive_path'])
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        entries=[dict(file=n,bytes=z.getinfo(n).file_size,CRC32=format(z.getinfo(n).CRC,'08x'),sha256=sha(z.read(n))) for n in z.namelist() if not z.getinfo(n).is_dir()]
    write(path.parent/'ARCHIVE_FILES_SHA256.json',dict(files=entries))
    archive=dict(path=str(path),sha256=proof['raw_archive_sha256'],bytes=path.stat().st_size,CRC_valid=True,file_index_path=str(path.parent/'ARCHIVE_FILES_SHA256.json'))
    write(HERE/'RAW_ARCHIVES.json',dict(CPU=archive,historical_traces=json.loads((HERE/'TRACE_BEHAVIOR_METRICS.json').read_bytes())['archives'],raw_contents_public=False))
    files['RAW_ARCHIVES.json']=(HERE/'RAW_ARCHIVES.json').read_bytes()
    write(HERE/'INTEGRITY_MANIFEST.json',dict(source_base=BASE,pre_dispatch_source_commit=subprocess.check_output(['git','rev-parse','8ef16bd'],cwd=ROOT,text=True).strip(),historical_tracked_changes=[],candidates=candidates,production_payload_sha256=production['payload_sha256'],accepted_production_sources_unchanged=True,CPU_acceptance_raw_sha256=proof['raw_archive_sha256'],prospective_GPU_protocol_sha256=sha((HERE/'GPU_REPLICATION_PROTOCOL.json').read_bytes()),claims=[p.relative_to(HERE).as_posix() for p in claims],actual_current_scope=dict(CPU_Notebooks=1,CPU_SaveKernel=1,scripted_HTTP=14,GPU_Notebooks=0,real_Gemma_requests=0,formal_Submissions=0),publication=dict(scanned_files_and_decoded_members=len(decoded),known_credential_matches=0,full_evaluator_overlay_matches=0,signed_URL_matches=0,raw_trace_or_evaluator_files_added=0,limit='Known credential/full overlay/pattern checks plus source/role review; not a universal secret detector'),files={n:dict(bytes=len(b),sha256=sha(b)) for n,b in files.items()},self_hash_excluded=True))
    print(json.dumps(dict(status='INTEGRITY_PUBLICATION_PASS',scanned=len(decoded),CPU_dispatches=1,GPU_dispatches=0,accepted_runtime_unchanged=True,historical_tracked_changes=0)))

if __name__=='__main__':seal()
