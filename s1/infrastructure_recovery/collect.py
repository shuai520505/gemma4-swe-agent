"""Read-only collection into new revision directories, CRC and SHA checked."""
import json
from pathlib import Path
import sys
import zipfile
from experiments.prepare import write_new
from s1.collect import verify_zip
from s1.util import save


def main(revision):
    here=Path(__file__).resolve().parent
    download=here/'_local'/(revision+'-download')
    archives=list((download/'s1_infra_recovery'/revision).glob('*.zip'))
    assert len(archives)==1,archives
    path=archives[0];raw=path.read_bytes();audit=verify_zip(raw)
    output=here/'results'/revision;extract=here/'_local'/(revision+'-extract')
    write_new(output/'raw.zip',raw)
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.endswith('/'):continue
            write_new(extract/name,z.read(name))
            if name.startswith('source/') or name=='installation.log':continue
            write_new(output/name,z.read(name))
    for log in download.glob('*.log'):write_new(output/log.name,log.read_bytes())
    save(output/'collection.json',dict(kernel='wudangdexiaodoashi/gemma4-s1-infra-'+revision+'-cpu',**audit))
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main(sys.argv[1])
