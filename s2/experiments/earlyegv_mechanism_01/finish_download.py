"""Finish missing immutable output ranges concurrently; no compute execution."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

from .recover_download import HERE, FILE, SLUG, api, ApiListKernelSessionOutputRequest


if __name__ == '__main__':
    size=42305958;step=1024*1024
    request=ApiListKernelSessionOutputRequest();request.user_name='wudangdexiaodoashi';request.kernel_slug=SLUG;request.page_size=100
    with api.build_kaggle_client() as k:listing=k.kernels.kernels_api_client.list_kernel_session_output(request)
    item=next(f for f in listing.files if f.file_name==FILE)
    pieces=HERE/'download/range-parts'
    def receive(start):
        end=min(size,start+step)-1
        path=pieces/f'{start:010d}-{end:010d}.part'
        if path.exists():
            assert path.stat().st_size==end-start+1
            return dict(start=start,end=end,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),reused=True)
        response=requests.get(item.url,headers={'Range':f'bytes={start}-{end}'},timeout=(15,60))
        response.raise_for_status();assert response.status_code==206
        assert response.headers['Content-Range']==f'bytes {start}-{end}/{size}'
        raw=response.content;assert len(raw)==end-start+1
        with path.open('xb') as file:file.write(raw)
        return dict(start=start,end=end,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),reused=False)
    results=[]
    with ThreadPoolExecutor(max_workers=4) as executor:
        pending=[executor.submit(receive,start) for start in range(0,size,step)]
        for future in as_completed(pending):
            row=future.result();results.append(row)
            print('ranges',len(results),'of',len(pending),flush=True)
    results.sort(key=lambda r:r['start'])
    target=HERE/'download/range-recovery'/Path(FILE).name
    with target.open('xb') as handle:
        for row in results:handle.write((pieces/f"{row['start']:010d}-{row['end']:010d}.part").read_bytes())
    with (HERE/'DOWNLOAD_RECOVERY.json').open('x',encoding='utf-8') as handle:
        json.dump(dict(completed_at_utc=datetime.now(timezone.utc).isoformat(),expected_bytes=size,actual_bytes=target.stat().st_size,
            sha256=hashlib.sha256(target.read_bytes()).hexdigest(),parts=results,source_file=FILE,notebook_version=1,
            recovery_method='Sequential range transfer stopped locally to finish only missing ranges using four download threads; completed pieces retained.',
            ephemeral_signed_url_persisted=False,reran_GPU=False),handle,indent=2)
    print('Recovered full raw archive',flush=True)
