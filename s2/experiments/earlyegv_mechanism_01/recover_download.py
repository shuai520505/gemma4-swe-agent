"""Read-only ranged recovery of the completed immutable Notebook output."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent
FILE = 's2_earlyegv_mechanism_01/gpu01/20261020T072100_699825Z.zip'
SLUG = 'gemma4-s2-earlyegv-mechanism-01'
original = requests.Session.send


def send(self, request, **kwargs):
    kwargs.setdefault('timeout', (15,30))
    return original(self, request, **kwargs)


requests.Session.send = send
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest


if __name__ == '__main__':
    prior = HERE / 'download' / FILE
    assert prior.exists() and prior.stat().st_size == 0
    prior.rename(prior.with_suffix('.zip.incomplete'))
    (HERE / 'DOWNLOAD_ATTEMPT_01.json').write_text(json.dumps(dict(
        failure='requests.exceptions.ChunkedEncodingError / IncompleteRead',
        received_in_memory_bytes=3882604, additional_expected_bytes=38423354,
        expected_total_bytes=42305958, persisted_file_bytes=0,
        retained_as=str(prior.with_suffix('.zip.incomplete').relative_to(HERE)),
        recovery='Range download of same completed version; no GPU/Agent/Notebook retry.'),indent=2)+'\n',encoding='utf-8')
    request = ApiListKernelSessionOutputRequest()
    request.user_name='wudangdexiaodoashi';request.kernel_slug=SLUG;request.page_size=100
    with api.build_kaggle_client() as k:
        listing=k.kernels.kernels_api_client.list_kernel_session_output(request)
    item=next(f for f in listing.files if f.file_name==FILE)
    target=HERE/'download/range-recovery'/Path(FILE).name
    target.parent.mkdir(exist_ok=True)
    pieces=HERE/'download/range-parts';pieces.mkdir(exist_ok=False)
    size=42305958
    step=1024*1024
    manifest=[]
    for start in range(0,size,step):
        end=min(size,start+step)-1
        response=requests.get(item.url,headers={'Range':f'bytes={start}-{end}'},timeout=(15,30))
        response.raise_for_status()
        assert response.status_code==206, response.status_code
        assert response.headers['Content-Range']==f'bytes {start}-{end}/{size}',response.headers.get('Content-Range')
        raw=response.content
        assert len(raw)==end-start+1
        part=pieces/f'{start:010d}-{end:010d}.part'
        with part.open('xb') as handle:handle.write(raw)
        manifest.append(dict(start=start,end=end,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        print('received',end+1,'/',size,flush=True)
    with target.open('xb') as handle:
        for row in manifest:
            handle.write((pieces/f"{row['start']:010d}-{row['end']:010d}.part").read_bytes())
    (HERE/'DOWNLOAD_RECOVERY.json').write_text(json.dumps(dict(
        completed_at_utc=datetime.now(timezone.utc).isoformat(),expected_bytes=size,
        actual_bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        parts=manifest,source_file=FILE,notebook_version=1,
        ephemeral_signed_url_persisted=False,reran_GPU=False),indent=2)+'\n',encoding='utf-8')
    print('Recovered',target,flush=True)
