"""Only recovery changes; existing CPU archives and historical files are not rewritten."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parent;D=R.parent;ROOT=D.parents[1]
before=json.loads((R/'V02_BEFORE.json').read_bytes());entries=[];index={}
for p in sorted(D.rglob('*')):
 if not p.is_file() or '__pycache__' in p.parts or '.cpu-deps' in p.parts:continue
 rel=p.relative_to(D).as_posix()
 if rel.startswith('native-recovery/source/') or rel.startswith('native-recovery/compiler-work/packages/') or '.private.' in p.name:continue
 if p.name in ['PUBLICATION_DELTA_INDEX.json','PUBLICATION_META.json']:continue
 raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest()
 if rel in before and before[rel]==digest:continue
 assert not p.is_symlink()
 text=raw.decode('utf8')
 assert not re.search(r'\b(?:hf_[A-Za-z0-9]{24,}|sk-[A-Za-z0-9]{24,}|AKIA[A-Z0-9]{16})\b',text)
 path=p.relative_to(ROOT).as_posix();entries.append(dict(path=path,mode='100644',type='blob',content=text));index[path]=dict(sha256=digest,bytes=len(raw))
(R/'PUBLICATION_DELTA_INDEX.json').write_text(json.dumps(index,indent=2))
entries.append(dict(path=(R/'PUBLICATION_DELTA_INDEX.json').relative_to(ROOT).as_posix(),mode='100644',type='blob',content=(R/'PUBLICATION_DELTA_INDEX.json').read_text()))
raw=json.dumps(entries,ensure_ascii=True);(R/'PUBLICATION_PAYLOAD.private.json').write_text(raw,encoding='utf8')
meta=dict(files=len(entries),characters=len(raw),chunks=(len(raw)+23999)//24000,excluded='Audit-only third-party source, duplicate compiler packages, caches, private payload; original artifacts unchanged')
(R/'PUBLICATION_META.json').write_text(json.dumps(meta));print(json.dumps(meta))
