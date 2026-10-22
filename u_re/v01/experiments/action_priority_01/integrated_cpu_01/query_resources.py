"""One read-only raw quota snapshot;no Notebook or Competition writes."""
from datetime import datetime,timezone
from decimal import Decimal
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import requests

HERE=Path(__file__).resolve().parent/'resources'


def run():
    HERE.mkdir(exist_ok=False);ledger=[];raw={};original=requests.Session.send
    def send(session,request,**kwargs):
        operation=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert operation in ('IntrospectToken','GetAcceleratorQuotaStatistics') and len(ledger)<3
        kwargs.update(timeout=45,allow_redirects=False)
        response=original(session,request,**kwargs)
        ledger.append(dict(operation=operation,HTTP_status=response.status_code,queried_utc=datetime.now(timezone.utc).isoformat()))
        if operation=='GetAcceleratorQuotaStatistics':
            value=response.json().get('gpuQuota',{})
            raw.update({k:v for k,v in value.items() if k in ('totalTimeAllowed','timeUsed','timeReserved','nextResetTime','acceleratorType')})
            (HERE/'RAW_GPU_QUOTA.json').write_text(json.dumps(dict(utc=ledger[-1]['queried_utc'],HTTP_status=response.status_code,response=raw),indent=2)+'\n')
        return response
    requests.Session.send=send
    try:
        from kaggle import api
        api.quota_view()
        values=[raw.get(k) for k in ('totalTimeAllowed','timeUsed','timeReserved')]
        valid=all(isinstance(v,str) and re.fullmatch(r'\d+(?:\.\d{1,9})?s',v) for v in values)
        remaining=sum((Decimal(values[0][:-1]),-Decimal(values[1][:-1]),-Decimal(values[2][:-1]))) if valid else None
        (HERE/'GPU_RESOURCE_ADMISSION.json').write_text(json.dumps(dict(raw_units='Protobuf Duration seconds;never SDK timedelta.seconds',
            valid=valid,remaining_report_seconds=str(remaining) if valid else None,planning_threshold=20600,
            quota_threshold_passed=remaining>=20600 if valid else None,planned_window_seconds=10000,window_approved=False,
            live_4L4_capacity='RUNTIME_RECHECK_REQUIRED',weights_currently_rehashed=False,GPU_authorized=False,GPU_allocation_requests=0),indent=2)+'\n')
    finally:
        requests.Session.send=original;(HERE/'READ_LEDGER.json').write_text(json.dumps(ledger,indent=2)+'\n')


if __name__=='__main__':run()
