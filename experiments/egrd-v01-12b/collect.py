"""Read-only recovery of the single accepted pilot; never dispatches/retries."""
import argparse,hashlib,json,time,zipfile
from datetime import datetime,timezone
from pathlib import Path
from kaggle import api
D=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--watch',action='store_true');args=p.parse_args()
accepted=json.loads((D/'evidence/GPU_DISPATCH_ACCEPTANCE.json').read_bytes())
ref=accepted['url'].split('/code/')[1];assert accepted['SaveKernel_requests']==1
out=D/'gpu-output';out.mkdir(exist_ok=True);last=None
for attempt in range(650 if args.watch else 1):
 try:
  status=api.kernels_status(ref).to_dict()['status'];stamp=datetime.now(timezone.utc).isoformat()
  (out/'STATUS.latest.json').write_text(json.dumps(dict(status=status,observed_at_utc=stamp,ref=ref)))
  if status!=last:print(json.dumps(dict(status=status,observed_at_utc=stamp)),flush=True);last=status
  if status in ['COMPLETE','ERROR','CANCELLED']:
   (out/'PLATFORM.json').write_text(json.dumps(dict(status=status,observed_at_utc=stamp,ref=ref,version=accepted['version']),indent=2))
   (out/'LOG.private.json').write_text(api.kernels_logs(ref) or '[]')
   files,_=api.kernels_output(ref,str(out),file_pattern='^egrd-v01-12b-pilot01[.]zip$',page_token='',page_size=20)
   q=api.quota_view().gpu_quota
   (out/'QUOTA_AFTER.json').write_text(json.dumps(dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),total_seconds=q.total_time_allowed.total_seconds(),used_seconds=q.time_used.total_seconds(),reserved_seconds=q.time_reserved.total_seconds(),available_seconds=(q.total_time_allowed-q.time_used-q.time_reserved).total_seconds()),indent=2))
   archive=out/'egrd-v01-12b-pilot01.zip'
   if archive.exists():
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(json.dumps(dict(recovered=True,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size)),flush=True)
   else:print('MISSING_ARCHIVE',flush=True)
   break
 except Exception as exc:
  with (out/'RECOVERY_ERRORS.jsonl').open('a') as f:f.write(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),type=type(exc).__name__,reason=str(exc)))+'\n')
  print('RECOVERY_READ_ERROR '+type(exc).__name__,flush=True)
 if args.watch:time.sleep(30)
