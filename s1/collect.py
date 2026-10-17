"""Copy immutable Kaggle evidence, verify CRC and every declared file digest."""
import argparse
import io
import json
from pathlib import Path
import zipfile
from experiments.prepare import write_new
from .util import sha,sha_file,save

ROOT=Path(__file__).resolve().parents[1]


def verify_zip(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
        verified=0
        if 'evidence_manifest.json' in z.namelist():
            for n,info in json.loads(z.read('evidence_manifest.json')).items():
                b=z.read(n)
                assert sha(b)==info['sha256'] and len(b)==info['bytes'],n
                verified+=1
        nested=[]
        for n in z.namelist():
            if n.startswith('runs/') and n.endswith('.zip'):
                nested.append(dict(name=n,**verify_zip(z.read(n))))
        return dict(sha256=sha(raw),bytes=len(raw),CRC=True,manifest_files=verified,nested=nested)


def collect(path,label,kernel):
    path=Path(path);raw=path.read_bytes();audit=verify_zip(raw)
    output=ROOT/'s1/results'/label
    write_new(output/'raw.zip',raw)
    extraction=ROOT/'s1/_local'/label
    extraction.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for n in z.namelist():
            if n.endswith('/'):continue
            write_new(extraction/n,z.read(n))
            if n.startswith('source/') or n=='installation.log':continue
            # Full raw zip includes source/install log; expose run evidence
            # separately for convenient inspection, unchanged bytes.
            write_new(output/n,z.read(n))
    save(output/'collection.json',dict(kernel=kernel,source_archive=path.name,**audit,
        local_extract=str(extraction),raw_copy_identical=True,interpretation='CPU mock or public development, never an official leaderboard score'))
    return dict(output=str(output),extraction=str(extraction),**audit)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('zip');p.add_argument('label');p.add_argument('kernel')
    a=p.parse_args();print(json.dumps(collect(a.zip,a.label,a.kernel),indent=2))
