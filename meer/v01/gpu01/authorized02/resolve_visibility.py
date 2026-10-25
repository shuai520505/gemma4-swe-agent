"""Alternative official list view for redacted profile entries; read-only."""
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
from urllib.parse import urlsplit
import requests
from .read_preflight import HERE,PRIVATE,save,OWNER

def run():
    from kaggle import api
    from kagglesdk.kernels.types.kernels_api_service import ApiListKernelsRequest,KernelsListViewType,KernelsListSortType
    dest=HERE/'preflight/visibility01';dest.mkdir(parents=True,exist_ok=False)
    rawdir=PRIVATE/'visibility01';rawdir.mkdir(parents=True,exist_ok=False)
    original=requests.Session.send;ledger=[]
    def send(session,request,**kwargs):
        op=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert op in ['IntrospectToken','ListKernels'] and len(ledger)<8
        kwargs.update(timeout=45,allow_redirects=False)
        r=original(session,request,**kwargs)
        ledger.append(dict(operation=op,status=r.status_code,utc=datetime.now(timezone.utc).isoformat(),body_sha256=hashlib.sha256(r.content).hexdigest()))
        if op=='ListKernels':(rawdir/f'{len(ledger):02d}.json').write_bytes(r.content)
        return r
    requests.Session.send=send;rows=[];complete=False
    try:
        with api.build_kaggle_client() as client:
            token=None
            for page in range(1,6):
                q=ApiListKernelsRequest();q.group=KernelsListViewType.PUBLIC_AND_USERS_PRIVATE;q.user=OWNER
                q.page=page;q.page_size=100;q.sort_by=KernelsListSortType.DATE_CREATED
                q.kernel_type='all';q.language='all';q.output_type='all'
                if token:q.page_token=token
                reply=client.kernels.kernels_api_client.list_kernels(q)
                rows.extend(dict(ref=r.ref,id=r.id,slug=r.slug,last_run_time=r.last_run_time) for r in reply.kernels or [])
                token=reply.next_page_token
                if not token and len(reply.kernels or [])<100:complete=True;break
        value=dict(complete=complete,rows=rows,redacted_rows=[r for r in rows if not r['ref']],
                   prior_unknown_matches=[r for r in rows if r['ref'].endswith('/gemma4-u-re-v02b-gemma-batch02')],
                   scope='Official enum PUBLIC_AND_USERS_PRIVATE, same authenticated owner; absence does not establish rejected dispatch',HTTP=ledger,SaveKernel=0)
        save(dest/'VISIBILITY.json',value)
        print(json.dumps(dict(complete=complete,count=len(rows),redacted=len(value['redacted_rows']),unknown_matches=len(value['prior_unknown_matches']))))
    finally:
        requests.Session.send=original;save(dest/'READ_LEDGER.json',ledger)

if __name__=='__main__':run()
