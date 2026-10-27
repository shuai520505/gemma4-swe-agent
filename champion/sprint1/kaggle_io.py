"""One private CPU-only CLI dispatch; all subsequent operations read-only."""
import io
import json
import os
from contextlib import redirect_stdout,redirect_stderr
import subprocess
import sys
from urllib.parse import urlsplit
from .build import HERE,PRIVATE,sha,write
from .cpu_notebook import REF

def push():
    os.environ.update(HTTPS_PROXY='http://127.0.0.1:7890',PYTHONIOENCODING='utf-8')
    import requests
    from kaggle import api
    from kaggle.cli import main
    folder=PRIVATE/'kaggle-cpu-v1';meta=json.loads((folder/'kernel-metadata.json').read_bytes())
    assert meta['id']==REF and meta['is_private'] and not meta['enable_gpu'] and not meta['enable_tpu']
    assert not meta['enable_internet'] and not meta['model_sources'] and meta['machine_shape']==''
    assert api.get_config_value('username')==REF.split('/')[0]
    build=json.loads((HERE/'CPU_BUILD.json').read_bytes())
    assert sha((folder/'study.ipynb').read_bytes())==build['Notebook_sha256']
    with (PRIVATE/'CPU_DISPATCH.json').open('x',encoding='utf8') as stream:
        json.dump(dict(ref=REF,maximum_dispatches=1,status='CLAIMED_NO_RETRY',Notebook_sha256=build['Notebook_sha256']),stream);stream.flush();os.fsync(stream.fileno())
    original=requests.Session.send;sent=0
    def send(session,request,**kwargs):
        nonlocal sent
        if urlsplit(request.url).path.rsplit('/',1)[-1]!='SaveKernel':return original(session,request,**kwargs)
        assert sent==0
        body=json.loads(request.body);assert body['isPrivate'] and not body['enableGpu'] and not body.get('enableTpu',False)
        assert not body.get('enableInternet',False) and body['slug']==REF
        assert session.get_adapter(request.url).max_retries.total in (0,False)
        sent+=1;write(PRIVATE/'CPU_SAVE_SEND.json',dict(request_sha256=sha(request.body if isinstance(request.body,bytes) else request.body.encode()),CPU_only=True))
        kwargs.update(timeout=180,allow_redirects=False)
        response=original(session,request,**kwargs)
        (PRIVATE/'CPU_SAVE_RESPONSE.private.json').write_bytes(response.content)
        write(PRIVATE/'CPU_SAVE_HTTP.json',dict(status=response.status_code,sha256=sha(response.content)))
        return response
    stdout,stderr=io.StringIO(),io.StringIO();previous=sys.argv;code=None
    requests.Session.send=send
    try:
        sys.argv=['kaggle','kernels','push','-p',str(folder),'-t','3600']
        with redirect_stdout(stdout),redirect_stderr(stderr):
            try:main();code=0
            except SystemExit as e:code=e.code or 0
    finally:
        requests.Session.send=original;sys.argv=previous
        (PRIVATE/'CPU_PUSH.stdout.txt').write_text(stdout.getvalue(),encoding='utf8')
        (PRIVATE/'CPU_PUSH.stderr.txt').write_text(stderr.getvalue(),encoding='utf8')
        write(PRIVATE/'CPU_CLI_RECORD.json',dict(returncode=code,SaveKernel_requests=sent,ref=REF))
    print(json.dumps(dict(returncode=code,CPU_SaveKernel_requests=sent,ref=REF)))

def read(args,label):
    folder=PRIVATE/'cli'/label;folder.mkdir(parents=True,exist_ok=False)
    r=subprocess.run(['kaggle',*args],capture_output=True,timeout=300,
        env=dict(os.environ,HTTPS_PROXY='http://127.0.0.1:7890',PYTHONIOENCODING='utf-8'))
    (folder/'stdout.txt').write_bytes(r.stdout);(folder/'stderr.txt').write_bytes(r.stderr)
    write(folder/'RECORD.json',dict(returncode=r.returncode,args=args))
    print(label,'returncode',r.returncode)

if __name__=='__main__':
    if sys.argv[1]=='push':push()
    else:read(sys.argv[2:],sys.argv[1])
