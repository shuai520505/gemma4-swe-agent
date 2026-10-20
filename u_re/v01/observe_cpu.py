"""One bounded read-only snapshot. Output collection only after terminal status."""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
from kaggle import api
from .build import HERE


def observe(revision,collect=False):
    meta=json.loads((HERE/'notebooks'/revision/'kernel-metadata.json').read_text())
    assert meta['enable_gpu'] is False
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out=HERE/'results'/revision/'observations'/stamp;out.mkdir(parents=True,exist_ok=False)
    status=api.kernels_status(meta['id']).to_dict(ignore_defaults=False)
    (out/'status.json').write_text(json.dumps(status,indent=2,default=str)+'\n')
    print(json.dumps(dict(queried_at_utc=stamp,response=status),indent=2,default=str))
    if collect:
        assert status['status'] in ('COMPLETE','ERROR'),'Do not infer final artifacts from a running version'
        dest=HERE/'results'/revision/'download';dest.mkdir(parents=True,exist_ok=True)
        assert not list(dest.iterdir()),'Preserve original download; never overwrite'
        result=api.kernels_output(meta['id'],path=str(dest),file_pattern=r'.*\.zip$',force=False,quiet=True)
        (out/'download_response.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
        print('DOWNLOADED',dest)


if __name__=='__main__':
    observe(sys.argv[1],len(sys.argv)>2 and sys.argv[2]=='collect')
