"""Read-only evidence recovery; no dispatch or retry."""
import argparse,hashlib,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
from kaggle import api
D=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--model',choices=['12b','31b'],required=True);args=p.parse_args()
slug='egrd-v02-'+args.model+'-smoke01';ref='wudangdexiaodoashi/'+slug
out=D/('gpu'+args.model.removesuffix('b')+'-output');out.mkdir(exist_ok=True)
status=api.kernels_status(ref).to_dict()['status']
r=dict(ref=ref,version=1,status=status,observed_at_utc=datetime.now(timezone.utc).isoformat())
(out/'PLATFORM.json').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
if status in ['COMPLETE','ERROR','CANCELLED']:
 (out/'LOG.private.json').write_text(api.kernels_logs(ref) or '[]')
 api.kernels_output(ref,str(out),file_pattern='^'+slug+'[.]zip$',page_token='',page_size=20)
 q=api.quota_view().gpu_quota
 (out/'QUOTA_AFTER.json').write_text(json.dumps(dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),total_seconds=q.total_time_allowed.total_seconds(),used_seconds=q.time_used.total_seconds(),reserved_seconds=q.time_reserved.total_seconds(),available_seconds=(q.total_time_allowed-q.time_used-q.time_reserved).total_seconds()),indent=2))
 archive=out/(slug+'.zip')
 if archive.exists():
  evidence=D/('gpu'+args.model.removesuffix('b')+'-evidence');evidence.mkdir(exist_ok=True)
  with zipfile.ZipFile(archive) as z:
   assert z.testzip() is None
   assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
   z.extractall(evidence)
  receipt=dict(sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size)
  (out/'ARCHIVE.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
 else:print('EVIDENCE_ARCHIVE_MISSING')
