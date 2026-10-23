"""Offline raw-evidence replay, publication scan and additive history seal."""
import ast,base64,io,json,re,subprocess,zipfile
from pathlib import Path
from .dependencies import HERE,ROOT,ID,sha,write
from .production_audit import audit

BASE='6f6b7500baa007ee317466b93329ce99cf58950e'

def run():
    proof=json.loads((HERE/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
    assert audit(proof['raw_archive_path'],proof['attempt'])==proof,'Acceptance must be re-derived from raw bytes'
    archive_rows=[]
    for attempt in ('recovery01','recovery02','screen01','e2e02'):
        directory=HERE/attempt
        receipt=json.loads((directory/'execution/HTTP_RECEIPT.json').read_bytes())
        manifests=sorted((directory/'read_observations').glob('read-*/OUTPUT_MANIFEST.json'))
        manifest=next(json.loads(p.read_bytes()) for p in reversed(manifests) if json.loads(p.read_bytes()).get('files'))
        item=next(f for f in manifest['files'] if f['file']=='v02b-'+attempt+'.zip')
        private=ROOT.parent/'private-evidence'/('u_re_v02b_'+attempt)
        path=next(p for p in private.rglob(item['file']) if p.stat().st_size and sha(p.read_bytes())==item['sha256'])
        assert item['Notebook_id']==receipt['Notebook_id'] and item['version']==receipt['accepted_version']==1
        assert manifest['version_bound_before_after'] and item['complete']
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            files=[dict(file=n,bytes=z.getinfo(n).file_size,CRC32=format(z.getinfo(n).CRC,'08x'),sha256=sha(z.read(n))) for n in z.namelist() if not z.getinfo(n).is_dir()]
            # Per-file original evidence remains private, including filenames.
            write(path.parent/'ARCHIVE_FILES_SHA256.json',dict(Notebook_id=receipt['Notebook_id'],version=1,files=files))
        claim=json.loads((directory/'DISPATCH_SUMMARY.json').read_bytes());assert claim['dispatches']==1
        build=json.loads((directory/'BUILD_FREEZE.json').read_bytes())
        source_commit=build.get('source_commit') or json.loads((directory/'SOURCE_COMMIT.json').read_bytes())['source_commit']
        seal={'recovery01':'b5f356d','recovery02':'21c48fa','screen01':'6da9ce5','e2e02':'89fddb8'}[attempt]
        seal=subprocess.check_output(['git','rev-parse',seal],cwd=ROOT,text=True).strip()
        archive_rows.append(dict(attempt=attempt,Notebook_id=receipt['Notebook_id'],version=1,status=manifest['status'],dispatches=1,source_commit_at_build=source_commit,sealed_dispatch_commit=seal,payload_sha256=json.loads((directory/'BUILD.json').read_bytes())['payload_sha256'],private_archive=str(path),sha256=sha(path.read_bytes()),bytes=path.stat().st_size,CRC_valid=True,member_files=len(files),private_file_hash_manifest=str(path.parent/'ARCHIVE_FILES_SHA256.json'),version_bound_before_after=True,original_UNKNOWN_STOP_preserved=True))
    assert [r['status'] for r in archive_rows]==['ERROR','COMPLETE','COMPLETE','COMPLETE']
    write(HERE/'RAW_ARCHIVES.json',dict(experiment_id=ID,archives=archive_rows,CPU_Notebooks=4,new_SaveKernel_dispatches=4,GPU_Notebooks=0,real_Gemma_requests=0,real_SWE_Agent_sessions=0,owned_scripted_Agent_sessions=1,formal_Submissions=0,real_SWE_native_verifier_executions=13,prospective_new_tasks_checked=3,local_pre_dispatch_seal_rejection=dict(attempt='e2e01',Notebook_id=None,dispatches=0,status='LOCAL_BUILD_REJECTED_NOT_DISPATCHED',reason='Immutable sealed Notebook rejected a different rebuild before any launch; distinct e2e02 validated the final payload. Existing e2e01 BUILD remains historical, not accepted.'),CPU_cost='No exact per-Notebook bill exposed. Native durations and CPU session logs retained privately. GPU report quota read is an account snapshot, not a CPU or GPU bill.'))
    candidates={}
    for key,name,expected in (
        ('A','u_re/v01/submission_noegv.zip','2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608'),
        ('B','u_re/v01/experiments/action_priority_01/submission_action_v01.zip','70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8'),
        ('Full','u_re/v01/submission_full.zip','887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821')):
        raw=(ROOT/name).read_bytes();assert sha(raw)==expected
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            candidates[key]=dict(path=name,sha256=sha(raw),members={n:sha(z.read(n)) for n in z.namelist()},CRC_valid=True)
    prefix=HERE.relative_to(ROOT).as_posix()+'/'
    changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    assert all(n.startswith(prefix) for n in changed),'Historical tracked file changed'
    write(HERE/'HISTORY_INTEGRITY.json',dict(base_commit=BASE,historical_tracked_file_changes=[],candidates=candidates,approved_tasks_source_sha256=sha((ROOT.parent/'official-inputs/tasks.jsonl').read_bytes()),V02_original_STOP_preserved=True,prior_GPU_results_preserved=True,unrelated_untracked_directory='u_re/v01/experiments/dependency_security_review_01/ untouched',reference_patch_read=False))
    bad=[];decoded=[]
    secret=re.compile(rb'(?:KGAT_[A-Za-z0-9_-]{20,}|eyJhbGciOi[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|https?://[^\s"<>]+[?&](?:X-Amz-Signature|X-Goog-Signature)=)')
    forbidden=('evaluator_test_text/','native_evidence/','phase2.junit.xml','adk_events.jsonl','final.patch','returned.patch','reference_patch','gold_patch','PRIVATE_BASE_SOURCE.json')
    def inspect_zip(raw,label):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            for name in z.namelist():
                assert not any(x in name for x in forbidden),('Raw evidence cannot be published',label,name)
                if secret.search(z.read(name)):bad.append(label+':'+name)
            decoded.append(dict(path=label,sha256=sha(raw),members=len(z.namelist())))
    for p in HERE.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts:continue
        raw=p.read_bytes();label=p.relative_to(HERE).as_posix()
        if secret.search(raw):bad.append(label)
        if p.suffix=='.zip':inspect_zip(raw,label)
        elif p.suffix=='.ipynb':
            nb=json.loads(raw)
            for cell in nb['cells']:
                for line in cell['source'].splitlines():
                    if line.startswith("payload=__import__('base64').b64decode("):
                        embedded=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]));inspect_zip(embedded,label+':decoded_payload')
    assert not bad,('Publication/credential review required',bad)
    write(HERE/'PUBLICATION_CHECK.json',dict(status='SAFE_CODE_DERIVED_METADATA_AND_VERIFIED_PUBLIC_WHEELS',decoded_payloads=decoded,secret_pattern_matches=[],raw_evaluator_files_added=0,private_raw_archives_outside_Git=True,Agent_context_boundary='Real CPU production canary and chroot passed; new evaluator wheels only on trusted side; no evaluator or other-arm artifacts copied into Agent workspace. No new real SWE Agent or Gemma Session ran.',limitations='Pattern scan plus file-role review is not a proof against every possible secret or historical publication concern. Historical public evidence was not republished into this study or rewritten.'))
    files={p.relative_to(HERE).as_posix():sha(p.read_bytes()) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='INTEGRITY_MANIFEST.json'}
    write(HERE/'INTEGRITY_MANIFEST.json',dict(base_commit=BASE,initial_preregistration_commit='6456212',environment_and_policy_freeze_commit='21377a3',screen_dispatch_source_commit='6da9ce5',production_acceptance_dispatch_commit='89fddb8',historical_tracked_changes=[],candidates=candidates,files=files,self_hash_excluded=True))
    print(json.dumps(dict(publication='PASS',CPU_Notebooks=4,selected_tasks=4,prospective_new=3,local_file_hashes=len(files),historical_changes=0)))

if __name__=='__main__':run()
