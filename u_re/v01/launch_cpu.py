"""Only explicit CPU builds can be saved. Never accepts a GPU accelerator."""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import requests
from .build import HERE,sha


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2,ensure_ascii=False,default=str)


def launch(revision):
    assert revision.startswith('cpu')
    folder=HERE/'notebooks'/revision
    freeze=json.loads((HERE/'registrations'/f'{revision}_build.json').read_text())
    meta=json.loads((folder/'kernel-metadata.json').read_text())
    assert meta['enable_gpu'] is False and meta['enable_tpu'] is False
    assert not meta.get('machine_shape') and freeze['GPU'] is False
    assert sha((folder/'study.ipynb').read_bytes())==freeze['notebook_sha256']
    assert sha((folder/'kernel-metadata.json').read_bytes())==freeze['metadata_sha256']
    output=HERE/'results'/revision;output.mkdir(parents=True,exist_ok=True)
    save(output/'SAVE_INTENT.json',dict(created_at_utc=now(),GPU=False,freeze=freeze))
    original=requests.Session.send;sent=0
    def send(self,request,**kwargs):
        nonlocal sent
        kwargs.setdefault('timeout',60)
        if not request.url.rstrip('/').endswith('/SaveKernel'):
            return original(self,request,**kwargs)
        sent+=1;assert sent==1,'Ambiguous save: query accepted version, never automatically repeat'
        body=json.loads(request.body)
        assert not body.get('enableGpu') and not body.get('enableTpu')
        assert 'Nvidia' not in str(body.get('machineShape',''))
        # Keep metadata and source digest, not an unnecessary second source copy.
        source=body.get('text') or body.get('blob') or body.get('source')
        save(output/'SAVE_REQUEST.json',dict(sent_at_utc=now(),keys=list(body),
            metadata={k:v for k,v in body.items() if k not in ('text','blob','source')},
            source_sha256=sha(source.encode()) if isinstance(source,str) else None,GPU=False))
        response=original(self,request,**kwargs)
        save(output/'SAVE_RESPONSE.json',dict(received_at_utc=now(),http_status=response.status_code,response=response.json()))
        return response
    requests.Session.send=send
    from kaggle import api
    response=api.kernels_push(str(folder),timeout='3600',acc=None)
    value=response.to_dict(ignore_defaults=False)
    save(output/'SAVE_SDK_RESPONSE.json',value)
    print(json.dumps(value,indent=2,default=str))


if __name__=='__main__':
    launch(sys.argv[1])
