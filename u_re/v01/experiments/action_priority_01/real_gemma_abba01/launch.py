"""Authorized single SaveKernel. CPU02 durable claim/receipt/no-retry controller."""
from datetime import datetime,timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit
import requests
from .GPU_NOTEBOOK import HERE,ROOT,SLUG,ID,MODEL_SOURCE,controller_module,sha,write

def preflight():
    directory=HERE/'preflight';directory.mkdir(exist_ok=True)
    from u_re.v01.experiments.fastapi_pilot_01 import auth_diagnose
    auth_diagnose.HERE=directory
    auth=auth_diagnose.diagnose()
    assert auth['status']=='AUTH_READONLY_GO' and auth['identity_confirmed'] and not auth['credential_files_changed']
    from kaggle import api
    from kagglesdk.kernels.types.kernels_api_service import ApiListKernelsRequest,KernelsListViewType,KernelsListSortType,ApiGetKernelSessionStatusRequest
    original=requests.Session.send;ledger=[];quota={}
    def send(session,request,**kw):
        op=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert op in ('IntrospectToken','ListKernels','GetKernelSessionStatus','GetAcceleratorQuotaStatistics','ListModelInstanceVersionFiles') and len(ledger)<18
        kw.update(timeout=45,allow_redirects=False);response=original(session,request,**kw)
        ledger.append(dict(operation=op,status=response.status_code,utc=datetime.now(timezone.utc).isoformat()))
        if op=='GetAcceleratorQuotaStatistics':quota.update(response.json().get('gpuQuota',{}))
        return response
    requests.Session.send=send
    try:
        with api.build_kaggle_client() as client:
            refs=[];recent=[];token=None;complete=False
            for page in range(1,6):
                q=ApiListKernelsRequest();q.user=SLUG.split('/')[0];q.group=KernelsListViewType.PROFILE;q.sort_by=KernelsListSortType.DATE_CREATED
                q.page=page;q.page_size=100;q.kernel_type='all';q.language='all';q.output_type='all';q.search=''
                if token:q.page_token=token
                result=client.kernels.kernels_api_client.list_kernels(q);rows=result.kernels or []
                refs.extend(x.ref for x in rows);recent.extend(x for x in rows if getattr(x,'enable_gpu',False))
                token=result.next_page_token
                if not token and len(rows)<100:complete=True;break
            assert complete and all(not str(r).rstrip('/').endswith(SLUG) for r in refs),'Slug collision or incomplete listing'
            conflicts=[];states=[]
            for item in recent[:5]:
                q=ApiGetKernelSessionStatusRequest();q.user_name=SLUG.split('/')[0];q.kernel_slug=item.slug
                status=client.kernels.kernels_api_client.get_kernel_session_status(q).status.name
                states.append(dict(id=item.id,slug=item.slug,status=status))
                if status not in ('COMPLETE','ERROR','CANCELLED'):conflicts.append(item.slug)
            assert not conflicts,'Existing GPU Notebook conflict'
        api.quota_view()
        from decimal import Decimal
        remaining=Decimal(quota['totalTimeAllowed'].removesuffix('s'))-Decimal(quota['timeUsed'].removesuffix('s'))-Decimal(quota['timeReserved'].removesuffix('s'))
        assert remaining>=20600
        files=api.model_instance_version_files(MODEL_SOURCE,page_size=100)
        assert files and not files.next_page_token
        names=[x.name for x in files.files]
        lock=json.loads((HERE.parent/'integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json').read_bytes())
        assert set(names)==set(lock['model']['files']),'Model input file identity mismatch'
        value=dict(identity_confirmed=True,current_readonly_GO=True,slug_conflict=False,payload_integrity=True,
            raw_quota={k:quota.get(k) for k in ('totalTimeAllowed','timeUsed','timeReserved')},remaining_report_seconds=str(remaining),
            account_GPU_sessions=states,model_source_readable=True,model_files=names,
            machine_request='NvidiaL4;actual4L4 allocation checked before inference',requested_window=10000,
            source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),HTTP=ledger)
        write(directory/'DYNAMIC_PRECHECK.json',value)
        return value
    finally:requests.Session.send=original;write(directory/'READ_LEDGER.json',ledger)

def launch():
    assert not (HERE/'execution/dispatch.claim').exists(),'Prior dispatch:read only recovery only'
    spec=json.loads((HERE/'BUILD.json').read_bytes());raw=(HERE/'notebook/study.ipynb').read_bytes()
    assert sha(raw)==spec['Notebook_sha256'] and sha(json.dumps(json.loads(raw)).encode())==spec['wire_sha256']
    assert spec['sdk_versions']=={n:importlib.metadata.version(n) for n in ('kaggle','kagglesdk')}
    cached=HERE/'preflight/DYNAMIC_PRECHECK.json'
    if cached.exists():
        gates=json.loads(cached.read_bytes())
        assert (datetime.now(timezone.utc)-datetime.fromisoformat(gates['HTTP'][-1]['utc'])).total_seconds()<600,'Dynamic precheck older than10minutes;do not reuse'
    else:gates=preflight()
    gates['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    grant=json.loads((HERE/'GPU_AUTHORIZATION.json').read_bytes())
    assert gates['remaining_report_seconds']==grant['quota_at_dispatch_report_seconds'],'Refresh build if quota changed before dispatch'
    grant.update({k:spec[k] for k in ('Notebook_sha256','wire_sha256','payload_sha256')})
    write(HERE/'DISPATCH_AUTHORIZATION.json',grant)
    controller=controller_module().Controller(HERE/'execution',spec)
    from kaggle import api
    try:
        result=controller.execute(grant,gates,lambda:api.kernels_push(str(HERE/'notebook'),timeout='10000',acc='NvidiaL4'))
        write(HERE/'SDK_SAFE_RESULT.json',dict(Notebook_id=getattr(result,'kernel_id',None),version=getattr(result,'version_number',None),ref=getattr(result,'ref',None)))
    finally:write(HERE/'DISPATCH_SUMMARY.json',dict(dispatches=controller.dispatches,states=controller.journal.states(),GPU=True,formal_submission=False))

if __name__=='__main__':launch()
