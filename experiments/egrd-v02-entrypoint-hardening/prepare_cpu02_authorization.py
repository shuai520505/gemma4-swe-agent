"""Record the actual subsequent human confirmation; no network call."""
import json
from pathlib import Path
D=Path(__file__).resolve().parent
b=json.loads((D/'cpu-recheck-prepared/BUILD.json').read_bytes())
auth=dict(user_answer='允许CPU和GPU',scope='One CPU02-only recheck; GPU authorization recorded separately and subject to CPU pass',GPU=False,TPU=False,maximum_SaveKernel_requests=1,notebook_sha256=b['notebook_sha256'])
with (D/'CPU02_AUTHORIZATION.json').open('x',encoding='utf8') as f:json.dump(auth,f,ensure_ascii=False,indent=2)
s=(D/'dispatch_cpu_once.py').read_text(encoding='utf8').replace("F=D/'cpu-notebook'","F=D/'cpu-recheck-prepared'").replace("D/'CPU_AUTHORIZATION.json'","D/'CPU02_AUTHORIZATION.json'").replace('允许一次 CPU-only SaveKernel，仍禁止 GPU','允许CPU和GPU').replace('egrd-v02-cpu-hardening01','egrd-v02-cpu-hardening02')
(D/'dispatch_cpu02_once.py').write_text(s,encoding='utf8')
