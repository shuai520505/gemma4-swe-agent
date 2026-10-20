"""Immutable CPU/environment collection, CRC and all manifest SHA checks."""
import json
from pathlib import Path
import sys
import zipfile
from experiments.prepare import write_new
from s1.collect import verify_zip

HERE=Path(__file__).resolve().parent


def collect(revision):
    download=HERE/'_local'/(revision+'-download')
    archives=list((download/'s2_t500_early_v01'/revision).glob('*.zip'))
    assert len(archives)==1,archives
    raw=archives[0].read_bytes();proof=verify_zip(raw)
    target=HERE/'results'/revision;write_new(target/'raw.zip',raw)
    with zipfile.ZipFile(archives[0]) as z:
        for n in z.namelist():
            if n.endswith('/') or n.startswith('source/') or 'snapshot_source' in Path(n).parts or '.git' in Path(n).parts:continue
            write_new(target/n,z.read(n))
    for p in download.glob('*.log'):write_new(target/p.name,p.read_bytes())
    write_new(target/'collection.json',(json.dumps(proof,indent=2)+'\n').encode())
    print(json.dumps(proof,indent=2))


if __name__=='__main__':collect(sys.argv[1])
