"""Final narrow integrity/publication check;no network or experiment execution."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile
from .GPU_NOTEBOOK import HERE,ROOT,PRIOR,sha

def run():
    prefix=HERE.relative_to(ROOT).as_posix()+'/'
    changed=subprocess.check_output(['git','diff','--name-only','804681b1cb546d629c750096ea9e6b371e1d0a4c'],cwd=ROOT,text=True).splitlines()
    assert all(p.startswith(prefix) for p in changed),'Historical tracked file changed'
    candidates={}
    for path,wanted in (
        ('u_re/v01/submission_noegv.zip','2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608'),
        ('u_re/v01/submission_full.zip','887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821'),
        ('u_re/v01/experiments/action_priority_01/submission_action_v01.zip','70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8')):
        raw=(ROOT/path).read_bytes();assert sha(raw)==wanted
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None and set(z.namelist())=={'agent.yaml','eval_config.yaml','prompts/system.md'}
            candidates[path]=dict(sha256=wanted,members={n:sha(z.read(n)) for n in z.namelist()},CRC_valid=True)
    lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    for n,h in lock['source_pins'].items():assert sha((PRIOR/n).read_bytes())==h
    data=ROOT.parent/'official-inputs'
    records={r['instance_id']:r for r in map(json.loads,(data/'tasks.jsonl').read_text(encoding='utf-8').splitlines())}
    snapshot_checks={}
    original=ROOT.parent/'private-evidence/u_re_integrated_screen01/read-02/evidence_confirmed/output/u_re_integrated_screen01.zip'
    assert sha(original.read_bytes())==json.loads((PRIOR/'SELECTED_TASKS.json').read_bytes())['archive_sha256']
    with zipfile.ZipFile(original) as z:original_identities=json.loads(z.read('validation/INPUT_IDENTITIES_BEFORE_EXECUTION.json'))
    for frozen in lock['tasks']:
        row=records[frozen['instance_id']]
        assert sha(json.dumps(row,sort_keys=True).encode())==frozen['task_record_sha256']
        assert sha(row['problem_statement'].encode())==frozen['issue_sha256']
        assert sha(row['test_patch'].encode())==frozen['test_patch_sha256']
        for n,h in frozen['input_files'].items():
            if (data/n).is_file():
                assert sha((data/n).read_bytes())==h;snapshot_checks[n]='CURRENT_LOCAL_BYTES_MATCH'
            else:
                assert original_identities[frozen['instance_id']]['input_files'][n]==h
                snapshot_checks[n]='NOT_LOCALLY_PRESENT;matched original hash-verified CPU archive identity;GPU rehash stage NOT_REACHED'
    # Both executed builds and their payloads retain original sealed SHA bytes.
    for attempt in (HERE,HERE/'repair_cpu01'):
        spec=json.loads((attempt/'BUILD.json').read_bytes());notebook=(attempt/'notebook/study.ipynb').read_bytes()
        assert sha(notebook)==spec['Notebook_sha256'] and sha(json.dumps(json.loads(notebook)).encode())==spec['wire_sha256']
        receipt=json.loads((attempt/'execution/HTTP_RECEIPT.json').read_bytes());assert receipt['accepted_version']==1
        assert len(list((attempt/'execution/events').glob('*DISPATCH_STARTED.json')))==1
    files={p.relative_to(HERE).as_posix():p.read_bytes() for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='INTEGRITY_MANIFEST.json'}
    scan=dict(files)
    for n,b in files.items():
        if not n.endswith('.ipynb'):continue
        nb=json.loads(b)
        first=nb['cells'][0]['source'];first=''.join(first) if isinstance(first,list) else first
        line=next((l for l in first.splitlines() if l.startswith("payload=__import__('base64').b64decode(")),None)
        if not line:continue
        payload=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            assert z.testzip() is None
            scan.update({n+'::'+name:z.read(name) for name in z.namelist()})
    from u_re.v01.experiments.fastapi_pilot_01.auth_diagnose import inventory
    secrets=inventory()[-1]
    for secret in secrets:
        if len(secret)>12:assert not any(secret.encode() in raw for raw in scan.values()),'Credential in public files'
    for record in records.values():
        overlay=(record.get('test_patch') or '').encode()
        if len(overlay)>80:assert not any(overlay in raw for raw in scan.values()),'Full competition evaluator overlay in public files'
    for raw in scan.values():assert not re.search(rb'https://[^\s"<>]+[?&](?:X-Goog-Signature|X-Amz-Signature|Signature)=[a-zA-Z0-9%]{12,}',raw),'Signed URL found'
    manifests=json.loads((HERE/'RAW_ARCHIVES.json').read_bytes())
    for m in manifests:
        path=ROOT.parent/'private-evidence'/m['storage'].removeprefix('PRIVATE_EVIDENCE_ROOT/')
        assert sha(path.read_bytes())==m['sha256']
        with zipfile.ZipFile(path) as z:assert z.testzip() is None
    result=dict(base_PR21_commit='804681b1cb546d629c750096ea9e6b371e1d0a4c',historical_tracked_changes=[],
        GPU_execution_source_commit='2f3b855',CPU_repair_source_commit='d0d6ff64b1d46515588aae36b4cf86ba92409634',
        candidates=candidates,frozen_tasks=lock['tasks'],snapshot_checks=snapshot_checks,frozen_source_pins=lock['source_pins'],raw_archives=manifests,
        GPU_dispatches=1,CPU_dispatches=1,real_Gemma_requests=0,Agent_runs=0,new_native_baselines=0,formal_submissions=0,
        publication=dict(scanned_files_and_decoded_members=len(scan),known_credential_matches=0,signed_URL_matches=0,full_competition_overlay_matches=0),
        files={n:dict(bytes=len(b),sha256=sha(b)) for n,b in files.items()},self_hash_excluded=True)
    (HERE/'INTEGRITY_MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status='INTEGRITY_PASS',scanned=len(scan),history_changed=0,candidate_SHA_changes=0,GPU_dispatches=1,CPU_dispatches=1)))

if __name__=='__main__':run()
