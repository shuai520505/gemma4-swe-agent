"""Bounded read-only Kaggle resource/model inspection; no save or inference."""
from datetime import datetime,timezone
from decimal import Decimal
import json
import os
import subprocess

from .prepare import HERE,PRIVATE,ROOT,REF,MODEL_REF,WINDOW,write,verify_history


def duration_seconds(value):
    assert value is not None,'Missing quota duration is not zero'
    return Decimal(value.days*86400+value.seconds)+Decimal(value.microseconds)/1000000


def run():
    binding=verify_history()
    os.environ.update(HTTPS_PROXY='http://127.0.0.1:7890',PYTHONIOENCODING='utf-8')
    from kaggle.api.kaggle_api_extended import KaggleApi
    from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelSessionStatusRequest
    api=KaggleApi();api.authenticate()
    dest=PRIVATE/'preflight'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    dest.mkdir(parents=True,exist_ok=False)
    quota=api.quota_view();raw=json.loads(quota.to_json())
    write(dest/'QUOTA.json',raw)
    # Installed SDK to_json incorrectly renders fractional timedeltas as e.g.
    # 2269.744.0s. Preserve that serialization privately, and calculate exactly
    # from its parsed timedelta fields without reparsing the malformed string.
    seconds=duration_seconds
    q=quota.gpu_quota
    gpu={key:str(seconds(value)) for key,value in (
        ('total_seconds',q.total_time_allowed),('used_seconds',q.time_used),('reserved_seconds',q.time_reserved))}
    remaining=seconds(q.total_time_allowed)-seconds(q.time_used)-seconds(q.time_reserved)
    result=dict(queried_UTC=datetime.now(timezone.utc).isoformat(),source_binding=binding,raw_gpu_quota=gpu,
                remaining_report_seconds=str(remaining),GPU_reserved_seconds=str(seconds(q.time_reserved)),
                requested_window_seconds=WINDOW,planned_resource_floor_report_seconds=4*WINDOW+1200,
                quota_gate=remaining>=4*WINDOW+1200 and seconds(q.time_reserved)==0,
                actual_GPU_allocation='NOT_YET_ALLOCATED',max_dispatches=1,planned_sessions=2)
    write(HERE/'DYNAMIC_PREFLIGHT.json',result)
    print(json.dumps(dict(remaining_report_seconds=str(remaining),reserved_report_seconds=str(seconds(q.time_reserved)),quota_gate=result['quota_gate'])),flush=True)
    if not result['quota_gate']:return result
    command=['kaggle','kernels','list','--mine','--sort-by','dateRun','--page-size','10','--csv']
    recent=subprocess.run(command,capture_output=True,timeout=120)
    (dest/'recent.csv').write_bytes(recent.stdout);(dest/'recent.stderr').write_bytes(recent.stderr)
    assert recent.returncode==0,'Recent jobs unreadable'
    import csv,io
    text=recent.stdout.decode('utf8');rows=list(csv.DictReader(io.StringIO(text[text.index('ref,'):])))
    states=[]
    with api.build_kaggle_client() as client:
        for row in rows:
            owner,slug=row['ref'].split('/');request=ApiGetKernelSessionStatusRequest()
            request.user_name=owner;request.kernel_slug=slug
            status=client.kernels.kernels_api_client.get_kernel_session_status(request)
            states.append(dict(ref=row['ref'],status=status.status.name))
    result['recent_states']=states
    result['conflict_gate']=all(r['status'] in ('COMPLETE','ERROR','CANCELLED') for r in states)
    files=api.model_instance_version_files(MODEL_REF,page_size=100)
    write(dest/'MODEL_METADATA.json',json.loads(files.to_json()))
    expected=json.loads((ROOT/'u_re/v01/experiments/gemma_smoke_01/MODEL_RUNTIME_CONFIG.json').read_bytes())
    result['model_source']=MODEL_REF
    result['model_available_names']=[f.name for f in files.files]
    result['model_names_gate']=not files.next_page_token and set(result['model_available_names'])==set(expected['model_files'])
    result['model_actual_hashes']='VERIFY_MOUNTED_BYTES_BEFORE_INFERENCE'
    unused=subprocess.run(['kaggle','kernels','list','--mine','--search',REF.split('/')[1],'--page-size','100','--csv'],capture_output=True,timeout=120)
    (dest/'slug.csv').write_bytes(unused.stdout)
    result['slug_unused']=unused.returncode==0 and REF.encode() not in unused.stdout
    result['static_read_GO']=result['quota_gate'] and result['conflict_gate'] and result['model_names_gate'] and result['slug_unused']
    result['preflight_private_record']=str(dest)
    write(HERE/'DYNAMIC_PREFLIGHT.json',result)
    print(json.dumps({k:result[k] for k in ('static_read_GO','model_names_gate','conflict_gate','slug_unused')}))
    return result


if __name__=='__main__':run()
