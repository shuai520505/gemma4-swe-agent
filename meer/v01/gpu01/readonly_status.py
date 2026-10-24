"""Finite read-only status checks; an absent historical slug is not rejection."""
from datetime import datetime, timezone
import json
from urllib.parse import urlsplit
import requests
from .prepare import put


def run():
    from kaggle import api
    from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelSessionStatusRequest
    refs=['meer-v01-cpu03','meer-v01-cpu-binding01','gemma4-u-re-v02b-gemma-batch02']
    ledger=[]; rows=[]; original=requests.Session.send
    def send(session,request,**kwargs):
        op=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert op in ('IntrospectToken','GetKernelSessionStatus') and len(ledger)<8
        kwargs.update(timeout=45,allow_redirects=False)
        response=original(session,request,**kwargs)
        ledger.append(dict(operation=op,status=response.status_code,utc=datetime.now(timezone.utc).isoformat()))
        return response
    requests.Session.send=send
    try:
        with api.build_kaggle_client() as client:
            for slug in refs:
                request=ApiGetKernelSessionStatusRequest();request.user_name='wudangdexiaodoashi';request.kernel_slug=slug
                try:
                    reply=client.kernels.kernels_api_client.get_kernel_session_status(request)
                    rows.append(dict(slug=slug,status=reply.status.name))
                except Exception as exc:
                    rows.append(dict(slug=slug,status='READ_UNAVAILABLE',error_type=type(exc).__name__))
    finally:
        requests.Session.send=original
        value=dict(queried_at_utc=datetime.now(timezone.utc).isoformat(),resources=rows,HTTP=ledger,
                   prior_PR27_Batch2_dispatch_status='UNKNOWN',
                   historical_slug_absence_is_not_rejection=True,GPU_SaveKernel=0)
        put('readonly01/FINITE_STATUS_READ.json',value)
    print(json.dumps(value))


if __name__=='__main__':run()
