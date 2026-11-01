"""Whitelist only this step's new preparation code and non-secret receipts."""
import hashlib,json,re
from pathlib import Path
D=Path(__file__).resolve().parent;O=D/'holdout-preparation';P=O/'publication'
files=[D/n for n in ('prepare_holdout_metadata.py','check_native_contract_cpu.py','finalize_holdout_preparation.py','verify_holdout_preparation.py','prepare_holdout_publication.py')]
files+=sorted(p for p in O.iterdir() if p.is_file() and p.suffix in {'.json','.md'})
entries=[];expected={}
for p in files:
    raw=p.read_bytes();s=raw.decode('utf8');assert not p.is_symlink()
    assert not re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|KGAT_[A-Za-z0-9]{25,}',s),p
    path='experiments/r2-budget-optimization/candidate-a-design/'+p.relative_to(D).as_posix()
    entries.append(dict(path=path,mode='100644',type='blob',content=s))
    expected[path]=dict(git_blob_sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
P.mkdir(exist_ok=True)
payload=json.dumps(entries,ensure_ascii=True,separators=(',',':'))
(P/'PUBLIC_ELEMENTS.json').write_text(payload,encoding='utf8')
(P/'PUBLIC_EXPECTED.json').write_text(json.dumps(expected,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(files=len(entries),payload_characters=len(payload),raw_bytes=sum(x['bytes'] for x in expected.values()),official_raw_dataset_excluded=True)))
