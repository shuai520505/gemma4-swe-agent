"""Compare archived source Git object identities to authenticated upstream metadata."""
import hashlib,json,tarfile
from pathlib import Path
D=Path(__file__).resolve().parent
def obj(kind,b):return hashlib.sha1(kind+b' '+str(len(b)).encode()+b'\0'+b).digest()
def tree(entries):
    raw=b''
    for name,(mode,value) in sorted(entries.items(),key=lambda item:(item[0]+('/' if item[1][0]=='40000' else '')).encode()):
        h=tree(value) if mode=='40000' else value
        raw+=mode.encode()+b' '+name.encode()+b'\0'+h
    return obj(b'tree',raw)
rows=[]
for r in json.loads((D/'OFFICIAL_COMMIT_IDENTITIES.json').read_bytes()):
    p=D/'assets/snapshots'/(r['task']+'.tgz');root={}
    with tarfile.open(p,'r:gz') as tar:
        for m in tar.getmembers():
            names=Path(m.name).parts[1:]
            if not names or m.isdir():continue
            d=root
            for part in names[:-1]:d=d.setdefault(part,('40000',{}))[1]
            if m.issym():mode='120000';b=m.linkname.encode()
            elif m.isfile():mode='100755' if m.mode&0o111 else '100644';b=tar.extractfile(m).read()
            else:raise AssertionError(('Unsupported source archive type',m.name))
            d[names[-1]]=(mode,obj(b'blob',b))
    actual=tree(root).hex()
    rows.append(r|{'archive_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actual_archive_git_tree':actual,'exact_git_tree_match':actual==r['git_tree']})
(D/'SOURCE_TREE_VERIFICATION.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
