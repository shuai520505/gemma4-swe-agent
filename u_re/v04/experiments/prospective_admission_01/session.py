"""Same EGR production coordinator with new admitted identities and PR26 reader."""
import inspect,json
from pathlib import Path
from .common import HERE,ROOT,PACKAGE,sha
from u_re.v02.experiments.env_recovery_admission_01.runtime import native,install_extras,fingerprint

async def native_baseline(data,task,frozen,output):
    keys=('instance_id','repo','base_commit','issue_sha256','task_record_sha256','test_patch_sha256','input_files')
    evidence,audit=await native(data,task.instance_id,output,{k:frozen[k] for k in keys})
    assert evidence['evidence_ok'] and evidence['counts']==frozen['native_baseline_counts'] and evidence['native_resolved'] is False
    assert audit['category']=='assertion_failure' and not audit['infrastructure_stop']
    if evidence['counts']['errors']:
        assert audit['snapshot_assertion_teardown_proven'] and audit['environment_errors']==0 and audit['duplicate_snapshot_finalizer_errors']==evidence['counts']['errors']
    capture=json.loads((Path(output)/'phase2_junit_capture.json').read_bytes())
    return dict(eligible=True,production_source_hashes=capture['production_source_hashes'])

def coordinator(lock,grant):
    from u_re.v04.experiments.evidence_guided_repair_01 import session as accepted
    code=inspect.getsource(accepted.coordinator)
    anchor='    namespace=dict(prior.__dict__'
    assert code.count(anchor)==1
    code=code.replace(anchor,"    code=code.replace(\"['fastapi_5077','fastapi_11355']\",repr([t['instance_id'] for t in lock['tasks']]))\n"+anchor)
    code=code.replace('V04_EGR_PAYLOAD_END_TO_END_CPU_PASS','V04_PROSPECTIVE_PAYLOAD_END_TO_END_CPU_PASS')
    code=code.replace('V04_EGR_GPU_NOT_AUTHORIZED','V04_EGR_REAL_GEMMA_ABBA_COMPLETE')
    namespace=dict(accepted.__dict__,HERE=HERE,ROOT=ROOT,PACKAGE=PACKAGE)
    exec(compile(code,'<Reused-EGR-new-admitted-task-coordinator>','exec'),namespace)
    fn=namespace['coordinator'](lock,grant);fn.__globals__['native_baseline']=native_baseline
    return fn

async def run(output,session_started,*,mode='CPU_DRY_RUN',cpu_transport=None,quota_at_dispatch=None,authorization=None):
    assert mode in ('CPU_DRY_RUN','GPU')
    lock=json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    if mode=='GPU':
        assert cpu_transport is None and authorization and authorization.get('GPU_authorized') is True,'New independent GPU authorization required'
        assert authorization['experiment_id']==lock['experiment_id'] and authorization['order']==lock['order']
        assert authorization['task_lock_sha256']==sha((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
        # The original ZIP is decoded/extracted by the Notebook, not embedded
        # recursively into itself. Bind to its setup-generated identity record.
        payload_identity=json.loads((Path(output).parent/'PAYLOAD_IDENTITY.json').read_bytes())
        assert payload_identity['production_entry']==PACKAGE+'.session.run'
        assert authorization['payload_sha256']==payload_identity['payload_sha256']
        assert authorization['environment_lock_sha256']==lock['environment_lock_sha256']
        assert authorization['arms']==lock['arms'] and authorization['model_files']==lock['model']['files']
        assert authorization['max_SaveKernel_dispatches']==1 and authorization['max_Agent_runs']==4
        assert authorization['GPU_count']==4 and authorization['GPU_type']=='NVIDIA L4' and authorization['TP']==4
        assert authorization['Agent_seconds']==300 and authorization['platform_window_seconds']==10000
        grant=dict(authorization,quota_at_dispatch_report_seconds=quota_at_dispatch)
    else:
        assert cpu_transport is not None
        grant=dict(GPU_authorized=False,order=lock['order'],Agent_seconds=300,platform_window_seconds=10000)
    from harness_v2.evidence import atomic_json
    environment=json.loads((HERE/'ENVIRONMENT_LOCK.json').read_bytes())
    before=install_extras(Path(output).parent/'environment');assert before==environment['fingerprint']
    atomic_json(Path(output).parent/'PRODUCTION_ENVIRONMENT_BEFORE.json',before)
    await coordinator(lock,grant)(output,session_started,mode=mode,cpu_transport=cpu_transport,quota_at_dispatch=quota_at_dispatch)
    assert fingerprint()==before
    atomic_json(Path(output).parent/'PRODUCTION_ENVIRONMENT_AFTER.json',fingerprint())
