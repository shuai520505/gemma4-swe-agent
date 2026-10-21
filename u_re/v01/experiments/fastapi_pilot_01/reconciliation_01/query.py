"""Bounded read-only Kaggle reconciliation. All mutation operations fail closed."""
import contextlib
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import traceback
from urllib.parse import urlsplit

import requests
from u_re.v01.experiments.fastapi_pilot_01.auth_diagnose import inventory,redact

HERE=Path(__file__).resolve().parent
PILOT=HERE.parent
ROOT=PILOT.parents[3]
OWNER='wudangdexiaodoashi'
SLUG='gemma4-u-re-fastapi-pilot01-cpu01'
TARGET=OWNER+'/'+SLUG
CONTROL=OWNER+'/gemma4-u-re-requests-fixture-cpu01'
ALLOWED={'IntrospectToken','ListKernels','GetKernel','GetKernelSessionStatus','ListKernelSessionOutput'}
MAX_HTTP=24
MAX_LIST_PAGES=10


def utc():return datetime.now(timezone.utc).isoformat()


def write(name,data):
    path=HERE/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,indent=2,default=str);f.write('\n')


def allowed_request(method,url):
    parsed=urlsplit(url)
    return method=='POST' and parsed.hostname=='api.kaggle.com' and parsed.path.rsplit('/',1)[-1] in ALLOWED


def metadata(obj):
    # Preserve unknown private/version flags instead of SDK property defaults.
    keys=['id','ref','slug','author','current_version_number','last_run_time','is_private',
          'enable_gpu','enable_tpu','language','kernel_type']
    return {k:getattr(obj,'_'+k,None) for k in keys}


