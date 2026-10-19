"""Read-only collection with immutable writes and recursive ZIP/hash checks."""
import json
from pathlib import Path
import zipfile
from experiments.prepare import write_new
from s1.collect import verify_zip
from s1.util import save


def collect(revision):
    here=Path(__file__).resolve().parent
    download=here/'_local'/(revision+'-download')
    archives=list((download/'s1_egv_v01'/revision).glob('*.zip'))
    assert len(archives)==1,archives
    result=verify_zip(archives[0].read_bytes());out=here/'results'/revision
    write_new(out/'raw.zip',archives[0].read_bytes())
    with zipfile.ZipFile(archives[0]) as z:
        for name in z.namelist():
            if name.endswith('/'):continue
            write_new(here/'_local'/(revision+'-extract')/name,z.read(name))
            if not name.startswith('source/') and name!='installation.log':write_new(out/name,z.read(name))
    for log in download.glob('*.log'):write_new(out/log.name,log.read_bytes())
    save(out/'collection.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    import sys
    collect(sys.argv[1])
