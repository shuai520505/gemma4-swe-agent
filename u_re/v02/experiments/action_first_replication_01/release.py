"""Offline publication/integrity seal; never executes tasks or calls a service."""
import io,json,re,subprocess,zipfile
from pathlib import Path
from .selection import HERE,ROOT,sha,write

def run():
    pool=json.loads((HERE/'TASK_POOL_FREEZE.json').read_bytes())
    archive=json.loads((HERE/'TASK_ADMISSION_LEDGER.json').read_bytes())['source_archive']['path']
    original=ROOT/'u_re/v01/experiments/action_priority_01/integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json'
    lock=json.loads(original.read_bytes())
    tasks=ROOT.parent/'official-inputs/tasks.jsonl'
    metadata=json.loads((ROOT/'u_re/v01/experiments/mechanism_02/TASK_POOL_METADATA.json').read_bytes())
    assert sha(tasks.read_bytes())==metadata['source_sha256']
    approved={r['instance_id']:r for r in map(json.loads,tasks.read_text(encoding='utf-8').splitlines())}
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        sources=json.loads(z.read('validation/official_source_hashes.json'))
        assert sources==lock['native_verifier_source_sha256']
        identities=json.loads(z.read('validation/SNAPSHOT_ALIAS_CHECK.json'))['all_task_identities']
        assert len(identities)==129
        for ident,r in identities.items():assert r['task_record_sha256']==sha(json.dumps(approved[ident],sort_keys=True).encode())
        dependency=json.loads(z.read('validation/dependency_smoke/cleanup.json'))
        detached=json.loads(z.read('validation/dependency_smoke/DETACHED_SESSION_PROOF.json'))
        assert dependency['complete'] and all(detached[k] for k in ('timeout_detached_PID_gone','abort_detached_PID_gone','UID_ownership_verified'))
    write(HERE/'INPUT_INTEGRITY_AUDIT.json',dict(approved_tasks_file_sha256=sha(tasks.read_bytes()),canonical_record_matches=129,canonical_record_mismatches=[],native_Verifier_source_hashes=sources,native_Verifier_matches_approved_lock=True,detached_child_timeout_and_abort_cleanup=True,dependency_chroot_clean=True,new_reference_patch_access=False,scope='Offline comparison to actual frozen Notebook outputs, not a new baseline or model run'))
    candidates={}
    for key,row in pool['candidates'].items():
        raw=(ROOT/row['path']).read_bytes();assert sha(raw)==row['sha256']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            candidates[key]=dict(path=row['path'],sha256=sha(raw),members={n:sha(z.read(n)) for n in z.namelist()},CRC_valid=True)
    prefix=HERE.relative_to(ROOT).as_posix()+'/'
    changed=subprocess.check_output(['git','diff','--name-only','f5beac9979a0a9d307b14f686d3477b09a021a95'],cwd=ROOT,text=True).splitlines()
    assert all(p.startswith(prefix) for p in changed),'Historical tracked files changed'
    # Inspect decoded upload ZIPs, not just opaque Notebook base64.
    forbidden=('evaluator_test_text/','native_evidence/','phase2.junit.xml','adk_events.jsonl','final.patch','returned.patch','reference_patch','gold_patch')
    bad=[];inspected=[]
    secret=re.compile(rb'(?:KGAT_[A-Za-z0-9_-]{20,}|eyJhbGciOi[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|https?://[^\s"<>]+[?&](?:X-Amz-Signature|X-Goog-Signature)=)')
    for p in HERE.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts:continue
        if secret.search(p.read_bytes()):bad.append(p.relative_to(HERE).as_posix())
        if p.name=='screen_payload.zip':
            with zipfile.ZipFile(p) as z:
                assert z.testzip() is None
                for n in z.namelist():
                    assert not any(k in n for k in forbidden),('Raw evaluator publication',n)
                    if secret.search(z.read(n)):bad.append(p.name+':'+n)
            inspected.append(dict(path=p.relative_to(HERE).as_posix(),sha256=sha(p.read_bytes()),decoded_members=len(z.namelist())))
    assert not bad,('Publication review required',bad)
    write(HERE/'PUBLICATION_CHECK.json',dict(status='SAFE_DERIVED_METADATA_AND_CODE_ONLY',decoded_uploads=inspected,secret_pattern_matches=0,raw_evaluator_or_model_trace_files_added=0,history_rewritten=False,limitations='Narrow secret-pattern scan plus manifest/file-role review, not proof against all possible secrets. No new Agent ran; future context isolation is not claimed verified by this screening.'))
    files={p.relative_to(HERE).as_posix():sha(p.read_bytes()) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='INTEGRITY_MANIFEST.json'}
    write(HERE/'INTEGRITY_MANIFEST.json',dict(base_commit='f5beac9979a0a9d307b14f686d3477b09a021a95',preregistration_commit='c3cfb75418e6e9b34a88542c722d5c496f9dd031',historical_tracked_changes=[],candidates=candidates,files=files,source_scope='New V02 study only; prior research, candidate ZIPs and unrelated untracked directory untouched',self_hash_excluded=True))
    print(json.dumps(dict(publication='PASS',new_files=len(files),historical_changes=0,candidates_unchanged=True)))

if __name__=='__main__':run()
