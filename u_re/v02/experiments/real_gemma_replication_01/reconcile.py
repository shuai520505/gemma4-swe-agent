"""Bounded read-only discovery after an empty SaveKernel response, never resend."""
import ast,base64,json,types
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
import requests
from .notebook import HERE,ROOT,MODEL_SOURCE,location,sha
from .results import write

def discover(batch):
    directory,slug,_=location(batch)
    assert (directory/'execution/dispatch.claim').exists()
    number=len(list((directory/'discovery').glob('read-*')))+1;assert number<=3
    output=directory/'discovery'/f'read-{number:02d}';output.mkdir(parents=True,exist_ok=False)
    ledger=[];original=requests.Session.send;found=None;status=None;error=None
    def send(session,request,**kw):
        operation=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert operation in ('IntrospectToken','GetKernel','ListKernels') and len(ledger)<8
        kw.update(timeout=45,allow_redirects=False);response=original(session,request,**kw)
        ledger.append(dict(operation=operation,HTTP_status=response.status_code,utc=datetime.now(timezone.utc).isoformat()))
        return response
    requests.Session.send=send
    try:
        from kaggle import api
        from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelsRequest,KernelsListViewType,KernelsListSortType
        with api.build_kaggle_client() as client:
            svc=client.kernels.kernels_api_client
            try:
                q=ApiGetKernelRequest();q.user_name=slug.split('/')[0];q.kernel_slug=slug.split('/')[1]
                value=svc.get_kernel(q)
                # Reuse the source/owner/ref/version gate, with GPU-specific
                # config. Numeric ID is independently checked against raw fields
                # and later complete owned listing, never invented from slug.
                m=types.ModuleType('V02b_unknown_save_identity')
                path=ROOT/'u_re/v01/experiments/fastapi_pilot_01/attempts/cpu02/reconciliation_01/recover.py'
                source=path.read_text(encoding='utf8').replace("meta['enable_gpu'] is False","meta['enable_gpu'] is True").replace("meta['model_data_sources'] == []",repr(MODEL_SOURCE)+" in (meta['model_data_sources'] or []) and len(meta['model_data_sources'] or [])==1 and meta['machine_shape']=='NvidiaL4'")
                exec(compile(source,str(path),'exec'),m.__dict__)
                if not (directory/'BUILD_FREEZE.json').exists():(directory/'BUILD_FREEZE.json').write_bytes((directory/'BUILD.json').read_bytes())
                m.CPU02=directory;m.OWNER=slug.split('/')[0];m.SLUG=slug.split('/')[1];m.REF=slug;m.ID=value.metadata.id
                found=m.identity(value)
                write(output/'RESOURCE_IDENTITY.json',found)
                if found['state']=='IDENTITY_CONFIRMED':
                    write(directory/'RECOVERED_RESOURCE_IDENTITY.json',dict(Notebook_id=value.metadata.id,accepted_version=1,source='Independent read-only GetKernel source/owner/ref/slug/version/model verification after empty499; not a fabricated SaveKernel receipt',identity=found,original_receipt_unchanged=True))
            except Exception as exc:error=type(exc).__name__
            # Complete owned listing independently cross-checks discovered ID,
            # or supplies actual negative visibility evidence without rejection.
            rows=[];token=None;complete=False
            for page in range(1,6):
                q=ApiListKernelsRequest();q.user=slug.split('/')[0];q.group=KernelsListViewType.PROFILE;q.sort_by=KernelsListSortType.DATE_CREATED;q.page=page;q.page_size=100;q.kernel_type='all';q.language='all';q.output_type='all';q.search=''
                if token:q.page_token=token
                result=svc.list_kernels(q);items=result.kernels or []
                rows.extend(dict(id=x.id,slug=x.slug,ref=x.ref) for x in items)
                token=result.next_page_token
                if not token and len(items)<100:complete=True;break
            matches=[r for r in rows if str(r['ref']).rstrip('/').endswith(slug) or r['slug']==slug.split('/')[1]]
            write(output/'OWNED_LIST_RESULT.json',dict(complete=complete,visible_records=len(rows),matches=matches,negative_visibility_does_not_prove_rejection=True))
            if found and found['state']=='IDENTITY_CONFIRMED' and matches:
                assert len(matches)==1 and matches[0]['id']==found['metadata']['id']
            status='IDENTITY_CONFIRMED' if found and found['state']=='IDENTITY_CONFIRMED' else 'IDENTITY_UNKNOWN'
    except Exception as exc:error=type(exc).__name__
    finally:
        requests.Session.send=original
        write(output/'READ_LEDGER.json',dict(batch=batch,state=status or 'IDENTITY_UNKNOWN',HTTP=ledger,error_class=error,SaveKernel=0,GPU_retry=0,original_UNKNOWN_STOP_preserved=True))
    print(json.dumps(dict(batch=batch,state=status or 'IDENTITY_UNKNOWN',Notebook_id=found['metadata']['id'] if found else None,error_class=error)))

def delayed_owned_list(batch):
    """One delayed complete visibility check; never repeats an already failed Get."""
    directory,slug,_=location(batch);output=directory/'discovery/DELAYED_OWNED_LIST.json'
    assert not output.exists(),'Bounded single delayed listing already performed'
    ledger=[];original=requests.Session.send
    def send(session,request,**kw):
        op=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert op in ('IntrospectToken','ListKernels') and len(ledger)<7
        kw.update(timeout=45,allow_redirects=False);r=original(session,request,**kw)
        ledger.append(dict(operation=op,HTTP_status=r.status_code,utc=datetime.now(timezone.utc).isoformat()));return r
    requests.Session.send=send
    try:
        from kaggle import api
        from kagglesdk.kernels.types.kernels_api_service import ApiListKernelsRequest,KernelsListViewType,KernelsListSortType
        rows=[];token=None;complete=False
        with api.build_kaggle_client() as c:
            for page in range(1,6):
                q=ApiListKernelsRequest();q.user=slug.split('/')[0];q.group=KernelsListViewType.PROFILE;q.sort_by=KernelsListSortType.DATE_CREATED;q.page=page;q.page_size=100;q.kernel_type='all';q.language='all';q.output_type='all';q.search=''
                if token:q.page_token=token
                result=c.kernels.kernels_api_client.list_kernels(q);items=result.kernels or []
                rows.extend(dict(id=x.id,slug=x.slug,ref=x.ref) for x in items);token=result.next_page_token
                if not token and len(items)<100:complete=True;break
        matches=[r for r in rows if r['slug']==slug.split('/')[1] or str(r['ref']).rstrip('/').endswith(slug)]
        record=dict(complete=complete,visible_records=len(rows),matches=matches,HTTP=ledger,GetKernel=0,SaveKernel=0,negative_visibility_does_not_prove_rejection=True)
        write(output,record);print(json.dumps(record))
    finally:requests.Session.send=original

if __name__=='__main__':
    import sys
    if sys.argv[1]=='list':delayed_owned_list(int(sys.argv[2]))
    else:discover(int(sys.argv[1]))
