"""Pinned official repository snapshots and public distribution runtime wheels."""
import concurrent.futures,hashlib,io,json,os,socket,subprocess,sys,tarfile,zipfile
from pathlib import Path
import requests
OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def snapshot(row):
    dest=OUT/'assets'/'snapshots'/(row['instance_id']+'.tgz');dest.parent.mkdir(parents=True,exist_ok=True)
    url=f"https://codeload.github.com/{row['repo']}/tar.gz/{row['base_commit']}"
    if not dest.exists():
        r=requests.get(url,timeout=120);r.raise_for_status();dest.write_bytes(r.content)
    raw=dest.read_bytes()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:
        members=t.getmembers();root=Path(members[0].name).parts[0]
        assert root.endswith(row['base_commit'])
        assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members)
    return dict(instance_id=row['instance_id'],url=url,archive_root=root,bytes=len(raw),sha256=sha(raw),base_commit=row['base_commit'])
def main():
    try:
        with socket.create_connection(('127.0.0.1',7890),timeout=1):os.environ['HTTPS_PROXY']='http://127.0.0.1:7890'
    except OSError:pass
    rows=json.loads((OUT/'TASK_IDENTITY_LOCK.json').read_bytes())['rows']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:result=list(pool.map(snapshot,rows))
    (OUT/'SOURCE_ACQUISITION.json').write_text(json.dumps(result,indent=2)+'\n')
    wheels=OUT/'assets'/'wheels';wheels.mkdir(parents=True,exist_ok=True)
    required=['numpy==1.26.4','pandas==2.2.3','scipy==1.14.1','hypothesis==6.131.9','mpmath==1.3.0','pytest==8.4.2','pytest-xdist==3.6.1','pytest-timeout==2.3.1','setuptools==75.8.0','setuptools-scm==8.1.0','wheel==0.45.1','packaging==26.1','pip==24.1.2','pylint==3.0.0','Sphinx==7.2.6','dask==2024.6.2','zarr==2.18.3','numcodecs==0.12.1']
    command=[sys.executable,'-m','pip','--isolated','download','--index-url','https://pypi.org/simple','--only-binary=:all:','--platform','manylinux2014_x86_64','--python-version','312','--implementation','cp','--abi','cp312','-d',str(wheels)]+required
    with (OUT/'ASSET_DOWNLOAD.log').open('w',encoding='utf8') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900)
    # Runtime closure only. The four task libraries must come from their locked source snapshots.
    for p in list(wheels.glob('*.whl')):
        if p.name.split('-')[0].lower() in {'pylint','sphinx','sympy','xarray'}:p.unlink()
    manifest={p.relative_to(OUT/'assets').as_posix():sha(p.read_bytes()) for p in (OUT/'assets').rglob('*') if p.is_file()}
    (OUT/'ASSET_MANIFEST.json').write_text(json.dumps(dict(files=manifest,sources=result,required_distributions=required,source_packages_excluded=['pylint','sphinx','sympy','xarray']),indent=2)+'\n')
    print(json.dumps(dict(snapshots=len(result),wheels=len(list(wheels.glob('*.whl'))),bytes=sum(p.stat().st_size for p in (OUT/'assets').rglob('*') if p.is_file()))))
if __name__=='__main__':main()
