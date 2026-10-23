"""Hash-only alias checks. Never inspect reference patches or execute input code."""
import json,tarfile
from pathlib import Path,PurePosixPath
from .common import sha

def tree_digest(path):
    with tarfile.open(path,'r:*') as archive:
        members=archive.getmembers();names=[PurePosixPath(m.name).parts for m in members if m.name not in ('.','./')]
        roots={p[0] for p in names if p};strip=len(roots)==1 and all(len(p)>1 or m.isdir() for p,m in zip(names,[m for m in members if m.name not in ('.','./')]))
        rows=[]
        for item in members:
            parts=PurePosixPath(item.name).parts
            if strip:parts=parts[1:]
            if not parts or '.git' in parts or item.isdir():continue
            assert '..' not in parts and not item.name.startswith('/'),'Unsafe snapshot member'
            name='/'.join(parts)
            if item.isfile():
                stream=archive.extractfile(item);digest=sha(stream.read())
            else:
                assert item.issym() or item.islnk(),'Unsupported snapshot member type'
                digest=sha(item.linkname.encode())
            rows.append((name,item.type.decode('ascii'),item.mode&0o111,digest))
        assert rows,'No source content'
        return sha(json.dumps(sorted(rows),separators=(',',':')).encode())

def overlay_content_digest(text):
    # Ignore diff offsets/context but retain affected paths and all changed
    # lines. Identical content under another issue is a conservative conflict.
    rows=[s for s in text.splitlines() if s.startswith(('diff --git ','+++ ','--- ')) or (s.startswith(('+','-')) and not s.startswith(('+++','---')))]
    return sha('\n'.join(rows).encode()) if rows else None

def conflicts(identities,candidate_ids):
    rows=[];keys=('issue_sha256','base_commit','snapshot_tree_sha256','test_overlay_content_sha256')
    for ident in candidate_ids:
        a=identities[ident]
        for other,b in identities.items():
            if ident==other or a['repo']!=b['repo']:continue
            shared=[key for key in keys if a.get(key) and a.get(key)==b.get(key)]
            left={h for n,h in a['input_files'].items() if n.endswith(('.tgz','.tar.gz'))}
            right={h for n,h in b['input_files'].items() if n.endswith(('.tgz','.tar.gz'))}
            if left & right:shared.append('snapshot_bytes_sha256')
            if shared:rows.append(dict(instance_id=ident,other=other,shared=shared))
    return rows
