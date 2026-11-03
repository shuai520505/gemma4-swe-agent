"""One durable claim and one authenticated Kaggle SaveKernel. No retry."""
import hashlib,io,json,os,sys
from contextlib import redirect_stdout,redirect_stderr
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit

D=Path(__file__).resolve().parent;folder=D/'gpu-notebook'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((folder/'BUILD.json').read_bytes());meta=json.loads((folder/'kernel-metadata.json').read_bytes())
for name,field in [('study.ipynb','notebook_sha256'),('kernel-metadata.json','metadata_sha256'),('GPU_AUTHORIZATION.json','authorization_sha256')]:assert sha(folder/name)==build[field],name
assert build['maximum_dispatches']==1 and build['maximum_seconds']==18000
assert meta['id']=='wudangdexiaodoashi/egrd-v01-12b-pilot01' and meta['enable_gpu'] and not meta['enable_internet']
assert meta['machine_shape']=='NvidiaL4' and meta['is_private'] and not meta.get('enable_tpu')
assert meta['model_sources']==['google/gemma-4/Other/gemma-4-12b-it-qat-w4a16-ct/2','google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2']
auth=json.loads((folder/'GPU_AUTHORIZATION.json').read_bytes())
assert auth['maximum_dispatches']==1 and not auth['formal_submission'] and auth['actual_four_L4_required']
from kaggle import api
from kaggle.cli import main as cli
import requests
assert api.get_config_value('username')==meta['id'].split('/')[0]
existing=api.kernels_list(mine=True,search='egrd-v01-12b-pilot01',page_size=100)
assert not any(str(getattr(k,'ref',''))==meta['id'] for k in existing),'EXISTING_NOTEBOOK_MUST_NOT_BE_OVERWRITTEN'
q=api.quota_view().gpu_quota
quota=dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),total_seconds=q.total_time_allowed.total_seconds(),used_seconds=q.time_used.total_seconds(),reserved_seconds=q.time_reserved.total_seconds(),available_seconds=(q.total_time_allowed-q.time_used-q.time_reserved).total_seconds(),required_seconds=73200)
(folder/'QUOTA_IMMEDIATELY_BEFORE_DISPATCH.json').write_text(json.dumps(quota,indent=2))
assert quota['available_seconds']>=73200,'RESOURCE_BLOCKED_NO_DISPATCH'
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
 return original(session,request,**kwargs)
requests.Session.send=send;out,err=io.StringIO(),io.StringIO();code=None
try:
 sys.argv=['kaggle','-W','kernels','push','-p',str(folder),'-t','18000']
 with redirect_stdout(out),redirect_stderr(err):
  try:cli();code=0
  except SystemExit as e:code=e.code or 0
finally:
 requests.Session.send=original
 (evidence/'stdout.private.txt').write_text(out.getvalue(),encoding='utf8');(evidence/'stderr.private.txt').write_text(err.getvalue(),encoding='utf8')
 record=dict(ref=meta['id'],SaveKernel_requests=sent,returncode=code,retry_forbidden=True,window_seconds=18000)
 (evidence/'DISPATCH_RECORD.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
assert sent==1 and code==0,'DISPATCH_NOT_CONFIRMED_NO_RETRY'
