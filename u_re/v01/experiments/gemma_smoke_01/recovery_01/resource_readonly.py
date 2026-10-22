"""Bounded raw read-only quota and formal status snapshot. No save/submit API."""
from datetime import datetime,timezone
from decimal import Decimal
import json,re
from pathlib import Path
from urllib.parse import urlsplit
import requests
HERE=Path(__file__).resolve().parent/'resource_snapshot'
def write(name,value):
    HERE.mkdir(exist_ok=True)
    with (HERE/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,default=str)
def main():
    original=requests.Session.send; ledger=[]; quota={}
    def send(session,request,**kwargs):
        operation=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert operation in ('IntrospectToken','GetAcceleratorQuotaStatistics','ListSubmissions'),operation
        assert len(ledger)<8
        kwargs.update(timeout=45,allow_redirects=False)
        response=original(session,request,**kwargs)
        ledger.append(dict(operation=operation,http_status=response.status_code,utc=datetime.now(timezone.utc).isoformat()))
        if operation=='GetAcceleratorQuotaStatistics':
            data=response.json()
            for name in ('gpuQuota','tpuQuota'):
                if name in data:quota[name]={k:v for k,v in data[name].items() if k in ('totalTimeAllowed','timeUsed','timeReserved','nextResetTime','acceleratorType')}
            write('QUOTA_RAW.json',dict(utc=ledger[-1]['utc'],status=response.status_code,response=quota))
        return response
    requests.Session.send=send
    try:
        from kaggle import api
        api.quota_view()
        q=quota['gpuQuota']
        def seconds(v):
            assert re.fullmatch(r'\d+(?:\.\d{1,9})?s',v)
            return Decimal(v[:-1])
        total,used,reserved=[seconds(q[k]) for k in ('totalTimeAllowed','timeUsed','timeReserved')]
        write('GPU_RESOURCE.json',dict(total=str(total),used=str(used),reserved=str(reserved),remaining=str(total-used-reserved),units='raw protobuf Duration seconds, not SDK timedelta.seconds',planning_threshold=10800,quota_passed=total-used-reserved>=10800,live_4L4_capacity='RUNTIME_RECHECK_REQUIRED',window_seconds_requested=5400,window_approved=False,allocation_requested=False))
        rows=api.competition_submissions('gemma-4-developer-agent')
        safe=[]
        for row in rows:
            d=row.to_dict(ignore_defaults=False)
            safe.append({k:d.get(k) for k in ('ref','status','date','public_score','publicScore','error_description','errorDescription','description') if k in d})
        write('FORMAL_STATUS.json',dict(utc=datetime.now(timezone.utc).isoformat(),submissions=safe,new_submission=False))
    finally:
        requests.Session.send=original;write('READ_LEDGER.json',ledger)
if __name__=='__main__':main()
