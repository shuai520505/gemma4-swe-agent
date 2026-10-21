"""Read existing accepted CPU02 version only; no restart, save or retry."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import PurePosixPath
from urllib.parse import urlsplit

import requests
from .prepare import HERE,write
from .dispatch import Journal,SLUG


def collect():
    events=[json.loads(p.read_bytes()) for p in sorted((HERE/'execution/events').glob('*.json'))]
    accepted=[e for e in events if e['state']=='ACCEPTED_CONFIRMED']
    assert len(accepted)==1 and accepted[0]['accepted_version']==1,'No accepted existing version; no output queries'
    assert not (HERE/'collected').exists(),'Preserve existing output;never overwrite or retry'
    spec=json.loads((HERE/'BUILD_FREEZE.json').read_bytes());log=[];urls=set();original=requests.Session.send
    def send(session,request,**kw):
        u=urlsplit(request.url);op=u.path.rsplit('/',1)[-1]
        allowed=request.method=='POST' and u.hostname=='api.kaggle.com' and op in {'GetKernel','GetKernelSessionStatus','ListKernelSessionOutput'}
        download=request.method=='GET' and request.url in urls
        assert allowed or download,'Non-read-only or unregistered output request refused'
        assert len(log)<14,'Read-only collection bound reached'
        kw.update(timeout=60,allow_redirects=False)
        r=original(session,request,**kw)
        log.append(dict(at_utc=datetime.now(timezone.utc).isoformat(),operation='download existing output' if download else op,http_status=r.status_code))
        return r
    requests.Session.send=send
    try:
        from kagglesdk.kaggle_env import get_access_token_from_env
        from kagglesdk.kaggle_client import KaggleClient
        from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiGetKernelSessionStatusRequest,ApiListKernelSessionOutputRequest
        token,_=get_access_token_from_env();assert token
        with KaggleClient(api_token=token,verbose=False) as client:
            def identity():
                q=ApiGetKernelRequest();q.user_name=SLUG.split('/')[0];q.kernel_slug=SLUG.split('/')[1]
                value=client.kernels.kernels_api_client.get_kernel(q)
                assert value.metadata.ref==SLUG and value.metadata.current_version_number==1
                assert hashlib.sha256(value.blob.source.encode()).hexdigest()==spec['wire_sha256']
            identity()
            q=ApiGetKernelSessionStatusRequest();q.user_name=SLUG.split('/')[0];q.kernel_slug=SLUG.split('/')[1]
            status=client.kernels.kernels_api_client.get_kernel_session_status(q)
            assert status.status.name in ('COMPLETE','ERROR'),'No output collection before terminal status'
            files=[];token_page=None;raw_log=None
            for page in range(3):
                q=ApiListKernelSessionOutputRequest();q.user_name=SLUG.split('/')[0];q.kernel_slug=SLUG.split('/')[1];q.page_size=100
                if token_page:q.page_token=token_page
                result=client.kernels.kernels_api_client.list_kernel_session_output(q)
                files.extend(result.files or []);raw_log=raw_log or result.log;token_page=result.next_page_token
                if not token_page:break
            assert not token_page and len(files)<=8,'Output scope cap;stop rather than partial completeness claim'
            identity()  # The installed CLI ignores version suffix for output; pin latest1 before/after listing.
            target=HERE/'collected';target.mkdir(exist_ok=False);records=[]
            for item in files:
                name=PurePosixPath(item.file_name)
                assert not name.is_absolute() and '..' not in name.parts
                assert item.file_name.endswith(('.zip','.log','.json','.xml')),'Unexpected output file'
                urls.add(item.url)
                r=requests.get(item.url,stream=True);r.raise_for_status()
                path=target/item.file_name;path.parent.mkdir(parents=True,exist_ok=True)
                h=hashlib.sha256();size=0
                with path.open('xb') as out:
                    for b in r.iter_content(1024*1024):
                        size+=len(b);assert size<=200*1024*1024;h.update(b);out.write(b)
                records.append(dict(file=item.file_name,sha256=h.hexdigest(),bytes=size))
            if raw_log:
                # Future evidence remains evaluator-side; no Agent ever receives it.
                raw=raw_log.encode();(target/'notebook.log').write_bytes(raw)
                records.append(dict(file='notebook.log',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
            identity()
            write(target/'OUTPUT_MANIFEST.json',dict(accepted_version=1,status=status.status.name,files=records,HTTP=log,
                task_admission_audited=False,note='Raw collection only;validate internal archives,TaskResult/JUnit/input identities/cleanup offline before promotion'))
            Journal(HERE/'execution').append('OUTPUT_COLLECTED',version=1,task_admission_audited=False)
    finally:requests.Session.send=original


if __name__=='__main__':collect()
