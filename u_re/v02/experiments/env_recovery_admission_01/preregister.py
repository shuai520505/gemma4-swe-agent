"""Freeze carry decision and untouched candidate order before recovery outcomes."""
import json
from .dependencies import HERE,ROOT,ID,sha,write

def initial():
    prior=ROOT/'u_re/v02/experiments/action_first_replication_01'
    pool=json.loads((prior/'TASK_POOL_FREEZE.json').read_bytes())
    ledger=json.loads((prior/'TASK_ADMISSION_LEDGER.json').read_bytes())
    observed={r['instance_id'] for r in ledger['rows'] if r['status']!='NOT_RUN'}
    assert observed=={'fastapi_14851','fastapi_14246','fastapi_5077','fastapi_14077','fastapi_14609'}
    unseen=[r for r in pool['ranked_rows'] if r['instance_id'] not in observed]
    assert len(unseen)==29 and len(pool['excluded_ids'])==95
    source_files=['TASK_POOL_FREEZE.json','TASK_ADMISSION_LEDGER.json','SELECTED_TASKS.json','REPLICATION_PROTOCOL.json']
    write(HERE/'TASK_POOL_FREEZE.json',dict(experiment_id=ID,scope='SAME_REPOSITORY_REPLICATION',inherited_excluded_ids=pool['excluded_ids'],inherited_exclusions_count=95,prior_observed_ids=sorted(observed),new_model_or_reference_exposure_found=[],carry='fastapi_5077',carry_policy='CARRIED_FORWARD_BASELINE_ELIGIBLE only if discriminating native baseline survives frozen environment migration; never count as newly discovered',diagnostic_only=['fastapi_14851','fastapi_14246','fastapi_14077','fastapi_14609'],ranked_rows=unseen,next_max24_in_order=unseen[:24],max_new_checks=24,target_total=4,target_new_if_carry_valid=3,ranking='Preserve exact PR25 full frozen34 order, remove5 previously observed. Do not rehash/reorder. User explicitly permits29 NOT_RUN identities; all95 older exclusions retained.',sources={str((prior/n).relative_to(ROOT)):sha((prior/n).read_bytes()) for n in source_files},source_base='6f6b7500baa007ee317466b93329ce99cf58950e',history_scope='PR25 actual head, inherited79 plus both prior8 reservations; no subsequent model runs or reference reads in current tracked tree. Unrecorded exposure unknown.'))
    write(HERE/'RECOVERY_PROTOCOL.json',dict(experiment_id=ID,status='DIAGNOSTIC_PRECOMMIT_NOT_NEW_SCREENING',carry_decision='Carry5077 pending environment migration evidence, decided before recovery and new screening',diagnostic_tasks=['fastapi_14246','fastapi_14609'],runs='Both original empty-patch native baselines before installing extras; then exactly fixed verified artifacts, dependency closure/negative canary and recovered native baselines;5077 migration check. All original inputs/tests/Verifier unchanged.',new_task_baselines_before_environment_lock=0,artifact_manifest_sha256=sha((HERE/'NEW_DEPENDENCIES.json').read_bytes()),test_mutation='Forbidden including snapshot auto-update. Detect source/config/test hash drift and STOP.',reference_patch='Forbidden; only original Issue, frozen base source, actual tracebacks and evaluator results on trusted side',GPU_authorized=False,formal_submission=False))

if __name__=='__main__':initial()
