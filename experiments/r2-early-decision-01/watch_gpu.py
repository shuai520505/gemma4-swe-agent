"""Read-only monitoring/recovery of the single accepted GPU Notebook."""
import json,time
from datetime import datetime,timezone
from pathlib import Path
from kaggle import api

D=Path(__file__).resolve().parent;folder=D/'gpu-notebook'
accepted=json.loads((folder/'DISPATCH_ACCEPTANCE.json').read_bytes());ref=accepted['actual_ref']
assert accepted['SaveKernel_requests']==1
started=time.monotonic();last=None;failures=0
while time.monotonic()-started<19000:
    try:
        status=api.kernels_status(ref)
        row=status.to_dict() if hasattr(status,'to_dict') else dict(status=str(status))
        state=str(row.get('status','UNKNOWN')).split('.')[-1]
        observed=dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),actual_ref=ref,platform=row,
            real_hardware_evidence='NOT_YET_RECOVERED',SaveKernel_requests=1)
        (folder/'LATEST_PLATFORM_STATUS.json').write_text(json.dumps(observed,indent=2)+'\n')
        if state!=last:
            print(json.dumps(dict(observed_at_utc=observed['observed_at_utc'],status=state,actual_ref=ref)),flush=True);last=state
        failures=0
        if state in ('COMPLETE','ERROR','CANCEL_ACKNOWLEDGED','CANCELLED'):
            log=api.kernels_logs(ref) or '[]'
            (folder/'GPU_LOG_FINAL.json').write_text(log,encoding='utf8')
            (folder/'GPU_PLATFORM_TERMINAL.json').write_text(json.dumps(observed,indent=2)+'\n')
            q=api.quota_view().gpu_quota
            quota=dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),used_seconds=q.time_used.total_seconds(),reserved_seconds=q.time_reserved.total_seconds(),available_seconds=(q.total_time_allowed-q.time_used-q.time_reserved).total_seconds())
            (folder/'QUOTA_AFTER_TERMINAL.json').write_text(json.dumps(quota,indent=2)+'\n')
            output=D/'gpu-output';output.mkdir(exist_ok=True)
            for attempt in range(3):
                try:
                    files,_=api.kernels_output(ref,str(output),file_pattern=r'^r2a-real-gpu-01[.]zip$',page_token='',page_size=20)
                    print(json.dumps(dict(terminal=state,archives_downloaded=len(files),quota=quota)),flush=True)
                    break
                except Exception as exc:
                    print(json.dumps(dict(read_only_recovery_error=type(exc).__name__,attempt=attempt+1)),flush=True)
                    if attempt==2:raise
                    time.sleep(30)
            break
    except Exception as exc:
        failures+=1
        # Never persist exception URLs: a download error can contain a signed URL.
        (folder/'LAST_READ_ONLY_MONITOR_ERROR.json').write_text(json.dumps(dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),type=type(exc).__name__,message='Read-only API/recovery operation failed; exception text deliberately omitted',consecutive=failures),indent=2))
        print(json.dumps(dict(read_only_monitor_error=type(exc).__name__,consecutive=failures)),flush=True)
    time.sleep(60)
else:
    raise RuntimeError('MONITOR_WINDOW_ENDED_WITHOUT_TERMINAL_EVIDENCE_NO_REDISPATCH')
