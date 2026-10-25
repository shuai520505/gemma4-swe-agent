"""Bounded, paced read-only recovery. No save, session creation or inference."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlsplit
import requests

HERE=Path(__file__).resolve().parent
GPU=HERE.parent
OWNER='wudangdexiaodoashi'
PRIVATE=GPU.parents[3]/'private-evidence/meer_v01_authorized02'

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,default=str)

def run():
    dest=HERE/'preflight/read01';dest.mkdir(parents=True,exist_ok=False)
    rawdest=PRIVATE/'read01';rawdest.mkdir(parents=True,exist_ok=False)
    ledger=[];raw_quota={};original=requests.Session.send;raw_rows=[]
    def send(session,request,**kwargs):
        op=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert op in ['IntrospectToken','ListKernels','GetKernelSessionStatus','GetAcceleratorQuotaStatistics','ListModelInstanceVersionFiles']
        assert len(ledger)<270
        kwargs.update(timeout=45,allow_redirects=False)
        started=time.monotonic();response=original(session,request,**kwargs)
        item=dict(operation=op,status=response.status_code,utc=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-started,
                  body_sha256=hashlib.sha256(response.content).hexdigest())
        ledger.append(item)
        # Never store credentials/headers or signed download URLs in public output.
        if op in ['ListKernels','GetAcceleratorQuotaStatistics']:
            (rawdest/f'{len(ledger):03d}-{op}.json').write_bytes(response.content)
        if response.status_code==200:
            if op=='GetAcceleratorQuotaStatistics':raw_quota.update(response.json()['gpuQuota'])
            if op=='ListKernels':raw_rows.extend(response.json().get('kernels',[]))
        save(dest/f'http-{len(ledger):03d}.json',item)
        return response
    requests.Session.send=send
    try:
        from kaggle import api
        from kagglesdk.kernels.types.kernels_api_service import (ApiListKernelsRequest,KernelsListViewType,KernelsListSortType,ApiGetKernelSessionStatusRequest)
        assert api.get_config_value('username')==OWNER
        resources=[];complete=False;token=None
        with api.build_kaggle_client() as client:
            for page in range(1,6):
                q=ApiListKernelsRequest();q.user=OWNER;q.group=KernelsListViewType.PROFILE;q.sort_by=KernelsListSortType.DATE_CREATED
                q.page=page;q.page_size=100;q.kernel_type='all';q.language='all';q.output_type='all';q.search=''
                if token:q.page_token=token
                reply=client.kernels.kernels_api_client.list_kernels(q)
                resources.extend(reply.kernels or []);token=reply.next_page_token
                if not token and len(reply.kernels or [])<100:complete=True;break
        assert complete,'Owned list incomplete'
        safe=[dict(id=r.id,ref=r.ref,slug=r.slug,last_run_time=r.last_run_time,current_version=r.current_version_number,
                   enable_gpu_raw=r._enable_gpu,machine_shape=r.machine_shape) for r in resources]
        save(dest/'OWNED_RESOURCES.json',dict(complete=complete,resources=safe,raw_response_rows=len(raw_rows),raw_keys=sorted({k for r in raw_rows for k in r})))
        quota=api.quota_view()
        assert Decimal(str(quota.gpu_quota.total_time_allowed.total_seconds()))==Decimal(raw_quota['totalTimeAllowed'].removesuffix('s'))
        remaining=Decimal(raw_quota['totalTimeAllowed'].removesuffix('s'))-Decimal(raw_quota['timeUsed'].removesuffix('s'))-Decimal(raw_quota['timeReserved'].removesuffix('s'))
        model=api.model_instance_version_files('google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',page_size=100)
        frozen=json.loads((GPU/'EXECUTION_MANIFEST.json').read_bytes())
        model_ok=not model.next_page_token and {r.name for r in model.files}==set(frozen['model']['files'])
        save(dest/'QUOTA_MODEL.json',dict(raw_quota=raw_quota,remaining_report_seconds=str(remaining),quota_gate=remaining>=41200,
             model_file_names_match=model_ok,actual_model_hashes='RUNTIME_RECHECK_REQUIRED',actual_GPU_allocation='NOT_YET_ALLOCATED'))
        print(json.dumps(dict(stage='LIST_QUOTA_MODEL',owned_rows=len(safe),blank_rows=sum(not r['ref'] for r in safe),
                  remaining_report_seconds=str(remaining),model_files_match=model_ok)),flush=True)
        # An unaddressable metadata object cannot be silently treated as idle.
        blank=[r for r in safe if not r['ref']]
        states=[]
        # Recover the previously UNKNOWN dispatch explicitly, without changing its historical state.
        refs=['gemma4-u-re-v02b-gemma-batch02']+[r['ref'].rsplit('/',1)[-1] for r in safe if r['ref']]
        with api.build_kaggle_client() as client:
            for i,slug in enumerate(dict.fromkeys(refs)):
                time.sleep(3)
                q=ApiGetKernelSessionStatusRequest();q.user_name=OWNER;q.kernel_slug=slug
                try:
                    r=client.kernels.kernels_api_client.get_kernel_session_status(q)
                    row=dict(slug=slug,status=r.status.name)
                except Exception as exc:
                    row=dict(slug=slug,status='UNKNOWN_READ_FAILURE',error_type=type(exc).__name__,HTTP_status=ledger[-1]['status'])
                states.append(row);save(dest/f'status-{i:03d}.json',row)
                if i%10==0:print(json.dumps(dict(stage='PACED_STATUS_RECOVERY',checked=len(states),total=len(set(refs)),last_status=row['status'])),flush=True)
                if ledger[-1]['status']==429:break
        value=dict(queried_utc=datetime.now(timezone.utc).isoformat(),owned_rows=len(safe),states=states,unaddressable_rows=blank,
                   unresolved=[r for r in states if r['status'] not in ['COMPLETE','ERROR','CANCELLED']],
                   remaining_report_seconds=str(remaining),quota_gate=remaining>=41200,model_names_gate=model_ok,
                   prior_UNKNOWN_preserved=True,GPU_SaveKernel=0)
        save(dest/'DYNAMIC_PREFLIGHT.json',value)
        print(json.dumps(dict(stage='DONE',statuses=len(states),unresolved=len(value['unresolved']),blank_rows=len(blank))),flush=True)
        return value
    finally:
        requests.Session.send=original;save(dest/'READ_LEDGER.json',ledger)

if __name__=='__main__':run()
