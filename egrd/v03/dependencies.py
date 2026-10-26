"""Freeze minimal CPU wheel inputs from PyPI, preserving wheel license files."""
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import requests
from packaging.utils import parse_wheel_filename
from concurrent.futures import ThreadPoolExecutor

from .cli import PRIVATE,HERE,sha,write

PINS={
 'asgiref':'3.8.1','sqlparse':'0.5.3','setuptools':'75.8.0',
 'numpy':'1.26.4','pandas':'2.2.3','python-dateutil':'2.9.0.post0',
 'pytz':'2025.2','tzdata':'2025.2','six':'1.17.0','packaging':'24.2',
 'starlette':'0.48.0','pydantic':'2.11.7','pydantic-core':'2.33.2',
 'annotated-types':'0.7.0','typing-extensions':'4.14.1','typing-inspection':'0.4.1',
 'python-multipart':'0.0.20','httpx':'0.28.1','httpcore':'1.0.9',
 'anyio':'4.9.0','idna':'3.10','sniffio':'1.3.1','certifi':'2025.8.3','h11':'0.16.0','annotated-doc':'0.0.2',
}
GROUPS={
 'django':['asgiref','sqlparse','setuptools'],
 'xarray':['numpy','pandas','python-dateutil','pytz','tzdata','six','packaging','setuptools'],
 'fastapi':['starlette','pydantic','pydantic-core','annotated-types','typing-extensions',
    'typing-inspection','python-multipart','httpx','httpcore','anyio','idna','sniffio','certifi','h11','annotated-doc'],
}


def freeze():
    directory=PRIVATE/'dependencies';directory.mkdir(parents=True,exist_ok=True)
    wheels=directory/'wheels';wheels.mkdir(exist_ok=True)
    requirements=directory/'download.txt'
    requirements.write_text(''.join(f'{n}=={v}\n' for n,v in sorted(PINS.items())),encoding='utf8')
    def fetch(item):
        name,version=item
        url=f'https://pypi.org/pypi/{name}/{version}/json'
        response=requests.get(url,proxies={'https':'http://127.0.0.1:7890'},timeout=60)
        response.raise_for_status();(directory/(str(name)+'.json')).write_bytes(response.content)
        metadata=response.json();choices=[]
        for entry in metadata['urls']:
            if not entry['filename'].endswith('.whl'):continue
            tags=parse_wheel_filename(entry['filename'])[3]
            if any(t.interpreter in ('py3','cp312') and t.abi in ('none','cp312','abi3') and
                t.platform in ('any','manylinux_2_17_x86_64','manylinux2014_x86_64') for t in tags):
                choices.append(entry)
        assert choices,(name,'No CPython312/Linux-compatible wheel')
        published=sorted(choices,key=lambda r:r['filename'])[0]
        assert published['url'].startswith('https://files.pythonhosted.org/')
        wheel=wheels/published['filename']
        if not wheel.exists():
            result=requests.get(published['url'],proxies={'https':'http://127.0.0.1:7890'},timeout=120)
            result.raise_for_status();wheel.write_bytes(result.content)
        digest=sha(wheel.read_bytes());assert digest==published['digests']['sha256']
        with zipfile.ZipFile(wheel) as archive:
            assert archive.testzip() is None
            licenses={n:sha(archive.read(n)) for n in archive.namelist()
                if '.dist-info/' in n and any(v in n.lower() for v in ('license','copying','notice'))}
        supplemental=None
        if not licenses and name=='annotated-doc':
            assert metadata['info']['project_urls']['Repository']=='https://github.com/fastapi/annotated-doc'
            license_url=f'https://raw.githubusercontent.com/fastapi/annotated-doc/{version}/LICENSE'
            text=requests.get(license_url,proxies={'https':'http://127.0.0.1:7890'},timeout=60)
            text.raise_for_status();assert b'The MIT License' in text.content
            location=directory/'supplemental-licenses'/f'{name}-{version}-LICENSE'
            location.parent.mkdir(exist_ok=True);location.write_bytes(text.content)
            supplemental=dict(source_url=license_url,sha256=sha(text.content),file=location.name,
                reason='Original wheel omits license file; publisher release-tag license retained separately without changing wheel')
        assert licenses or supplemental,(name,'No verified license found')
        return str(name),dict(version=str(version),filename=wheel.name,sha256=digest,bytes=wheel.stat().st_size,
            source_url=published['url'],pypi_metadata_url=url,license_expression=metadata['info'].get('license_expression'),
            license_metadata_sha256=sha(str(metadata['info'].get('license')).encode()),license_files=licenses,supplemental_license=supplemental,
            redistribution='Unmodified whole wheel includes original license/notice files; private input only')
    with ThreadPoolExecutor(max_workers=4) as executor:records=dict(executor.map(fetch,sorted(PINS.items())))
    assert set(records)==set(PINS)
    write(HERE/'DEPENDENCY_LOCK.json',dict(platform='CPython 3.12 Linux x86_64',sources=['pypi.org','files.pythonhosted.org'],
        packages=records,groups=GROUPS,network_at_runtime=False))
    print('Frozen',len(records),'CPU wheels with publisher SHA and retained license files.')


if __name__=='__main__':freeze()
