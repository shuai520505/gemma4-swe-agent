"""One specifically confirmed CPU SaveKernel; GPU remains prohibited."""
import hashlib,io,json,os,sys
from pathlib import Path
from contextlib import redirect_stdout,redirect_stderr
from urllib.parse import urlsplit
D=Path(__file__).resolve().parent;F=D/'cpu-notebook'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((F/'BUILD.json').read_bytes());meta=json.loads((F/'kernel-metadata.json').read_bytes());auth=json.loads((D/'CPU_AUTHORIZATION.json').read_bytes())
assert auth['GPU'] is False and auth['TPU'] is False and auth['maximum_SaveKernel_requests']==1 and auth['user_answer']=='允许一次 CPU-only SaveKernel，仍禁止 GPU'
assert auth['notebook_sha256']==build['notebook_sha256']==sha(F/'study.ipynb')
assert build['metadata_sha256']==sha(F/'kernel-metadata.json') and meta['enable_gpu'] is False and meta['enable_tpu'] is False and meta['model_sources']==[]
from kaggle import api
from kaggle.cli import main as cli
import requests
assert api.get_config_value('username')==meta['id'].split('/')[0]
existing=api.kernels_list(mine=True,search='egrd-v02-cpu-hardening01',page_size=100)
assert not any(getattr(r,'ref','')==meta['id'] for r in existing),'Do not overwrite a historical Notebook'
E=F/'dispatch';E.mkdir(exist_ok=False)
with (E/'ONE_SHOT_CLAIM.json').open('x',encoding='utf8') as f:
 json.dump(dict(notebook_sha256=build['notebook_sha256'],metadata_sha256=build['metadata_sha256'],CPU=True,GPU=False,TPU=False,maximum_SaveKernel_requests=1,retry=False),f);f.flush();os.fsync(f.fileno())
sent=0;original=requests.Session.send

def send(session,request,**kwargs):
 global sent
 if urlsplit(request.url).path.rsplit('/',1)[-1]=='SaveKernel':
  assert sent==0;body=json.loads(request.body)
  assert not body.get('enableGpu') and not body.get('enableTpu') and body['isPrivate'] and not body.get('enableInternet')
  assert session.get_adapter(request.url).max_retries.total in (0,False)
  sent+=1;(E/'REQUEST_SENT.json').write_text(json.dumps(dict(request=sent,CPU=True,GPU=False,ref=meta['id'])))
  kwargs.update(timeout=180,allow_redirects=False);response=original(session,request,**kwargs)
  (E/'response.private.json').write_bytes(response.content)
  (E/'HTTP.json').write_text(json.dumps(dict(status=response.status_code)));return response
 return original(session,request,**kwargs)
requests.Session.send=send;out=io.StringIO();err=io.StringIO();code=None
try:
 sys.argv=['kaggle','-W','kernels','push','-p',str(F),'-t','3600']
 with redirect_stdout(out),redirect_stderr(err):
  try:cli();code=0
  except SystemExit as e:code=e.code or 0
finally:
 requests.Session.send=original
 (E/'stdout.private.txt').write_text(out.getvalue(),encoding='utf8');(E/'stderr.private.txt').write_text(err.getvalue(),encoding='utf8')
 record=dict(CPU=True,GPU=False,TPU=False,SaveKernel_requests=sent,returncode=code,ref=meta['id'],retry=False);(E/'DISPATCH_RECORD.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
assert sent==1 and code==0,'CPU dispatch not confirmed; do not retry'
