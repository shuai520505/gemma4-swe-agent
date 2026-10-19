"""Preserve every CPU preparation, including failures, without overwrite."""
from pathlib import Path
import json
import zipfile
from experiments.prepare import write_new
from s1.collect import verify_zip


def main(revision):
    here=Path(__file__).resolve().parent
    download=here/'_local'/(revision+'-download')
    archives=list((download/'s2_egv_agenttool_v01'/revision).glob('*.zip'))
    assert len(archives)==1,archives
    raw=archives[0].read_bytes();proof=verify_zip(raw)
    out=here/'results'/revision;write_new(out/'raw.zip',raw)
    with zipfile.ZipFile(archives[0]) as z:
        for n in z.namelist():
            if n.endswith('/'):continue
            assert not n.startswith('/') and '..' not in Path(n).parts
            write_new(here/'_local'/(revision+'-extract')/n,z.read(n))
            if not n.startswith('source/') and '/original115/' not in n and n!='installation.log':
                write_new(out/n,z.read(n))
    for log in download.glob('*.log'):write_new(out/log.name,log.read_bytes())
    write_new(out/'collection.json',(json.dumps(proof,indent=2)+'\n').encode())
    print(json.dumps(proof,indent=2))


if __name__=='__main__':
    import sys
    main(sys.argv[1])
