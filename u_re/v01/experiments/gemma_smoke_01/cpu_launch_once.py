"""User-authorized CPU interface Notebook only. One durable dispatch, no GPU."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit
import requests
from .cpu_notebook import CPU,HERE,ROOT,SLUG,EXECUTION_ID,controller_module,sha,write

def preflight():
    from kagglesdk.kaggle_env import get_access_token_from_env
    from kagglesdk.kaggle_client import KaggleClient
    from kagglesdk.kernels.types.kernels_api_service import ApiListKernelsRequest,KernelsListViewType,KernelsListSortType
    auth=json.loads((CPU/'preflight/AUTH_STATUS.json').read_text(encoding='utf-8'))
    assert auth['status']=='AUTH_READONLY_GO' and auth['identity_confirmed'] and not auth['credential_files_changed']
    token,_=get_access_token_from_env();assert token
    original=requests.Session.send;ledger=[];seen=set();complete=False;collision=False
    def send(session,request,**kw):
        operation=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert operation in ('IntrospectToken','ListKernels') and len(ledger)<8
        kw.update(timeout=45,allow_redirects=False)
        r=original(session,request,**kw);ledger.append(dict(operation=operation,status=r.status_code));return r
    requests.Session.send=send
    try:
        with KaggleClient(api_token=token,verbose=False) as client:
            page_token=None
            for page in range(1,6):
                q=ApiListKernelsRequest();q.user=SLUG.split('/')[0];q.page_size=100;q.page=page
                q.group=KernelsListViewType.PROFILE;q.sort_by=KernelsListSortType.DATE_CREATED
                q.kernel_type='all';q.language='all';q.output_type='all';q.search=''
                if page_token:q.page_token=page_token
                result=client.kernels.kernels_api_client.list_kernels(q)
                rows=result.kernels or [];refs={r.ref for r in rows};seen|=refs
                collision|=SLUG in refs
                page_token=result.next_page_token
                if not page_token and len(rows)<100:complete=True;break
    finally:requests.Session.send=original
    value=dict(identity_confirmed=True,current_readonly_GO=True,slug_conflict=collision,
        pagination_complete=complete,visible_records=len(seen),HTTP=ledger,
        limitation='API-visible owned resources only; no create-only guarantee from server',
        queried_utc=datetime.now(timezone.utc).isoformat())
    number=len(list((CPU/'preflight').glob('SLUG_CHECK*.json')))+1
    write(CPU/'preflight'/f'SLUG_CHECK_{number:02d}.json',value)
    assert complete and not collision,'Slug collision or incomplete read-only listing'
    return value

def launch():
    spec=json.loads((CPU/'BUILD.json').read_text(encoding='utf-8'));directory=CPU/'notebook'
    raw=(directory/'study.ipynb').read_bytes();metadata=json.loads((directory/'kernel-metadata.json').read_text(encoding='utf-8'))
    assert sha(raw)==spec['Notebook_sha256'] and sha(json.dumps(json.loads(raw)).encode())==spec['wire_sha256']
    assert metadata['enable_gpu'] is False and metadata['enable_tpu'] is False and metadata['enable_internet'] is False
    assert not metadata['model_sources'] and metadata['id']==SLUG
    gates=preflight();gates.update(payload_integrity=True,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    grant=dict(execution_id=EXECUTION_ID,slug=SLUG,max_SaveKernel_dispatches=1,
        human_message_reference='Current human instruction: 你可以使用kaggle的notebook来完成这个任务; interpreted CPU-only official interface validation, no GPU/Gemma authorization.',
        **{k:spec[k] for k in ('Notebook_sha256','wire_sha256','payload_sha256')})
    write(CPU/'AUTHORIZATION.json',grant)
    controller=controller_module().Controller(CPU/'execution',spec)
    from kaggle import api
    # The CPU02 guard rejects every operation except the unique CPU SaveKernel, sets Retry(0), and logs before JSON.
    try:
        result=controller.execute(grant,gates,lambda:api.kernels_push(str(directory),timeout='3600',acc=None))
        write(CPU/'SDK_SAFE_RESULT.json',dict(Notebook_id=getattr(result,'kernel_id',None),
            version=getattr(result,'version_number',None),ref=getattr(result,'ref',None)))
    finally:
        write(CPU/'DISPATCH_SUMMARY.json',dict(dispatches=controller.dispatches,states=controller.journal.states(),GPU=False,Gemma_calls=0))
    print(json.dumps(json.loads((CPU/'DISPATCH_SUMMARY.json').read_text(encoding='utf-8'))))

if __name__=='__main__':launch()
