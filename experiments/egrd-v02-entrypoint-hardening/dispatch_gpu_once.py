"""One authorized, CPU-gated model smoke; no retries or competition submission."""
import argparse,hashlib,io,json,os,sys
from contextlib import redirect_stdout,redirect_stderr
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
D=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--model',choices=['12b','31b'],required=True);args=p.parse_args()
F=D/('gpu-'+args.model+'-prepared')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((F/'DISPATCH_CONFIG.json').read_bytes());meta=json.loads((F/'kernel-metadata.json').read_bytes());auth=json.loads((F/'GPU_AUTHORIZATION.json').read_bytes())
assert build['CPU_passed'] is True and build['authorization_embedded'] is True
assert auth['explicit_GPU_confirmation'] is True and auth['user_answer']=='允许CPU和GPU' and auth['model']==args.model
assert auth['maximum_dispatches']==1 and auth['retries']==0 and auth['formal_submission'] is False
assert sha(F/'study.ipynb')==build['notebook_sha256'] and sha(F/'kernel-metadata.json')==build['metadata_sha256']
assert meta['enable_gpu'] is True and meta['enable_tpu'] is False and meta['is_private'] is True and meta['enable_internet'] is False
assert meta['machine_shape']=='NvidiaL4' and meta['model_sources']==[json.loads((D/'MODEL_CONFIGURATIONS.json').read_bytes())[args.model]['mount']]
assert json.loads((D/'cpu02-evidence/CPU_SUMMARY.json').read_bytes())['status']=='PASS'
from result_contract import native_execution_check
assert native_execution_check(D/'cpu02-evidence/worker/trusted/NATIVE_RESULT.json')['passed'],'NATIVE_ENVIRONMENT_BLOCKED_NO_GPU_DISPATCH'
if args.model=='31b':
 decision=json.loads((D/'gpu12-evidence/execution/AGGREGATE_RESULT.json').read_bytes())
 assert decision['model_decision']=='REQUEST_31B_FALLBACK_CONFIRMATION' and decision['complete'] and decision['children_trusted']
 assert json.loads((D/'gpu12-evidence/execution/CLEANUP.json').read_bytes())['complete'] is True
from kaggle import api
from kaggle.cli import main as cli
import requests
assert api.get_config_value('username')==meta['id'].split('/')[0]
assert not any(getattr(r,'ref','')==meta['id'] for r in api.kernels_list(mine=True,search=meta['id'].split('/')[-1],page_size=100))
q=api.quota_view().gpu_quota
quota=dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),total_seconds=q.total_time_allowed.total_seconds(),used_seconds=q.time_used.total_seconds(),reserved_seconds=q.time_reserved.total_seconds(),available_seconds=(q.total_time_allowed-q.time_used-q.time_reserved).total_seconds(),required_seconds=73200,capacity='CAPACITY_UNVERIFIED_UNTIL_ACTUAL_ALLOCATION')
(F/'QUOTA_IMMEDIATELY_BEFORE_DISPATCH.json').write_text(json.dumps(quota,indent=2))
assert quota['available_seconds']>=73200,'RESOURCE_BLOCKED_NO_DISPATCH'
E=F/'dispatch';E.mkdir(exist_ok=False)
with (E/'ONE_SHOT_CLAIM.json').open('x') as f:
 json.dump(dict(notebook_sha256=build['notebook_sha256'],authorization_sha256=sha(F/'GPU_AUTHORIZATION.json'),claimed_at_utc=datetime.now(timezone.utc).isoformat(),maximum_SaveKernel_requests=1,retry=False),f);f.flush();os.fsync(f.fileno())
sent=0;original=requests.Session.send
def send(session,request,**kwargs):
 global sent
 if urlsplit(request.url).path.rsplit('/',1)[-1]=='SaveKernel':
  assert sent==0;body=json.loads(request.body)
  assert body['enableGpu'] and not body.get('enableTpu') and body['isPrivate'] and not body.get('enableInternet') and body['slug']==meta['id']
  assert session.get_adapter(request.url).max_retries.total in (0,False)
  sent+=1;kwargs.update(timeout=180,allow_redirects=False)
  (E/'REQUEST_SENT.json').write_text(json.dumps(dict(request=sent,ref=meta['id'],GPU=True,maximum_seconds=18000)))
  response=original(session,request,**kwargs);(E/'response.private.json').write_bytes(response.content)
  (E/'HTTP.json').write_text(json.dumps(dict(status=response.status_code)));return response
 return original(session,request,**kwargs)
requests.Session.send=send;out=io.StringIO();err=io.StringIO();code=None
try:
 sys.argv=['kaggle','-W','kernels','push','-p',str(F),'-t','18000']
 with redirect_stdout(out),redirect_stderr(err):
  try:cli();code=0
  except SystemExit as e:code=e.code or 0
finally:
 requests.Session.send=original
 (E/'stdout.private.txt').write_text(out.getvalue(),encoding='utf8');(E/'stderr.private.txt').write_text(err.getvalue(),encoding='utf8')
 r=dict(ref=meta['id'],SaveKernel_requests=sent,returncode=code,retry=False,GPU=True,formal_submission=False)
 (E/'DISPATCH_RECORD.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
assert sent==1 and code==0,'DISPATCH_NOT_CONFIRMED_NO_RETRY'
