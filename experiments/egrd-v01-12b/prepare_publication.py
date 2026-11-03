"""Explicit research publication allowlist; excludes credentials and private API replies."""
import base64,hashlib,json,re,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent;prefix='experiments/egrd-v01-12b/'
names=[p.relative_to(D).as_posix() for p in D.iterdir() if p.is_file() and p.suffix in ['.py','.md','.json'] and '.local.' not in p.name]
for folder in ['configs','inputs','packages','pilot-frozen','pilot-evidence']:
 names += [p.relative_to(D).as_posix() for p in (D/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
names += [p.relative_to(D).as_posix() for p in (D/'evidence').iterdir() if p.suffix in ['.json','.md','.log'] and p.name not in ['JOBS_BEFORE_DISPATCH.json']]
names += ['cpu-notebook/kernel-metadata.json','gpu-notebook/kernel-metadata.json','gpu-notebook/BUILD.json','gpu-notebook/GPU_AUTHORIZATION.json','gpu-notebook/QUOTA_IMMEDIATELY_BEFORE_DISPATCH.json','gpu-output/PLATFORM.json','gpu-output/QUOTA_AFTER.json']
names += ['gpu-notebook/dispatch/'+n for n in ['ONE_SHOT_CLAIM.json','REQUEST_SENT.json','HTTP.json','DISPATCH_RECORD.json']]
for i in [3,6]:
 folder=f'cpu-attempt-{i:02d}'
 names += [folder+'/PLATFORM.json',folder+'/egrd-v01-12b-cpu01.zip']
text=[];binary=[]
for n in sorted(set(names)):
 assert '.private.' not in n and '..' not in Path(n).parts
 b=(D/n).read_bytes()
 if n.endswith('.zip'):
  with zipfile.ZipFile(D/n) as z:assert z.testzip() is None
  binary.append(dict(path=prefix+n,base64=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest()));continue
 s=b.decode('utf8');assert not re.search(r'KGAT_[A-Za-z0-9_-]{12,}|hf_[A-Za-z0-9]{24,}',s)
 text.append(dict(path=prefix+n,mode='100644',type='blob',content=s))
payload=json.dumps(dict(text=text,binary=binary),ensure_ascii=True)
(D/'PUBLICATION_PAYLOAD.local.json').write_text(payload,encoding='utf8')
print(json.dumps(dict(text_files=len(text),binary_files=len(binary),chars=len(payload))))
