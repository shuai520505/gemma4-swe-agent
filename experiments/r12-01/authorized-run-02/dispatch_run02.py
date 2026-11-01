"""Authenticated CLI dispatch, one durable claim, one SaveKernel, no retries."""
import hashlib,io,json,os,socket,sys
from contextlib import redirect_stdout,redirect_stderr
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
WORK=Path(__file__).parent;folder=WORK
from r12_dispatch_guard_v02 import pre_dispatch,require_quota
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((folder/'BUILD.json').read_bytes());meta=json.loads((folder/'kernel-metadata.json').read_bytes())
receipt=json.loads((folder/'GPU_AUTHORIZATION.json').read_bytes())
pre_dispatch(folder,build,receipt)
assert sha(folder/'GPU_AUTHORIZATION.json')==build['authorization_sha256']
assert meta['competition_sources']==['gemma-4-developer-agent'] and meta['model_sources']==['google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2']
try:
 with socket.create_connection(('127.0.0.1',7890),timeout=1):os.environ['HTTPS_PROXY']='http://127.0.0.1:7890'
except OSError:pass
from kaggle import api
from kaggle.cli import main as cli
import requests
assert api.get_config_value('username')==meta['id'].split('/')[0]
q=api.quota_view().gpu_quota
quota=dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),total_seconds=q.total_time_allowed.total_seconds(),used_seconds=q.time_used.total_seconds(),reserved_seconds=q.time_reserved.total_seconds(),available_seconds=(q.total_time_allowed-q.time_used-q.time_reserved).total_seconds(),required_seconds=73200)
(folder/'QUOTA_IMMEDIATELY_BEFORE_DISPATCH.json').write_text(json.dumps(quota,indent=2));require_quota(quota['available_seconds'],18000)
evidence=folder/'dispatch';evidence.mkdir(exist_ok=False)
with (evidence/'ONE_SHOT_CLAIM.json').open('x') as f:
 json.dump(dict(build,claimed_at_utc=datetime.now(timezone.utc).isoformat(),maximum_SaveKernel_requests=1,retry_forbidden=True),f);f.flush();os.fsync(f.fileno())
sent=0;original=requests.Session.send
def send(session,request,**kwargs):
 global sent
 if urlsplit(request.url).path.rsplit('/',1)[-1]=='SaveKernel':
  assert sent==0,'SECOND_GPU_DISPATCH_FORBIDDEN'
  body=json.loads(request.body)
  assert body['enableGpu'] and body['isPrivate'] and not body.get('enableTpu') and not body.get('enableInternet') and body['slug']==meta['id']
  assert session.get_adapter(request.url).max_retries.total in (0,False)
  sent+=1;kwargs.update(timeout=180,allow_redirects=False)
  (evidence/'REQUEST_SENT.json').write_text(json.dumps(dict(sent_at_utc=datetime.now(timezone.utc).isoformat(),request_number=sent,ref=meta['id'],GPU=True,maximum_seconds=18000)))
  response=original(session,request,**kwargs)
  (evidence/'response.private.json').write_bytes(response.content)
  (evidence/'HTTP.json').write_text(json.dumps(dict(status=response.status_code)))
  return response
requests.Session.send=send;out,err=io.StringIO(),io.StringIO();code=None
try:
 sys.argv=['kaggle','-W','kernels','push','-p',str(folder),'-t','18000']
 with redirect_stdout(out),redirect_stderr(err):
  try:cli();code=0
  except SystemExit as e:code=e.code or 0
finally:
 requests.Session.send=original
 (evidence/'stdout.txt').write_text(out.getvalue(),encoding='utf8');(evidence/'stderr.txt').write_text(err.getvalue(),encoding='utf8')
 record=dict(ref=meta['id'],SaveKernel_requests=sent,returncode=code,retry_forbidden=True,window_seconds=18000)
 (evidence/'DISPATCH_RECORD.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
print(out.getvalue()[:1800],flush=True);print(err.getvalue()[:1800],flush=True)
