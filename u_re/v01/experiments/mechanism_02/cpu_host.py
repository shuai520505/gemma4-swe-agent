"""CPU-only one-save launch. Checked operations stay in one Python process."""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import requests
from u_re.v01.build import sha

HERE=Path(__file__).resolve().parent


def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,indent=2,default=str)


def launch():
    from kaggle import api
    folder=HERE/'notebooks/cpu01';meta=json.loads((folder/'kernel-metadata.json').read_text())
    freeze=json.loads((HERE/'registrations/cpu01_build.json').read_text());out=HERE/'results/cpu01'
    assert meta['enable_gpu'] is False and meta['enable_tpu'] is False and meta['model_sources']==[]
    assert freeze['GPU'] is False
    assert sha((folder/'study.ipynb').read_bytes())==freeze['notebook_sha256']
    assert sha((folder/'kernel-metadata.json').read_bytes())==freeze['metadata_sha256']
    # Unlike an ambiguous get-by-new-slug response, owner listing can be checked
    # in the SAME process before a save. No chained shell fallthrough.
    rows=api.kernels_list(mine=True,search=meta['id'].split('/')[1],page_size=100)
    listing=[r.to_dict(ignore_defaults=False) for r in rows]
    save(out/'PREEXISTENCE.json',dict(queried_at_utc=datetime.now(timezone.utc).isoformat(),response=listing))
    assert not listing,'Existing/ambiguous Notebook match: inspect rather than duplicate'
    save(out/'SAVE_INTENT.json',dict(created_at_utc=datetime.now(timezone.utc).isoformat(),freeze=freeze,GPU=False))
    original=requests.Session.send;sent=0
    def send(self,request,**kwargs):
        nonlocal sent
        kwargs.setdefault('timeout',60)
        if not request.url.rstrip('/').endswith('/SaveKernel'):return original(self,request,**kwargs)
        sent+=1;assert sent==1,'Never automatically retry uncertain save'
        body=json.loads(request.body)
        assert body.get('enableGpu') is False and not body.get('enableTpu')
        assert not body.get('modelSources')
        save(out/'SAVE_REQUEST.json',dict(sent_at_utc=datetime.now(timezone.utc).isoformat(),
             metadata={k:v for k,v in body.items() if k not in ('text','blob','source')},
             notebook_text_sha256=sha(body['text'].encode()) if isinstance(body.get('text'),str) else None))
        response=original(self,request,**kwargs)
        save(out/'SAVE_RESPONSE.json',dict(received_at_utc=datetime.now(timezone.utc).isoformat(),http_status=response.status_code,response=response.json()))
        return response
    requests.Session.send=send
    reply=api.kernels_push(str(folder),timeout='7200',acc=None)
    result=reply.to_dict(ignore_defaults=False);save(out/'SAVE_SDK_RESPONSE.json',result)
    print(json.dumps(result,indent=2));assert result.get('versionNumber')==1,'No duplicate version permitted'


def main():
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='observe':
        from u_re.v01 import observe_cpu
        observe_cpu.HERE=HERE;observe_cpu.observe('cpu01',False)
    else:raise ValueError(sys.argv[1])


if __name__=='__main__':main()
