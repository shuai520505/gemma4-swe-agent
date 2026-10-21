"""CPU02-only bounded read identity/collision snapshot, never Save or refresh."""
from datetime import datetime,timezone
import contextlib
import io
import json
from pathlib import Path
from urllib.parse import urlsplit
import requests
from .prepare import HERE,write
from .dispatch import SLUG


def snapshot(destination):
    events=[];original=requests.Session.send
    def send(session,request,**kwargs):
        op=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert request.method=='POST' and urlsplit(request.url).hostname=='api.kaggle.com'
        assert op in ('IntrospectToken','ListKernels') and len(events)<8
        kwargs['timeout']=35
        r=original(session,request,**kwargs)
        events.append(dict(operation=op,http_status=r.status_code,at_utc=datetime.now(timezone.utc).isoformat()))
        return r
    from kagglesdk.kaggle_creds import KaggleCredentials
    saved={n:getattr(KaggleCredentials,n) for n in ('save','delete','generate_access_token','refresh_access_token')}
    def refuse(*a,**kw):raise RuntimeError('No credential mutation authorized')
    for n in saved:setattr(KaggleCredentials,n,refuse)
    requests.Session.send=send
    output=io.StringIO()
    record=dict(queried_at_utc=datetime.now(timezone.utc).isoformat(),identity_confirmed=False,
        current_readonly_GO=False,slug_conflict=None,pagination_complete=False,HTTP=events,
        scope='CPU02 identity only; does not query or reclassify CPU01',resource_mutations=0)
    try:
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):from kaggle import api
        assert api.get_config_value('username')=='wudangdexiaodoashi'
        record['identity_confirmed']=True
        from kagglesdk.kernels.types.kernels_api_service import ApiListKernelsRequest,KernelsListViewType,KernelsListSortType
        seen=set();token=None;found=False
        with api.build_kaggle_client() as client:
            for page in range(1,6):
                q=ApiListKernelsRequest();q.user='wudangdexiaodoashi';q.group=KernelsListViewType.PROFILE
                q.sort_by=KernelsListSortType.DATE_CREATED;q.page=page;q.page_size=100;q.kernel_type='all';q.language='all';q.output_type='all';q.search=''
                if token:q.page_token=token
                r=client.kernels.kernels_api_client.list_kernels(q);keys={x.ref for x in r.kernels or []}
                new=keys-seen;seen|=keys;found=found or SLUG in keys
                if not r.next_page_token and len(r.kernels or [])<100:record['pagination_complete']=True;break
                if not new:break
                token=r.next_page_token or None
        record.update(pages=page,API_visible_records=len(seen),slug_conflict=found if record['pagination_complete'] else None,
            current_readonly_GO=True,collision_scope='API-visible profile only; not an authoritative server create-only guarantee')
    except BaseException as e:record['exception_class']=type(e).__name__
    finally:
        requests.Session.send=original
        for n,v in saved.items():setattr(KaggleCredentials,n,v)
    write(Path(destination),record);print(json.dumps(record))


if __name__=='__main__':snapshot(HERE/'evidence/READONLY_PREFLIGHT.json')
