"""Read current CPU-only Notebook logs and preserve versioned final summary."""
import json,sys
from pathlib import Path
from kaggle import api
D=Path(__file__).resolve().parent
version=int(sys.argv[1]); ref='wudangdexiaodoashi/r2a-native-cpu-admission-01'
raw=api.kernels_logs(ref) or '[]'
(D/'cpu-notebook'/f'LATEST_LOG_V{version}.json').write_text(raw,encoding='utf8')
found=[]
for row in json.loads(raw):
    if row.get('stream_name')!='stdout':continue
    for line in row.get('data','').splitlines():
        if line.startswith('R2A_CPU_ADMISSION '):found.append(json.loads(line.split(' ',1)[1]))
if found:
    final=found[-1]
    (D/f'CPU_ATTEMPT_{version:02d}_SUMMARY.json').write_text(json.dumps(final,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(status=final['status'],worker_returncode=final.get('worker_returncode'),reason=final.get('reason'),rows=[dict(task=r['task'],status=r['status'],error=r.get('error')) for r in final.get('admission',{}).get('rows',[])],replay=final.get('plumbing_replay'))))
else:print('FINAL_SUMMARY_NOT_AVAILABLE')
print(api.kernels_status(ref))