def run():
    assert not (HERE/'READONLY_QUERY_LEDGER.json').exists(),'No automatic repeated query run'
    _,_,_,secrets=inventory()
    filepaths=[Path.home()/'.kaggle'/n for n in ('kaggle.json','access_token','access_token.txt','credentials.json')]
    before={str(p):p.read_bytes() for p in filepaths if p.is_file()}
    ledger=dict(started_at_utc=utc(),target=TARGET,control=CONTROL,max_http=MAX_HTTP,max_list_pages=MAX_LIST_PAGES,
        sdk_version=importlib.metadata.version('kaggle'),kagglesdk_version=importlib.metadata.version('kagglesdk'),
        identity_confirmed=False,HTTP=[],queries=[],pagination={},SaveKernel_requests=0,
        resource_mutations=0,credential_mutations=0,request_body_or_headers_saved=False)
    active={'name':'SDK initialization','identifiers':{}}
    original=requests.Session.send
    def send(session,request,**kwargs):
        if not allowed_request(request.method,request.url):
            raise RuntimeError('Non-allowlisted network operation refused before dispatch')
        assert len(ledger['HTTP'])<MAX_HTTP,'Read-only HTTP bound reached'
        operation=urlsplit(request.url).path.rsplit('/',1)[-1]
        row=dict(sent_at_utc=utc(),operation=operation,method=request.method,
                 query=active['name'],identifiers=active['identifiers'])
        ledger['HTTP'].append(row);kwargs['timeout']=35
        try:
            response=original(session,request,**kwargs)
            row.update(received_at_utc=utc(),http_status=response.status_code,
                       content_type=response.headers.get('Content-Type','').split(';')[0])
            try:
                data=response.json();row['response_parsed']=True
                if operation=='IntrospectToken' and isinstance(data,dict):
                    row['active']=data.get('active') if isinstance(data.get('active'),bool) else None
                    row['identity_matches_expected']=data.get('username')==OWNER
                if response.status_code>=400 and isinstance(data,dict):
                    error=data.get('error',data)
                    if isinstance(error,dict):
                        for k in ('code','status','message'):
                            if isinstance(error.get(k),(str,int)):row['error_'+k]=redact(error[k],secrets)
            except ValueError:row['response_parsed']=False
            return response
        except requests.RequestException as exc:
            row.update(exception_class=type(exc).__name__,redacted_error=redact(str(exc),secrets));raise
        finally:
            # Durable append snapshot, no arbitrary bodies, cookies or headers.
            name='queries/http-'+str(len(ledger['HTTP'])).zfill(2)+'.json'
            write(name,row)
    requests.Session.send=send
    from kagglesdk.kaggle_creds import KaggleCredentials
    originals={n:getattr(KaggleCredentials,n) for n in ('refresh_access_token','generate_access_token','save','delete')}
    def refuse(*args,**kwargs):raise RuntimeError('Credential mutation refused')
    for n in originals:setattr(KaggleCredentials,n,refuse)
    capture=io.StringIO();identity=dict(target=TARGET,exists=None,accepted_version=None,version_created_at=None,
        original_save_association=None,source_sha256=None,source_matches_original=None,metadata=None)
    try:
        with contextlib.redirect_stdout(capture),contextlib.redirect_stderr(capture):
            from kaggle import api
        ledger['identity_confirmed']=api.get_config_value('username')==OWNER
        assert ledger['identity_confirmed'],'Identity mismatch: STOP'
        from kagglesdk.kernels.types.kernels_api_service import ApiListKernelsRequest,KernelsListViewType,KernelsListSortType,ApiGetKernelRequest
        with api.build_kaggle_client() as client:
            seen=set();token=None;complete=False;matches=[]
            for page in range(1,MAX_LIST_PAGES+1):
                active.update(name='explicit owner PROFILE pagination',identifiers=dict(user=OWNER,page=page,page_size=100,has_page_token=bool(token),sort='DATE_CREATED'))
                req=ApiListKernelsRequest();req.group=KernelsListViewType.PROFILE;req.user=OWNER
                req.page=page;req.page_size=100;req.language='all';req.kernel_type='all';req.output_type='all';req.search='';req.sort_by=KernelsListSortType.DATE_CREATED
                if token:req.page_token=token
                response=client.kernels.kernels_api_client.list_kernels(req)
                rows=response.kernels or [];next_token=response.next_page_token
                keys={r.ref for r in rows if r};new=keys-seen;seen|=keys
                exact=[metadata(r) for r in rows if r and r.ref==TARGET];matches+=exact
                entry=dict(query=active['name'],identifiers=active['identifiers'],returned_rows=len(rows),
                    newly_seen=len(new),has_next_page_token=bool(next_token),exact_matches=exact,
                    non_owner_refs=sum(not k.startswith(OWNER+'/') for k in keys))
                ledger['queries'].append(entry)
                if not next_token and len(rows)<100:complete=True;break
                if not new:
                    ledger['pagination']['stop']='no_new_rows_cannot_prove_complete';break
                token=next_token or None
            ledger['pagination'].update(pages=page,unique_rows=len(seen),complete=complete,exact_matches=matches,
                scope='explicit owner PROFILE, no search, all languages/types; pagination completeness is limited to API visibility, not proof of nonexistent resource')
            def get(ref,label):
                owner,slug=ref.split('/',1)
                active.update(name=label,identifiers=dict(user=owner,kernel_slug=slug))
                request=ApiGetKernelRequest();request.user_name=owner;request.kernel_slug=slug
                receipt=dict(query=label,identifiers=active['identifiers'])
                try:
                    value=client.kernels.kernels_api_client.get_kernel(request)
                    receipt['metadata']=metadata(value.metadata)
                    ledger['queries'].append(receipt);return value
                except BaseException as exc:
                    receipt.update(exception_class=type(exc).__name__,redacted_error=redact(str(exc),secrets))
                    ledger['queries'].append(receipt);return None
            control=get(CONTROL,'known own private GetKernel positive control')
            ledger['control_private_read_confirmed']=bool(control and control.metadata.ref==CONTROL and control.metadata._is_private is True)
            value=get(TARGET,'exact target GetKernel new endpoint (not repeated403 status)')
            if value is not None:
                assert value.metadata.ref==TARGET,'Returned identity mismatch'
                identity.update(exists=True,metadata=metadata(value.metadata),accepted_version=value.metadata._current_version_number,
                    source_sha256=hashlib.sha256(value.blob.source.encode()).hexdigest())
                expected=json.loads((PILOT/'results/cpu01/WIRE_NOTEBOOK_IDENTITY.json').read_bytes())
                identity['source_matches_original']=identity['source_sha256'] in (expected['file_sha256'],expected['serialized_wire_sha256'])
                if identity['accepted_version'] and identity['source_matches_original']:
                    identity['original_save_association']='exact resource,accepted version and source hash; version creation timestamp not yet provided'
                    ledger['recovery_gate']='VERSION_FOUND_REQUIRES_EXACT_VERSION_OUTPUT_RECOVERY'
                else:ledger['recovery_gate']='RESOURCE_EXISTS_BUT_VERSION_OR_SOURCE_UNCONFIRMED'
            else:ledger['recovery_gate']='NO_CONFIRMED_VERSION_NO_OUTPUT_REQUESTS'
    except BaseException as exc:
        ledger.update(stop=type(exc).__name__,redacted_error=redact(str(exc),secrets),
            traceback=[dict(module=Path(x.filename).name,function=x.name,line=x.lineno) for x in traceback.extract_tb(exc.__traceback__)])
    finally:
        requests.Session.send=original
        for n,v in originals.items():setattr(KaggleCredentials,n,v)
        ledger['credential_files_unchanged']=before=={str(p):p.read_bytes() for p in filepaths if p.is_file()}
        ledger['captured_output_redacted']=redact(capture.getvalue(),secrets)
        ledger['finished_at_utc']=utc()
        write('READONLY_QUERY_LEDGER.json',ledger);write('NOTEBOOK_IDENTITY.json',identity)
    print(json.dumps(dict(identity_confirmed=ledger['identity_confirmed'],pagination=ledger['pagination'],
        private_control=ledger.get('control_private_read_confirmed'),target=identity,recovery_gate=ledger.get('recovery_gate'),
        HTTP_count=len(ledger['HTTP']),stop=ledger.get('stop')),default=str))


if __name__=='__main__':run()
