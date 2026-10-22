"""Additive-only release audit;raw competition evaluator evidence stays private."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
BASE='1a90f2914a715b2452dfd2864b4ca7ac1d911920'


def digest(raw):return hashlib.sha256(raw).hexdigest()


def run():
    history=subprocess.check_output(['git','ls-tree','-r',BASE],cwd=ROOT).decode().splitlines()
    newline_only=[]
    for line in history:
        meta,path=line.split('\t');mode,kind,oid=meta.split()
        if kind!='blob':continue
        raw=(ROOT/path).read_bytes()
        blob=lambda value:hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()
        if blob(raw)==oid:continue
        assert blob(raw.replace(b'\r\n',b'\n'))==oid,('Historical content drift',path)
        newline_only.append(path)
    candidates={}
    for name,path,folder,sha in [('NoEGV','u_re/v01/submission_noegv.zip','u_re/v01/candidate_noegv','2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608'),
        ('ActionFirst','u_re/v01/experiments/action_priority_01/submission_action_v01.zip','u_re/v01/experiments/action_priority_01/candidate_action_v01','70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8'),
        ('Full','u_re/v01/submission_full.zip','u_re/v01/candidate_full','887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821')]:
        assert digest((ROOT/path).read_bytes())==sha
        with zipfile.ZipFile(ROOT/path) as z:
            assert z.testzip() is None and set(z.namelist())=={'agent.yaml','eval_config.yaml','prompts/system.md'}
            members={n:digest(z.read(n)) for n in z.namelist()}
            assert all(z.read(n)==(ROOT/folder/n).read_bytes() for n in z.namelist())
        candidates[name]=dict(path=path,sha256=sha,members=members,CRC=True,compiled_directory_matches=True)
    archives={}
    for attempt,number in [('runner01',140215143),('runner02',140216241),('screen01',140218227),('taskruntime01',140220306)]:
        directory=HERE/attempt
        receipt=json.loads((directory/'execution/HTTP_RECEIPT.json').read_bytes());summary=json.loads((directory/'DISPATCH_SUMMARY.json').read_bytes())
        assert receipt['Notebook_id']==number and receipt['accepted_version']==1 and receipt['JSON_parsed'] is True
        assert summary['dispatches']==1 and summary['states'].count('DISPATCH_STARTED')==1
        event=json.loads((directory/'execution/events/0002-DISPATCH_STARTED.json').read_bytes())
        archives[attempt]=dict(Notebook_id=number,version=1,source_commit=event['source_commit'],dispatches=1,
            **json.loads((directory/'derived/ARCHIVE.json').read_bytes()))
    # Scan actual secret values in memory;never publish values,hashes or signed URLs.
    from u_re.v01.experiments.fastapi_pilot_01.auth_diagnose import inventory
    secrets=[s.encode() for s in inventory()[3] if len(s)>8]
    tasks={r['instance_id']:r for r in map(json.loads,(ROOT.parent/'official-inputs/tasks.jsonl').read_text(encoding='utf-8').splitlines())}
    frozen=json.loads((HERE/'EXPECTED_TASK_RECORDS.json').read_bytes())
    test_bodies=[tasks[i].get('test_patch','').encode() for i in frozen if tasks[i].get('test_patch')]
    checked=0
    def scan(raw):
        nonlocal checked
        checked+=1
        assert not any(s in raw for s in secrets),'Credential found;STOP publication'
        assert not any(t in raw for t in test_bodies),'Original evaluator test patch found;STOP publication'
        assert not re.search(rb'(?i)(?:X-Goog-Signature|X-Amz-Signature|access_token)=[A-Za-z0-9._%+-]{16,}',raw),'Signed URL found'
    for p in HERE.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts:continue
        raw=p.read_bytes();scan(raw)
        if p.name=='study.ipynb':
            nb=json.loads(raw);tree=ast.parse(nb['cells'][0]['source'])
            assign=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='payload' for v in n.targets))
            payload=base64.b64decode(ast.literal_eval(assign.value.args[0]))
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                assert z.testzip() is None
                for name in z.namelist():
                    assert not any(t in name for t in ('tasks.jsonl','evaluator_test_text','phase2.junit.xml','gold.patch','reference.patch'))
                    scan(z.read(name))
    files={p.relative_to(HERE).as_posix():dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes()))
        for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='INTEGRITY_MANIFEST.json'}
    value=dict(base_commit=BASE,history_files_checked=len(history),historical_content_changes=[],existing_CRLF_checkout_only=newline_only,
        candidates=candidates,archives=archives,files=files,publication_scan=dict(checked=checked,known_credentials_found=0,signed_URLs_found=0,full_competition_test_patches_found=0),
        raw_evidence='Private evidence outside Git;only owned synthetic/native toy and safe real-task identities/counts are published',
        actual_GPU=0,actual_real_Gemma=0,actual_formal_submissions=0,CPU_Notebooks=4,real_SWE_native_baselines=4)
    (HERE/'INTEGRITY_MANIFEST.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(dict(history_checked=len(history),new_files=len(files),scanned=checked,candidates='UNCHANGED',CPU_Notebooks=4,real_baselines=4)))


if __name__=='__main__':run()
