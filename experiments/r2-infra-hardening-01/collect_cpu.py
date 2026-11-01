"""Read-only terminal recovery; no kernel push or model access."""
import json,sys
from datetime import datetime,timezone
from pathlib import Path
from kaggle import api
D=Path(__file__).resolve().parent
label=sys.argv[1];out=D/label;out.mkdir(exist_ok=True)
ref='wudangdexiaodoashi/r2-infrastructure-cpu-hardening-01'
status=api.kernels_status(ref);v=status.to_dict();state=str(v.get('status','UNKNOWN')).split('.')[-1]
receipt=dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),ref=ref,platform=v,CPU_only=True)
(out/'PLATFORM_STATUS.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt),flush=True)
if state in ['COMPLETE','ERROR']:
    (out/'PLATFORM_LOG.json').write_text(api.kernels_logs(ref) or '[]',encoding='utf8')
    files,_=api.kernels_output(ref,str(out),file_pattern=r'^r2-infra-cpu-hardening-01[.]zip$',page_token='',page_size=20)
    print(json.dumps(dict(downloaded=len(files))),flush=True)
