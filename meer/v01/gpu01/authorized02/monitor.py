"""Finite CLI status/log snapshots of a confirmed version; no outcome unblinding."""
from datetime import datetime,timezone
import json,re
from .cli_control import cli,location
from .read_preflight import PRIVATE,save

def snapshot(batch,logs=False):
    directory,_,_=location(batch)
    binding=json.loads((directory/'ACTUAL_RESOURCE_BINDING.json').read_bytes())
    ref=binding['actual_ref']
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    private=PRIVATE/f'batch{batch:02d}/live'/stamp;private.mkdir(parents=True)
    result=cli(['kernels','status',ref]);save(private/'CLI_STATUS.json',result)
    m=re.search(r'KernelWorkerStatus\.(\w+)',result['stdout'])
    status=m[1] if result['exit_code']==0 and m else 'UNKNOWN_READ_FAILURE'
    summary=dict(batch=batch,Notebook_id=binding['Notebook_id'],version=1,actual_ref=ref,status=status,queried_utc=datetime.now(timezone.utc).isoformat())
    if logs:
        result=cli(['kernels','logs',ref]);save(private/'CLI_LOGS.json',result)
        text=result['stdout']
        summary.update(log_read_exit=result['exit_code'],log_characters=len(text),
            started_session_markers=text.count('REAL_GEMMA_RUN_START'),
            ended_session_markers=text.count('REAL_GEMMA_RUN_END'),
            model_server_ready_marker=bool(re.search(r'Application startup complete|Starting vLLM API server',text)),
            no_native_outcome_values_exposed_to_relevance_reviewer=True)
    save(directory/'status_observations'/f'{stamp}.json',summary)
    print(json.dumps(summary))
    return summary

if __name__=='__main__':
    import sys
    snapshot(int(sys.argv[1]),'logs' in sys.argv[2:])
