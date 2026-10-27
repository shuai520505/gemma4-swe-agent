"""Read-only range recovery after CLI buffered download lost an incomplete body.

Uses the same official Kaggle output-list API as the installed CLI. Signed URLs
and authentication headers are never printed or written into public records.
This utility cannot dispatch, modify or submit a Notebook.
"""
import json
import os
from pathlib import Path
import re

import requests

from .prepare import PRIVATE, REF, sha, write


def run():
    os.environ.update(HTTPS_PROXY='http://127.0.0.1:7890',PYTHONIOENCODING='utf-8')
    from kaggle.api.kaggle_api_extended import KaggleApi
    from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest
    api=KaggleApi();api.authenticate()
    owner,slug=REF.split('/')
    name='egrd-v0311-cpu-v1.zip'
    found=None;token=None
    with api.build_kaggle_client() as client:
        for _ in range(20):
            request=ApiListKernelSessionOutputRequest()
            request.user_name=owner;request.kernel_slug=slug;request.page_size=200
            if token:request.page_token=token
            response=client.kernels.kernels_api_client.list_kernel_session_output(request)
            found=next((f for f in response.files or [] if f.file_name==name),None)
            if found:break
            token=response.next_page_token
            if not token:break
    assert found is not None,'Exact archive not listed; never retry execution'
    folder=PRIVATE/'range-download';folder.mkdir(exist_ok=True)
    log=[];parts=[];start=0;total=None;chunk=2*1024*1024
    while total is None or start<total:
        end=start+chunk-1 if total is None else min(start+chunk-1,total-1)
        for attempt in range(1,4):
            try:
                with requests.get(found.url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'},
                                  stream=True,timeout=(15,45)) as response:
                    assert response.status_code==206,'Output storage must honor bounded byte ranges'
                    match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',response.headers['Content-Range'])
                    assert match is not None
                    lo,hi,size=map(int,match.groups())
                    assert lo==start and hi==min(end,size-1)
                    assert total is None or total==size
                    body=b''.join(response.iter_content(65536))
                    assert len(body)==hi-lo+1
                total=size
                part=folder/f'{lo:010d}-{hi:010d}.part'
                if part.exists():assert part.read_bytes()==body
                else:part.write_bytes(body)
                log.append(dict(start=lo,end=hi,total=size,attempt=attempt,sha256=sha(body),status='PASS'))
                parts.append(part);start=hi+1
                write(folder/'READ_ONLY_DOWNLOAD_RECORD.json',dict(parts=log,complete=False))
                print('Verified archive bytes',start,'/',total,flush=True)
                break
            except Exception as exc:
                log.append(dict(start=start,end=end,attempt=attempt,status='READ_ERROR',error_type=type(exc).__name__))
                write(folder/'READ_ONLY_DOWNLOAD_RECORD.json',dict(parts=log,complete=False))
                if attempt==3:raise RuntimeError('Read-only range recovery failed; private record retained') from None
    final=folder/name
    with final.open('xb') as stream:
        for part in parts:stream.write(part.read_bytes())
    assert final.stat().st_size==total
    write(folder/'READ_ONLY_DOWNLOAD_RECORD.json',dict(parts=log,complete=True,bytes=total,archive_sha256=sha(final.read_bytes()),
          Notebook_dispatches=0,formal_submissions=0,URLs_retained=False))


if __name__=='__main__':run()
