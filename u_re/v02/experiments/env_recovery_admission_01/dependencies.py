"""Fetch only fixed public PyPI wheels, verify hashes, never install locally."""
import hashlib,json,zipfile,io,email
from pathlib import Path
from urllib.parse import urlsplit
import requests

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
ID='U-RE-V02B-ENV-RECOVERY-ADMISSION'
ARTIFACTS=ROOT.parent/'private-evidence/u_re_v02b_dependencies/wheels'
VERSIONS={'inline-snapshot':'0.21.1','asttokens':'3.0.0','executing':'2.2.0'}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')

def fetch():
    assert not (HERE/'NEW_DEPENDENCIES.json').exists(),'Do not overwrite a frozen artifact manifest'
    ARTIFACTS.mkdir(parents=True,exist_ok=True);rows=[]
    for name,version in VERSIONS.items():
        source=f'https://pypi.org/pypi/{name}/{version}/json'
        response=requests.get(source,timeout=45);response.raise_for_status();meta=response.json()
        wheel=next(f for f in meta['urls'] if f['filename'].endswith('.whl') and not f['yanked'])
        assert urlsplit(wheel['url']).hostname=='files.pythonhosted.org' and urlsplit(wheel['url']).scheme=='https'
        path=ARTIFACTS/wheel['filename']
        raw=path.read_bytes() if path.exists() else requests.get(wheel['url'],timeout=60).content
        assert sha(raw)==wheel['digests']['sha256']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None and all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
            metadata=email.message_from_bytes(z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))))
            tags=z.read(next(n for n in z.namelist() if n.endswith('.dist-info/WHEEL'))).decode()
            assert 'none-any' in tags and metadata['Version']==version
            licenses=[n for n in z.namelist() if 'LICENSE' in n.upper() or 'NOTICE' in n.upper()]
            assert licenses,'Keep upstream redistribution license in wheel'
        if not path.exists():path.write_bytes(raw)
        rows.append(dict(name=name,version=version,filename=wheel['filename'],sha256=sha(raw),bytes=len(raw),source=source,artifact_url=wheel['url'],metadata_sha256=sha(response.content),Requires_Python=metadata['Requires-Python'],Requires_Dist=metadata.get_all('Requires-Dist',[]),wheel_tags=tags.splitlines(),licenses=licenses,license=metadata['License-Expression'] or metadata['License'] or metadata.get_all('Classifier',[]),source_verified=True,installed_local=False,approval='Current V02b human instruction explicitly permits verified fixed-version dependency retrieval and CPU installation; research native evaluation only'))
    write(HERE/'NEW_DEPENDENCIES.json',dict(status='VERIFIED_ARTIFACTS_NOT_YET_INSTALLED',packages=rows,environment='CPython3.12 Linux; mandatory dependencies only; existing pytest/rich closure must be checked in actual Notebook before use',rules_source='https://www.kaggle.com/competitions/gemma-4-developer-agent/rules',scope='Private CPU research environment. Does not establish permission/availability in official competition scoring. No Verifier/test/source modification.'))
    print(json.dumps([(r['name'],r['version'],r['sha256']) for r in rows]))

if __name__=='__main__':fetch()
