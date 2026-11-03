"""Read-only recovery of the one authorized CPU run. Never dispatches."""
import hashlib,json,zipfile,argparse
from datetime import datetime,timezone
from pathlib import Path
from kaggle import api
D=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--run',choices=['01','02'],default='01');args=p.parse_args()
slug='egrd-v02-cpu-hardening'+args.run
ref='wudangdexiaodoashi/'+slug
out=D/('cpu-output' if args.run=='01' else 'cpu02-output');out.mkdir(exist_ok=True)
stamp=datetime.now(timezone.utc).isoformat()
status=api.kernels_status(ref).to_dict()['status']
record=dict(ref=ref,version=1,status=status,observed_at_utc=stamp,GPU=False)
(out/'PLATFORM.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record),flush=True)
if status in ['COMPLETE','ERROR','CANCELLED']:
 (out/'LOG.private.json').write_text(api.kernels_logs(ref) or '[]')
 api.kernels_output(ref,str(out),file_pattern='^'+slug+'[.]zip$',page_token='',page_size=20)
 archive=out/(slug+'.zip')
 if archive.exists():
  with zipfile.ZipFile(archive) as z:
   assert z.testzip() is None
   assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
   evidence=D/('cpu-evidence' if args.run=='01' else 'cpu02-evidence');evidence.mkdir(exist_ok=True)
   z.extractall(evidence)
  receipt=dict(archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size)
  (out/'ARCHIVE.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
 else:print('EVIDENCE_ARCHIVE_MISSING')
