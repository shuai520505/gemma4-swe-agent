"""Official Kaggle CLI dispatch, at most one durable SaveKernel attempt."""
from contextlib import redirect_stdout,redirect_stderr
from datetime import datetime,timezone
import io
import json
import os
import subprocess
import sys
from urllib.parse import urlsplit

from .prepare import HERE,PRIVATE,ROOT,REF,WINDOW,sha,write,verify_history


def read(args,label,timeout=300):
    folder=PRIVATE/'cli'/label;folder.mkdir(parents=True,exist_ok=False)
    try:
        r=subprocess.run(['kaggle',*args],capture_output=True,timeout=timeout,
            env=dict(os.environ,HTTPS_PROXY='http://127.0.0.1:7890',PYTHONIOENCODING='utf-8'))
        code,out,err=r.returncode,r.stdout,r.stderr
    except subprocess.TimeoutExpired as exc:code,out,err=None,exc.stdout or b'',exc.stderr or b''
    (folder/'stdout.txt').write_bytes(out);(folder/'stderr.txt').write_bytes(err)
    write(folder/'RECORD.json',dict(arguments=args,returncode=code,stdout_sha256=sha(out),stderr_sha256=sha(err)))
    print(json.dumps(dict(label=label,returncode=code,stdout_bytes=len(out),stderr_bytes=len(err))),flush=True)


def bind():
    assert not (PRIVATE/'GPU_DISPATCH.json').exists(),'Existing attempt: read-only recovery only'
    gate=json.loads((HERE/'DYNAMIC_PREFLIGHT.json').read_bytes());assert gate['static_read_GO']
    assert gate['requested_window_seconds']==WINDOW
    assert (datetime.now(timezone.utc)-datetime.fromisoformat(gate['queried_UTC'])).total_seconds()<600
    folder=PRIVATE/'notebook-v1';nb=json.loads((folder/'study-template.ipynb').read_bytes())
    binding={k:gate[k] for k in ('remaining_report_seconds','queried_UTC','requested_window_seconds')}
    nb['cells'][0]['source']='DISPATCH_RESOURCE_BINDING='+repr(binding)+'\n'+nb['cells'][0]['source']
    for c in nb['cells']:
        c['id']=sha(c['source'].encode())[:12];compile(c['source'],'<final-GPU-notebook>','exec')
    raw=(json.dumps(nb,indent=1)+'\n').encode();(folder/'study.ipynb').write_bytes(raw)
    build=json.loads((HERE/'BUILD.json').read_bytes())
    build.update(Notebook_sha256=sha(raw),resource_binding=binding)
    write(HERE/'BUILD.json',build)
    print('Final Notebook frozen',sha(raw),'; no dispatch')


def push():
    verify_history()
    os.environ.update(HTTPS_PROXY='http://127.0.0.1:7890',PYTHONIOENCODING='utf-8')
    from kaggle import api
    from kaggle.cli import main
    import requests
    assert api.get_config_value('username')==REF.split('/')[0]
    gate=json.loads((HERE/'DYNAMIC_PREFLIGHT.json').read_bytes())
    assert gate['static_read_GO'] and (datetime.now(timezone.utc)-datetime.fromisoformat(gate['queried_UTC'])).total_seconds()<600
    folder=PRIVATE/'notebook-v1';build=json.loads((HERE/'BUILD.json').read_bytes())
    assert sha((folder/'study.ipynb').read_bytes())==build['Notebook_sha256']
    assert sha((folder/'payload.zip').read_bytes())==build['payload_sha256']
    meta=json.loads((folder/'kernel-metadata.json').read_bytes())
    assert meta['id']==REF and meta['is_private'] and meta['enable_gpu'] and not meta['enable_tpu'] and not meta['enable_internet']
    assert meta['machine_shape']=='NvidiaL4' and len(meta['model_sources'])==1
    assert subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).strip()==''
    claim=PRIVATE/'GPU_DISPATCH.json'
    with claim.open('x',encoding='utf8') as f:
        json.dump(dict(ref=REF,status='CLAIMED_NO_RETRY',max_dispatches=1,max_sessions=2,Notebook_sha256=build['Notebook_sha256'],
            payload_sha256=build['payload_sha256'],source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            owner_grant='Explicit human EGRD V0.3.2 task instruction'),f,indent=2);f.flush();os.fsync(f.fileno())
    sent=0;original=requests.Session.send
    def send(session,request,**kwargs):
        nonlocal sent
        op=urlsplit(request.url).path.rsplit('/',1)[-1]
        if op!='SaveKernel':return original(session,request,**kwargs)
        assert sent==0,'Second SaveKernel prohibited'
        body=json.loads(request.body)
        assert body['isPrivate'] is True and body['enableGpu'] is True and not body.get('enableTpu',False)
        assert not body.get('enableInternet',False)
        assert body['machineShape']=='NvidiaL4' and int(body['sessionTimeoutSeconds'])==WINDOW
        assert body['slug']==REF
        wire=json.loads(body['text']);expected=json.loads((folder/'study.ipynb').read_bytes())
        assert [c['source'] for c in wire['cells']]==[c['source'] for c in expected['cells']]
        sent+=1
        assert session.get_adapter(request.url).max_retries.total in (0,False),'Automatic HTTP retry is prohibited for SaveKernel'
        kwargs.update(timeout=180,allow_redirects=False)
        write(PRIVATE/'SAVEKERNEL_SEND.json',dict(operation=op,request_sha256=sha(request.body if isinstance(request.body,bytes) else request.body.encode()),
            Notebook_sha256=build['Notebook_sha256'],machine_shape=body['machineShape'],window=WINDOW,sent_UTC=datetime.now(timezone.utc).isoformat()))
        try:
            response=original(session,request,**kwargs)
            (PRIVATE/'SAVEKERNEL_RESPONSE.private.json').write_bytes(response.content)
            write(PRIVATE/'SAVEKERNEL_HTTP.json',dict(status=response.status_code,body_sha256=sha(response.content),bytes=len(response.content)))
            return response
        except BaseException as exc:
            write(PRIVATE/'SAVEKERNEL_TRANSPORT_ERROR.json',dict(type=type(exc).__name__,state='UNKNOWN_NO_RETRY'))
            raise
    out,err=io.StringIO(),io.StringIO();before=sys.argv;code=0
    requests.Session.send=send
    try:
        sys.argv=['kaggle','kernels','push','-p',str(folder),'-t',str(WINDOW),'--accelerator','NvidiaL4']
        with redirect_stdout(out),redirect_stderr(err):
            try:main()
            except SystemExit as exc:code=exc.code or 0
    except BaseException as exc:
        code=None;write(PRIVATE/'DISPATCH_EXCEPTION.json',dict(type=type(exc).__name__,state='UNKNOWN_NO_RETRY'))
    finally:
        requests.Session.send=original;sys.argv=before
        (PRIVATE/'CLI_PUSH.stdout.txt').write_text(out.getvalue(),encoding='utf8')
        (PRIVATE/'CLI_PUSH.stderr.txt').write_text(err.getvalue(),encoding='utf8')
        write(PRIVATE/'CLI_PUSH_RESULT.json',dict(returncode=code,SaveKernel_requests=sent,ref=REF,
              stdout_sha256=sha(out.getvalue().encode()),stderr_sha256=sha(err.getvalue().encode()),read_only_recovery_required=True))
    print(json.dumps(dict(returncode=code,SaveKernel_requests=sent,ref=REF,read_only_recovery_required=True)),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='bind':bind()
    elif sys.argv[1]=='push':push()
    else:read(sys.argv[2:],sys.argv[1])
