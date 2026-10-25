"""Publish whitelist-only summaries from already reviewed private evidence.

No network, model, runner, evaluator or candidate mutation. Run once after audit.
"""
import json
from .read_preflight import HERE, save


def main():
    first=json.loads((HERE/'BATCH_01_EXECUTION.json').read_bytes())
    measured=json.loads((HERE/'BATCH_02_DERIVED_METRICS.json').read_bytes())
    audited=json.loads((HERE/'BATCH_02_RUNTIME_AUDIT.json').read_bytes())
    rows=list(first['runs'])
    for m,n in zip(measured['sessions'],audited['native_results']):
        rows.append(dict(run=n['run'],instance_id=n['instance_id'],arm=n['arm'],
            status='COMPLETE_NATIVE_NEGATIVE',Agent_executed=True,native_resolved=m['native_resolved'],
            stop_reason='CONTEXT_RESERVATION_STOP',context_guard_triggered=m['context_guard_triggered'],
            guard_input_tokens=m['context_rejections'][0]['input_tokens'],
            patch_submitted=m['official_patch_submitted'],final_patch_bytes=m['final_patch_bytes'],
            final_patch_sha256=m['final_patch_sha256'],production_source_edits=0,
            patch_classification='DIAGNOSTIC_ONLY' if n['arm']=='A' else 'EMPTY',
            meaningful_behavior_edit_seconds=None,model_requests=m['real_HTTP_requests'],
            HTTP_200=m['HTTP_200'],prompt_tokens=m['observed_prompt_tokens'],
            completion_tokens=m['observed_completion_tokens'],received_tokens=m['observed_received_tokens'],
            usage_complete=m['usage_complete'],thinking_tokens_separately_observed=None,
            charged_tools=m['charged_tools'],agent_seconds=m['agent_wall_seconds'],worker_seconds=n['worker_seconds'],
            Skill_script_calls=m['Skill_invocations'],Skill_bypassed=m['Skill_bypassed'],
            TaskResult_sha256=n['TaskResult_sha256'],JUnit_sha256=n['JUnit_sha256'],counts=n['counts'],
            independent_environment_errors=0,duplicate_snapshot_teardown_records=2,cleanup_complete=True))
    save(HERE/'SESSION_RESULTS.json',dict(status='GPU_EXECUTION_PARTIAL',intended_sessions=6,
        actual_sessions=3,observed_native_outcomes=3,not_run=3,sessions=rows,
        success_denominator='0/3 actual sessions; each arm 0/1 observed task, NOT 0/2',
        raw_sources=['BATCH_01_EXECUTION.json','BATCH_02_DERIVED_METRICS.json','BATCH_02_RUNTIME_AUDIT.json']))
    save(HERE/'MECHANISM_EVENTS.json',dict(complete_observed_Skill_arms=2,
        B=dict(eligible_observed_sessions=1,available_in_request_schema=True,list_calls=0,load_calls=0,
               script_calls=0,bypassed_sessions=1,newly_executed_assertions=0,verdict_events=[]),
        C=dict(eligible_observed_sessions=1,available_in_request_schema=True,list_calls=0,load_calls=0,
               script_calls=0,bypassed_sessions=1,newly_executed_assertions=0,verdict_events=[]),
        A=dict(Skill_applicable=False,diagnostic_execution_attempts=5,executed_assertions=0),
        unrun_B_C_sessions=2,unrun_Skill_usage=None,unrun_bypass=None,
        substantive_verifier_wall_time_seconds=0,
        duplicate_suppression='NOT_EXERCISED',stale_evidence_detection='NOT_EXERCISED',
        model_awareness='UNKNOWN; interface exposed, no explicit list/load/script call',
        mechanism_classification='MECHANISM_BYPASSED',efficacy_classification='INCONCLUSIVE'))
    sums={k:sum(m[k] for m in measured['sessions']) for k in (
        'real_HTTP_requests','HTTP_responses','HTTP_200','observed_prompt_tokens',
        'observed_completion_tokens','observed_received_tokens','charged_tools','agent_wall_seconds','model_HTTP_seconds')}
    worker=sum(n['worker_seconds'] for n in audited['native_results'])
    save(HERE/'RESOURCE_USAGE.json',dict(GPU_SaveKernel_requests=2,CPU_SaveKernel_requests=1,
        real_Gemma_sessions=3,formal_Competition_Submissions=0,selective_reruns=0,
        totals=sums,worker_wall_seconds=worker,
        GPU_batch2_observed_Notebook_seconds=audited['GPU_cost']['session_elapsed_seconds'],
        worker_minus_Agent_seconds=worker-sums['agent_wall_seconds'],
        common_Notebook_seconds_outside_workers=audited['GPU_cost']['session_elapsed_seconds']-worker,
        GPU_batch1_Gemma_requests=0,GPU_batch1_actual_devices=None,GPU_billed_seconds=None,
        account_level_quota_note='POST_RUN_QUOTA_CLI.json is rounded account-wide usage, not an attributable Notebook bill',
        per_candidate=[dict(arm=m['arm'],requests=m['real_HTTP_requests'],prompt_tokens=m['observed_prompt_tokens'],
            completion_tokens=m['observed_completion_tokens'],received_tokens=m['observed_received_tokens'],
            agent_seconds=m['agent_wall_seconds'],model_HTTP_seconds=m['model_HTTP_seconds'],charged_tools=m['charged_tools']) for m in measured['sessions']],
        cost_per_success=None,cost_per_success_reason='No actual native repair succeeded; division by zero is undefined',
        measurement_limits=['First-cell elapsed clock omits earlier platform provisioning/queue.',
            'HTTP latency includes backend service/transport; it is not isolated GPU compute time.',
            'Worker-minus-Agent includes setup, trusted native verification and cleanup, not verifier-only cost.',
            'Two GPU billing totals, per-device active compute and separately attributed thinking usage are unavailable.']))
    save(HERE/'BATCH_02_EXECUTION.json',dict(Notebook_id=140785918,version=1,platform_status='COMPLETE',
        actual_ref='wudangdexiaodoashi/meer-v01-gpu-batch02',actual_GPU='4x NVIDIA L4',TP=4,
        model='Gemma 4 31B QAT v2',model_loaded=True,model_hashes_verified=8,
        real_Gemma_requests=40,HTTP_200=40,received_tokens=314334,sessions=3,
        Native_Resolved=dict(A=False,B=False,C=False),Skill_script_calls=dict(B=0,C=0),
        cleanup=True,archive_sha256=audited['archive_sha256'],shared_payload_sha256=audited['shared_payload_sha256'],
        authorization_consumed_GPU_dispatches=1,allowed_additional_GPU_dispatches=0))
    save(HERE/'PAIRED_ANALYSIS.json',dict(task_order=['fastapi_14297','fastapi_14459'],
        tasks=[dict(task='fastapi_14297',A=None,B=None,C=None,status='NOT_RUN_INFRASTRUCTURE'),
               dict(task='fastapi_14459',A=False,B=False,C=False,status='OBSERVED_NATIVE_NEGATIVE')],
        B_versus_C=dict(B_only=0,C_only=0,both=0,neither=1,unknown=1),
        B_versus_A=dict(B_only=0,A_only=0,both=0,neither=1,unknown=1),
        C_versus_A=dict(C_only=0,A_only=0,both=0,neither=1,unknown=1),
        conclusion='No observed resolved benefit. Verifier efficacy untested because B bypassed it; one task is missing.',
        inferential_statistics=None,generalization=None,leaderboard_prediction=None))
    print(json.dumps(dict(status='GPU_EXECUTION_PARTIAL',actual_sessions=3,real_requests=40,
                          received_tokens=314334,mechanism='BYPASSED')))


if __name__=='__main__':main()
