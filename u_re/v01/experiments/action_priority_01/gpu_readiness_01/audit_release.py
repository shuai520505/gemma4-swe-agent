"""Final additive-only/history/candidate and safe-artifact identity audit."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
BASE='363a8fa1dce91d9563007f73c6a7b57d23be78c4'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    candidates={}
    for name,path,expected in [('NoEGV','u_re/v01/submission_noegv.zip','2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608'),
        ('ActionFirst','u_re/v01/experiments/action_priority_01/submission_action_v01.zip','70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8'),
        ('Full','u_re/v01/submission_full.zip','887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821')]:
        raw=(ROOT/path).read_bytes();assert sha(raw)==expected
        with zipfile.ZipFile(ROOT/path) as z:
            assert z.testzip() is None and set(z.namelist())=={'agent.yaml','eval_config.yaml','prompts/system.md'}
            members={n:sha(z.read(n)) for n in z.namelist()}
        candidates[name]=dict(path=path,sha256=expected,members=members,CRC_valid=True)
    for n in ('agent.yaml','eval_config.yaml'):
        assert candidates['NoEGV']['members'][n]==candidates['ActionFirst']['members'][n]==candidates['Full']['members'][n]
    # Verify every tracked baseline file's exact Git blob survives. This also
    # protects old failures and unmerged research branches inherited in PR19.
    records=subprocess.check_output(['git','ls-tree','-r',BASE],cwd=ROOT).decode().splitlines()
    missing=[];changed=[];checkout_newline_only=[]
    for row in records:
        meta,name=row.split('\t');mode,kind,oid=meta.split()
        if kind!='blob':continue
        p=ROOT/name
        if not p.exists():missing.append(name);continue
        raw=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob!=oid:
            clean=raw.replace(b'\r\n',b'\n')
            if hashlib.sha1(b'blob '+str(len(clean)).encode()+b'\0'+clean).hexdigest()==oid:
                checkout_newline_only.append(name)
            else:changed.append(name)
    assert not missing and not changed,(missing,changed)
    # Existing credential values are compared only in memory,never logged or
    # hashed into the report. Also inspect decoded Notebook ZIP members.
    from u_re.v01.experiments.fastapi_pilot_01.auth_diagnose import inventory
    import ast,base64,io,re
    secrets=[v.encode() for v in inventory()[3] if len(v)>8]
    checked=0;payload_checked=0
    def scan(raw):
        nonlocal checked
        checked+=1
        assert not any(s in raw for s in secrets),'Credential match; refuse publication'
        assert not re.search(rb'(?i)(?:X-Goog-Signature|X-Amz-Signature|access_token)=[A-Za-z0-9._%+-]{16,}',raw),'Sensitive URL match'
    for p in HERE.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts:continue
        scan(p.read_bytes())
        if p.name=='study.ipynb':
            nb=json.loads(p.read_bytes());tree=ast.parse(nb['cells'][0]['source'])
            assign=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='payload' for t in n.targets))
            payload=base64.b64decode(ast.literal_eval(assign.value.args[0]))
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                assert z.testzip() is None
                for name in z.namelist():
                    assert not any(x in name.lower() for x in ('evaluator_test_text','phase2.junit','reference.patch','gold.patch','tasks.jsonl'))
                    scan(z.read(name));payload_checked+=1
    # Existing history is not re-published; only this safe additive directory.
    files={p.relative_to(HERE).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
        for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='INTEGRITY_MANIFEST.json'}
    report=dict(base_commit=BASE,history_blobs_checked=len(records),history_missing=missing,history_changed=changed,
        existing_Windows_checkout_CRLF_only=checkout_newline_only,
        newline_note='Initial worktree was Git-clean. These pre-existing CRLF checkout forms match baseline Git blobs after LF normalization; they were not rewritten. Candidate ZIPs and all new build hashes are always raw bytes.',
        publication_scan=dict(new_files_and_decoded_members_checked=checked,payload_members_checked=payload_checked,
            known_credential_value_matches=0,signed_URL_matches=0,original_task_test_or_reference_artifacts_added=False),
        candidates=candidates,files=files,publication='Owned synthetic data,code and whitelisted safe API fields only;raw output archives outside public checkout',
        limitation='Historical evaluator-publication concern remains; this audit adds no original evaluator or answer contents')
    (HERE/'INTEGRITY_MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(history_blobs_checked=len(records),history_changed=len(changed),candidate_CRC=True,new_files=len(files))))


if __name__=='__main__':main()
