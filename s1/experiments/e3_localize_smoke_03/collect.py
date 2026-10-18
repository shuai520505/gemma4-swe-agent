import json
from pathlib import Path
import zipfile
from experiments.prepare import write_new
from s1.collect import verify_zip
from s1.util import save


def main(kind):
    here=Path(__file__).resolve().parent;download=here/'_local'/(kind+'-download')
    archives=list((download/'s1_e3_localize_smoke_03'/kind).glob('*.zip'))
    assert len(archives)==1,archives
    path=archives[0];audit=verify_zip(path.read_bytes())
    output=here/'results'/kind;extract=here/'_local'/(kind+'-extract')
    write_new(output/'raw.zip',path.read_bytes())
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.endswith('/'):continue
            write_new(extract/name,z.read(name))
            if name.startswith('source/') or name=='installation.log':continue
            write_new(output/name,z.read(name))
    for log in download.glob('*.log'):write_new(output/log.name,log.read_bytes())
    save(output/'collection.json',audit);print(json.dumps(audit,indent=2))


if __name__=='__main__':
    import sys
    main(sys.argv[1])
