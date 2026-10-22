"""Bounded current score/quota and packaging-output reads. Never save or submit."""
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import urlsplit
import requests

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]

def run():
    out=HERE/'readonly';out.mkdir(exist_ok=False)
    ledger=[];rawquota={};original=requests.Session.send
    def send(session,request,**kwargs):
        op=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert op in ('IntrospectToken','ListSubmissions','GetAcceleratorQuotaStatistics','GetKernel','ListKernelSessionOutput') and len(ledger)<10
        kwargs.update(timeout=45,allow_redirects=False)
        r=original(session,request,**kwargs)
        ledger.append(dict(operation=op,http_status=r.status_code,utc=datetime.now(timezone.utc).isoformat()))
        if op=='GetAcceleratorQuotaStatistics':
            rawquota.update({k:v for k,v in r.json().get('gpuQuota',{}).items() if k in ('totalTimeAllowed','timeUsed','timeReserved','nextResetTime','acceleratorType')})
        return r
    requests.Session.send=send
    try:
        from kaggle import api
        rows=api.competition_submissions('gemma-4-developer-agent')
        safe=[]
        for row in rows:
            d=row.to_dict(ignore_defaults=False)
            if d.get('ref') in (57505115,57261002,57402336):safe.append({k:d.get(k) for k in ('ref','status','date','publicScore','errorDescription','description')})
        (out/'FORMAL_STATUS.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),submissions=safe,new_submission=False),indent=2)+'\n')
        api.quota_view()
        total,used,reserved=[Decimal(rawquota[k].removesuffix('s')) for k in ('totalTimeAllowed','timeUsed','timeReserved')]
        (out/'QUOTA.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),raw=rawquota,remaining_report_seconds=str(total-used-reserved),threshold=20600,threshold_pass=total-used-reserved>=20600,live_capacity='RUNTIME_RECHECK_REQUIRED'),indent=2)+'\n')
        from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
        with api.build_kaggle_client() as c:
            q=ApiGetKernelRequest();q.user_name='wudangdexiaodoashi';q.kernel_slug='u-re-full-v01-first-official-score'
            v=c.kernels.kernels_api_client.get_kernel(q);m=v.metadata
            assert m.id==140121936 and m.current_version_number==1
            q=ApiListKernelSessionOutputRequest();q.user_name='wudangdexiaodoashi';q.kernel_slug='u-re-full-v01-first-official-score';q.version_label='1'
            outputs=c.kernels.kernels_api_client.list_kernel_session_output(q)
            listing=[dict(file_name=x.file_name,size=getattr(x,'size',None)) for x in outputs.files or []]
            (out/'FORMAL_PACKAGING_OUTPUTS.json').write_text(json.dumps(dict(id=m.id,version=m.current_version_number,ref=m.ref,files=listing,meaning='Packaging Notebook output is not hidden competition inference trajectory'),indent=2)+'\n')
        local=ROOT/'u_re/v01/official/full_first_score_01'
        private=ROOT.parent/'private-evidence'
        (out/'LOCAL_EVIDENCE_INDEX.json').write_text(json.dumps(dict(
            packaging_log_sha256=hashlib.sha256((local/'reads/read-02/evidence_confirmed/output/notebook.log').read_bytes()).hexdigest(),
            existing_private_formal_files=[str(p.relative_to(private)) for p in (private/'formal_score').rglob('*') if p.is_file()],
            SDK_submission_signature=str(inspect.signature(api.competition_submissions)),
            trajectory_status='FORMAL_TRAJECTORY_NOT_AVAILABLE'),indent=2)+'\n')
    finally:
        requests.Session.send=original
        (out/'READ_LEDGER.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(json.dumps(dict(score=safe,quota_remaining=str(total-used-reserved),formal_trajectory='NOT_AVAILABLE')))

if __name__=='__main__':run()
