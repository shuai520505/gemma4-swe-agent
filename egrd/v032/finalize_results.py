"""Safe derived reports from the verified, once-only completed GPU experiment."""
import json
from pathlib import Path
from .prepare import HERE,PRIVATE,ROOT,REF,sha,write,verify_history
from .inspect_results import lines,transport

ARCHIVE_SHA='67386d9aa82f93612250b2d84dbf26f5bd2a7a82a5494d2ec2fe3bcc2bb74114'
STATUS='EGRD_V032_NEITHER_REPAIRS'


def primary(submitted,target,controls,regression,independent_review):
    if submitted is False:return False
    values=(submitted,target,controls,regression,independent_review)
    if any(v is False for v in values):return False
    if any(v is None for v in values):return None
    return all(v is True for v in values)


def text(name,body):
    (HERE/name).write_text(body,encoding='utf8',newline='\n')


def run():
    identity=verify_history();out=PRIVATE/'verified-output';execution=out/'execution'
    verified=json.loads((PRIVATE/'VERIFIED_PRIVATE_RESULTS.json').read_bytes())
    assert verified['archive_sha256']==ARCHIVE_SHA and verified['all_manifest_and_source_hashes_verified']
    dispatch=json.loads((PRIVATE/'CLI_PUSH_RESULT.json').read_bytes());assert dispatch['SaveKernel_requests']==1
    assert json.loads((execution/'EXECUTION_STATUS.json').read_bytes())==dict(real_sessions=2,status='PAIR_COMPLETE')
    env=json.loads((HERE/'GPU_ENVIRONMENT_LOCK.json').read_bytes())
    model=json.loads((execution/'MODEL_IDENTITY.json').read_bytes());assert model['files']==env['model_files'] and model['weights_verified']
    devices=json.loads((execution/'GPU_DEVICES.json').read_bytes());assert len(devices)==4 and all(d['name']=='NVIDIA L4' for d in devices)
    runtime=json.loads((execution/'GPU_RUNTIME.json').read_bytes());assert runtime['versions']==env['versions']
    boundary=json.loads((execution/'OBSERVED_BOUNDARY_COMPARISON.json').read_bytes());assert boundary['only_supplement_differs']
    tokens=json.loads((execution/'INITIAL_CONTEXT_ADMISSION.json').read_bytes())
    freeze=json.loads((HERE/'EXPERIMENT_FREEZE.json').read_bytes());results={};evaluations={};metrics={};costs={}
    for arm in 'AB':
        d=execution/arm;s=json.loads((d/'SESSION_RESULT.json').read_bytes());ev=s['evaluation']
        assert s['boundary_pass'] and s['cleanup'] and not s['patch_submitted']
        assert ev['submitted_patch_sha256'] is None and ev['original_failing_probe_still_fails']
        assert ev['trusted_probe_unchanged'] and ev['trusted_probe_write_denied'] and ev['tests_did_not_change_source']
        compiled=json.loads((d/'COMPILED_CONFIGURATION.json').read_bytes())
        wire=lines((d/'model_transport/http_wire.jsonl').read_bytes());usage=transport(wire)
        events=lines((d/'events.jsonl').read_bytes());adk=lines((d/'adk_events.jsonl').read_bytes())
        start=next(r['recorded_monotonic'] for r in events if r.get('kind')=='stage' and r.get('agent_started'))
        observed=[r for r in events if r.get('kind')=='production_source_observation' and r.get('changed')]
        calls=[];responses=[]
        for index,event in enumerate(adk,1):
            for part in event['event'].get('content',{}).get('parts',[]):
                call=part.get('function_call');reply=part.get('function_response')
                if call:
                    args=call.get('args',{})
                    calls.append(dict(event_index=index,event_id=event['event'].get('id'),
                        elapsed_seconds=event['recorded_monotonic']-start,name=call['name'],
                        filepath=args.get('filepath'),call_id=call.get('id')))
                if reply:responses.append(dict(event_index=index,name=reply['name'],response=reply['response']))
        relevant=next(c for c in calls if c['name']=='read_file' and c['filepath']=='django/contrib/auth/forms.py')
        failures=[r for r in responses if r['name']=='run_command' and r['response'].get('status')=='error']
        actual_tool_count=len(calls)
        path_files=sorted({name for row in observed for name in row['changed']})
        fallback=d/'unsubmitted_fallback.patch';assert fallback.exists()
        timings=dict(first_relevant_source_read_call_seconds=relevant['elapsed_seconds'],
            first_production_edit_observed_seconds=observed[0]['agent_elapsed_seconds'] if observed else None,
            production_source_observations=len(observed),production_files=path_files,
            production_edit_semantics='Issue-related behavioral attempt, untested' if observed else 'No production edit observed',
            executed_test_command_errors=len(failures),
            successful_discriminating_Agent_checks=0,
            hypothesis_correctness=None,receipt_causal_use_established=None,
            post_production_edit_verification_observed=False if observed else None,
            explicit_submission=False,Agent_tool_function_calls=actual_tool_count,
            official_charged_tools=s['charged_tools'],earliest_read_event=relevant,
            error_event_indices=[r['event_index'] for r in failures],
            evidence='Private per-arm adk_events.jsonl, events.jsonl, native_trace.json, HTTP wire and fallback patch')
        metrics[arm]=timings
        result=dict(arm=arm,status='ENDED_TIME_LIMIT' if arm=='A' else 'ENDED_SERVING_CONTEXT_ADMISSION',
            task_id=freeze['task_id'],study='DEVELOPMENT_MECHANISM_STUDY',S0_sha256=identity['S0_sha256'],
            task_input=freeze['inputs'][arm],actual_real_model_session=True,
            session_ended=True,normal_completion=False,termination_reason=s['agent_error'],
            patch_submitted=False,submitted_patch_sha256=None,submitted_patch_applicable=None,
            unsubmitted_fallback_sha256=sha(fallback.read_bytes()),unsubmitted_fallback_bytes=fallback.stat().st_size,
            fallback_behavioral_evaluation='NOT_RUN; retained privately, never substituted for a submitted repair',
            attempted_production_files=path_files,production_behavioral_edit_attempted=bool(observed),
            meaningful_edit_verified=None,primary_defensible_submitted_repair=False,
            post_edit_target_probe_passed=None,post_edit_controls_passed=None,post_edit_regression_passed=None,
            trusted_evaluation_scope='UNMODIFIED_BASE: missing submission; not evaluation of Agent fallback',
            baseline_target_probe_passed=False,baseline_positive_controls_passed=True,baseline_bounded_regression_passed=True,
            first_production_edit_seconds=timings['first_production_edit_observed_seconds'],
            Agent_seconds=s['agent_seconds'],worker_seconds=s['worker_seconds'],charged_tools=s['charged_tools'],
            native_completed_LLM_calls=s['native_llm_calls'],HTTP=usage,source_observer_seconds=s['source_observer_seconds'],
            initial_input_tokens=tokens['arms'][arm]['input_tokens'],actual_initial_boundary_pass=True,
            B_receipt_visible=(arm=='B'),receipt_used_to_cause_repair=None,
            custom_Context_Guard_triggered=False,server_context_rejection=(arm=='B'),
            rejected_input_tokens_exact=None,rejected_input_tokens_lower_bound=16385 if arm=='B' else None,
            Agent_cleanup=True,trusted_cleanup=True,official_native_resolved=None,canonical_swebench_resolved=None)
        write(HERE/f'SESSION_{arm}_RESULT.json',result);results[arm]=result
        checks=ev['target_receipt']['checks']
        evaluations[arm]=dict(scope='Unmodified exact base because no submitted patch',
            submitted_patch_sha256=None,patch_applicability=None,target_probe_passed=False,
            target_expected_relation_count=checks[-1]['expected'],target_actual_relation_count=checks[-1]['actual'],
            positive_controls_passed=sum(c['passed'] for c in checks if c['control']),positive_controls_total=3,
            bounded_regression_exit_code=ev['bounded_regression']['exit_code'],
            protected_probe_unchanged=ev['trusted_probe_unchanged'],probe_write_denied=ev['trusted_probe_write_denied'],
            source_before_equals_after_tests=ev['tests_did_not_change_source'],cleanup=ev['cleanup'],
            fallback_target_probe_passed=None,fallback_regression_passed=None,
            correctness='NOT_ESTABLISHED',official_native_resolved=None,canonical_swebench_resolved=None)
        costs[arm]=dict(HTTP_requests=usage['requests'],HTTP_responses=usage['responses'],
            HTTP_200=sum(x==200 for x in usage['HTTP_statuses']),HTTP_400=sum(x==400 for x in usage['HTTP_statuses']),
            native_completed_LLM_calls=s['native_llm_calls'],
            observed_received_usage=usage['observed_response_usage'],usage_complete=usage['usage_complete'],
            reasoning_tokens=None,charged_tools=s['charged_tools'],emitted_tool_calls=usage['actual_emitted_tool_calls'],
            executed_tool_function_responses=len(responses),Agent_seconds=s['agent_seconds'],worker_seconds=s['worker_seconds'],
            received_response_transport_seconds=usage['received_HTTP_latency_seconds'],
            source_observer_seconds=s['source_observer_seconds'],
            missing_usage_reason='Last in-flight request canceled at deadline' if arm=='A' else 'Server HTTP400 has no generation usage')
    configs=[json.loads((execution/arm/'COMPILED_CONFIGURATION.json').read_bytes()) for arm in 'AB'];assert configs[0]==configs[1]
    assert metrics['A']['production_source_observations']==1 and metrics['B']['production_source_observations']==0
    write(HERE/'DERIVED_TRAJECTORY_METRICS.json',metrics)
    write(HERE/'TRUSTED_EVALUATION_RESULTS.json',dict(arms=evaluations,
        baseline_reproduced_before_model_loading=True,post_edit_evaluation_of_fallbacks='NOT_RUN',
        limitation='Both trusted evaluations ran on original base after missing submission. Their negative target result is not evidence that the unsubmitted A patch fails.',
        all_three_owned_probe_copies_unchanged=True,official_native_resolved=None,canonical_swebench_resolved=None))
    load=json.loads((execution/'MODEL_LOAD_COMPLETED.json').read_bytes())
    rawcost=json.loads((execution/'COST_RAW.json').read_bytes())
    total={k:sum(costs[a]['observed_received_usage'][k] for a in 'AB') for k in ('prompt_tokens','completion_tokens','total_tokens')}
    write(HERE/'COST_COMPARISON.json',dict(arms=costs,total_observed_received_usage=total,
        real_Agent_sessions=2,HTTP_requests=44,HTTP_200=42,HTTP_400=1,canceled_inflight_requests=1,
        complete_inference_cost_known=False,unobserved_usage_imputed=False,charged_tools_total=40,
        initial_input_tokens={a:tokens['arms'][a]['input_tokens'] for a in 'AB'},B_initial_overhead_tokens=tokens['B_overhead_tokens'],
        model_startup_seconds=load['seconds'],first_cell_to_coordinator_final_record_seconds=rawcost['first_cell_elapsed_seconds'],
        Notebook_log_archive_emission_seconds=1323.315130851,exact_platform_total_runtime_seconds=None,
        billed_GPU_seconds=None,GPU_money_cost=None,
        caveat='Received usage excludes unknown canceled generation and the server rejection. Response latency includes HTTP overhead, not independently measured GPU inference. No separate billing statement available.'))
    write(HERE/'MODEL_IDENTITY.json',dict(source=model['model_source'],revision='Kaggle model instance version2',
        upstream_HF_commit=None,files=model['files'],mounted_bytes_verified=True,weights_loaded=True,
        actual_template_sha256=model['files']['chat_template.jinja'],actual_tokenizer_sha256=model['files']['tokenizer.json'],
        engine_quantization='compressed-tensors',weight_bits=4,model_generation_config=model['generation_config'],
        actual_model_path=model['mounted_path'],historical_serving_equivalence='HISTORICAL_SERVING_EQUIVALENCE_UNVERIFIED'))
    write(HERE/'RUNTIME_AUDIT.json',dict(runtime=runtime,devices=devices,initial_context=tokens,
        Compiler_preload_pass=True,Compiler_both_arms_pass=True,compiled_configurations_equal=True,
        compiled=configs[0],server_seed_observed=0,explicit_request_seed=False,seed17_not_inserted=True,
        engine_seed_source='backend_logs/before_stop-log_file_handle.log: Initializing a V1 LLM engine',
        prefix_cache_disabled_observed=True,context32768=True,research_Guard_installed=False,
        include_thoughts_override=False,all_required_cleanup_observed=True,
        supervisor_generic_official_result='UNKNOWN/official_result_missing, preserved: this development worker does not run an official benchmark TaskResult',
        Native_and_SWEbench_NOT_EVALUATED=True))
    write(HERE/'KAGGLE_GPU_EXECUTION_RECORD.json',dict(status=STATUS,platform_status='COMPLETE',
        ref=REF,Notebook_id=141100028,version=1,URL='https://www.kaggle.com/code/'+REF,
        GPU_dispatches=1,SaveKernel_requests=1,SaveKernel_HTTP_status=200,
        source_commit_at_dispatch=json.loads((PRIVATE/'GPU_DISPATCH.json').read_bytes())['source_commit'],
        payload_sha256=json.loads((HERE/'BUILD.json').read_bytes())['payload_sha256'],
        Notebook_sha256=json.loads((HERE/'BUILD.json').read_bytes())['Notebook_sha256'],
        actual_devices=devices,real_Gemma_sessions=2,order=['A','B'],HTTP_requests=44,
        successful_HTTP_generations=42,extra_model_readiness_generations=0,
        manual_reruns=0,third_session=False,formal_competition_submission='NOT_RUN',
        owner_parallel_clarification_preserved=True,historical_prior_stop='PRECLARIFICATION_STOP.json',
        runtime_window_requested=10000,model_loaded=True,pair_lifecycle_complete=True,
        server_cleanup=True,Agent_and_trusted_roots_and_UID_leases_cleaned=True,
        raw_archive_sha256=ARCHIVE_SHA,raw_archive_bytes=verified['archive_bytes']))
    write(HERE/'RAW_ARCHIVES.json',dict(archive=dict(private_path=str(PRIVATE/'range-download/egrd-v032-real-gemma-ab.zip'),
        sha256=ARCHIVE_SHA,bytes=verified['archive_bytes'],manifest_files=verified['manifest_files'],
        source_files=verified['source_files'],CRC_PASS=True,every_manifest_and_source_hash_PASS=True),
        privacy='Raw HTTP, model reasoning, patches, source/test bodies, evaluator material and logs private; safe derived records only in Git'))
    write_reports(results,costs,metrics)
    from .report_blocked import update_manifest
    update_manifest()
    # Bind the actual completed archive separately from the preserved preflight provenance.
    m=json.loads((HERE/'INTEGRITY_MANIFEST.json').read_bytes())
    m.update(raw_model_or_patch_archives=dict(sha256=ARCHIVE_SHA,private=True,manifest_files=verified['manifest_files']),
        reason='Completed one authorized two-session GPU study; raw contents excluded from Git')
    for p in (PRIVATE/'SAVEKERNEL_SEND.json',PRIVATE/'SAVEKERNEL_HTTP.json',PRIVATE/'CLI_PUSH_RESULT.json',PRIVATE/'range-download/READ_ONLY_DOWNLOAD_RECORD.json'):
        m['private_provenance'][p.relative_to(PRIVATE).as_posix()]=sha(p.read_bytes())
    write(HERE/'INTEGRITY_MANIFEST.json',m)


def write_reports(results,costs,metrics):
    for arm in 'AB':
        r=results[arm]
        text(f'PATCH_{arm}_AUDIT.md',f'''# Arm {arm} patch audit

Explicit submission: **false**. Submitted patch SHA/applicability: **null**.
Private fallback SHA256: `{r['unsubmitted_fallback_sha256']}` ({r['unsubmitted_fallback_bytes']} bytes).

'''+('''One issue-related production persistence-call edit was observed in
`django/contrib/auth/forms.py` at291.1158 seconds. It changes executable behavior,
not just comments, and is a plausible repair attempt on source review. It is not
independently test-validated. No post-edit test or submit_patch occurred. The
native fallback also contains a scratch reproducer; it is not a submitted repair.
''' if arm=='A' else '''No edit to django production code was observed. Two successful edits to
`tests/auth_tests/test_forms.py` added a targeted regression attempt; these are
test changes, not production repairs. A scratch reproducer was also written.
Native fallback extraction filters protected tests, so its scratch-only diff is
not evidence that the test edits never happened. Tool responses preserve them.
''')+'''
Both owned evaluations used an unmodified base because there was no submitted
patch. Fallback applicability, target behavior and regressions remain UNKNOWN;
do not substitute the base failure for a failed evaluation of this private patch.
No reference fix was used. Full patch and diagnostic/test bodies stay private.
''')
    text('REPAIR_TRAJECTORY_COMPARISON.md','''# Observed repair trajectories

| Observation | A: original Issue | B: Issue + frozen receipt |
|---|---:|---:|
| First relevant source-read call |15.596s|14.145s|
| First production edit observed |291.116s|null: none|
| Production files changed |django/contrib/auth/forms.py|none|
| Agent command errors |7|4|
| Production post-edit checks |0|N/A|
| Successful explicit submission |false|false|
| Stop |300s native Agent deadline|277.611s server context admission|

Times for calls are observed ADK event times relative to the session-start journal;
edit time is the post-action source observer's recorded Agent elapsed time.
They are not inferred internal reasoning timestamps. See DERIVED_TRAJECTORY_METRICS
for event indices and private trace references.

A inspected relevant implementation early, wrote scratch/test material, then
encountered a missing test directory, nonexistent root manage.py, missing pytest
executable/module, missing distutils, missing django-admin and unconfigured test
settings. Six test-command attempts failed before establishing a target assertion.
It made a plausible production edit only at291s and spent its remaining time on
an in-flight model request canceled at the official deadline. No fresh behavioral
verification or submission followed.

B inspected the auth form and ModelForm save path by30s, drafted scratch code,
read existing tests and a ManyToMany fixture, then added an Agent-written targeted
test. It did not modify production code. It tried a nonexistent manage.py, missing
pytest executable/module and finally an invalid test-label path. The resulting
traceback entered history before the next generation was rejected. No successful
Agent-side discriminating check was observed in either arm. Static assertion
presence in a test is not successful execution or proof of Issue relevance.

Continued source investigation was related to the Issue; it is not all labeled
waste. The demonstrably ineffective actions are the actual failing test-entry
attempts. Missing tools/dependencies are an Agent-visible development-environment
limitation, separate from the genuine target failure reproduced by the trusted
owned probe. This environment did not provide the full Django test dependency
suite. No recommendation assumes an earlier edit was already known correct.

The receipt was present exactly once at B's real model boundary. B's targeted
test attempt is compatible with that contract, but the original Issue also
describes it: receipt-caused understanding or behavior cannot be independently
identified from this one pair. A/B are development-exposed, fixed order, one seed
stream and one execution each; this is not held-out generalization evidence.
''')
    text('AB_RESULT_ANALYSIS.md','''# Result: neither produces a defensible submitted repair

**EGRD_V032_NEITHER_REPAIRS** refers to the preregistered submitted, verified repair
endpoint: A=false, B=false. It does not mean that A's private unsubmitted edit was
proved incorrect. Its correctness and fresh post-edit probe result are unknown.

Actual inference completed in both scheduled Agent invocations. A ended at its
300-second deadline; B ended with an actual vLLM HTTP400 context-admission error.
Both retained modifications, no successful submit_patch. There was no third
Session, retry, formal submission or reference-patch access.

The treatment has no demonstrated repair benefit. B received the exact failure
receipt (+678 initial serving tokens), but did not edit production. A attempted a
behavioral change late. Both lost time on unusable test commands. A plausible
candidate, execution of a target assertion, and timely closure are separate
capabilities; this trial exposes gaps in all three transitions but cannot assign
causal shares to model, evidence supplement or environment.

B's rejection is **not** the prior custom15360 Guard and **not** a300s timeout.
It is native serving admission with context32768 and requested output16384.
The server reports input **at least16385**, not an exact token count. Initial
inputs3430/4108 both fitted. Last successful B prompt15964; next rejected length
is a lower bound. No safety1024 or research Guard was installed, and no output
length truncation was observed in completed responses. More context cannot be
inferred to fix the issue. The receipt overhead alone is not proven to cause the
stop: paths, generated diagnostics and read volumes diverged.

The trusted evaluator ran after both sessions on the exact original base because
neither submitted a patch. The target remained expected1/actual0, all three
controls and bounded regression passed. These are valid base outcomes, **not
tests of the fallback patches**. No additional CPU/GPU Notebook was dispatched to
test the fallback. This is an important assessment limit, not a negative result
on a patch that was never evaluated.

Smallest next engineering question: can the Agent run one legitimate in-sandbox
targeted check using a verified project entry point and dependency closure,
distinguish setup failures from target assertions, and retain time to validate
and submit an actual repair? Supply execution-environment facts without a fix or
trusted probe leakage in a separately frozen study. First evaluate the retained
fallback with an explicitly scoped CPU-only follow-up if desired; its validity
must not be guessed. Do not tune the receipt/Prompt, increase output/context,
invent another optional verifier or replace S0 from these results.

No statistical superiority, official Native Resolved, canonical SWE-bench or
Public Score conclusion follows. S0's best-observed formal0.13 is unchanged.
''')
    text('FINAL_DECISION.md',f'''# EGRD V0.3.2 final decision

**{STATUS}** — the primary submitted-and-verified repair endpoint is false in
both arms. Two real-Gemma Agent sessions were executed; the platform Notebook is
COMPLETE, but neither Agent completed successfully or submitted a patch.

| Required question | Actual answer |
|---|---|
| Notebook/version |[141100028/v1](https://www.kaggle.com/code/{REF}); private, COMPLETE|
| Dispatches/attempts |One SaveKernel, HTTP200; A then B once each; no extra inference probe|
| GPU allocation |4×NVIDIA L4, each23,659,151,360 bytes; TP4|
| Model loaded |Yes; immutable Kaggle instance version2; all eight asset hashes matched before load|
| Model revision |google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2; no upstream HF commit invented|
| Tokenizer/template |Exact observed SHA256s in MODEL_IDENTITY.json; tokenizercc8d3a0c…, template94899c0f…|
| Runtime |vLLM0.19.1; Torch2.10.0+cu128; CUDA12.8; Python3.12.13; driver580.178.04|
| SDK |swegemma0.2.11, adk-submission0.2.13, google-adk1.36.1; both actual Compilers passed|
| Generation |context32768; output16384; thinking4096/enabled; no request seed; engine log resolves default seed0|
| Common serving |prefix caching disabled, no LoRA, no history filtering/compaction or research Guard|
| S0 bytes |Unchanged3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9|
| Actual input comparison |Only original frozen B supplement differs; identical instructions/tools/config/roles; receipt exactly once|
| Initial actual tokens |A3430; B4108; +678, measured by serving /tokenize and confirmed by first response usage|
| A ended |300.008s native deadline;20 charged tools; late production edit at291.116s|
| B ended |277.611s native serving HTTP400;20 charged tools; no production edit|
| Patches submitted |A=false; B=false; both submitted-patch hashes null|
| Production edits |A django/contrib/auth/forms.py; B none; B did successfully edit Agent-visible tests|
| Post-edit target/controls/regression |NOT_RUN for fallbacks; null. Owned baseline checks did run and failed target1→0, passed3 controls/regression|
| Costs |44 HTTP attempts;42 HTTP200;1 HTTP400;1 canceled in flight;444878 known received tokens, incomplete usage|
| Startup |295.364s model load; first-cell-to-final-coordinator-record1292.657s; exact billing unavailable|
| Evidence used by B |Receipt exposure verified; causal use and useful production impact not established|
| Hypothesis result |No demonstrated benefit on this one exposed task; no generalization or score inference|
| Next action |Repair test-execution prerequisites/entry-point decisions; separately test retained fallback before judging its correctness|

Raw archive `{ARCHIVE_SHA}`:39,610,066 bytes, CRC plus all421 evidence files and
sealed source members verified. Full requests/responses, reasoning, tool results,
test bodies and patches remain private. Per-arm workers/chroots/histories and
trusted contexts were independent; leases, owned processes, workspaces and model
server cleanup passed. Boundary failures were not hidden. Generic supervisor
`official_result_missing` remains UNKNOWN because official benchmark TaskResult
is intentionally absent from this external development study; it is not a Native
Resolved=false. Native per-session traces are present privately.

Missing pytest, distutils, django-admin and proper settings/labels impeded
Agent-created tests. The minimal pinned Django environment supports the owned
probe and bounded regression, not an entire canonical Django/SWE-bench suite.
This is a material experimental limitation, not a claimed model-only failure.
Historical S0 formal-serving equivalence remains UNVERIFIED. The shared engine
default seed0 is observed, not retroactively asserted as historical S0 seed.

**Official Native Resolved: NOT_EVALUATED (null). Canonical SWE-bench resolved:
NOT_EVALUATED (null). Formal competition submission: NOT_RUN.** No candidate or
formal leaderboard submission changed. No further Notebook or real-model run
is authorized by completion of this two-session study.
''')
    text('README.md','''# EGRD V0.3.2 — real Gemma evidence-to-patch A/B

Final status: **EGRD_V032_NEITHER_REPAIRS**. Private Kaggle141100028/v1 COMPLETE;
one GPU dispatch, exactly A→B real Agent sessions, four L4 GPUs and frozen S0.
Neither produced a submitted verified repair. A made a late unverified production
edit; B edited tests/scratch only. Neither fallback was evaluated as a submitted
patch. See FINAL_DECISION.md and AB_RESULT_ANALYSIS.md for the key limitations.

Reproduction: validate archive using inspect_results.py (private verified-output
must not already exist), then `python -m egrd.v032.finalize_results`. Run
`python -m unittest egrd.v032.test_preflight egrd.v032.test_results -v` for offline
integrity and missing-data/endpoint checks. No analysis utility performs model
inference, Notebook dispatch or competition submission.

The exact original S0 ZIP, task, receipt, generation settings and tools remain
unchanged. The only A/B input intervention was the frozen B receipt. Real serving
token overhead678; no seed17, later research Guard, compaction or new Skill.
No official Native/SWE-bench evaluation or new Public Score. Historical S0
serving equivalence remains unverified. S0 remains the formal0.13 baseline.

The earlier no-dispatch stop is preserved in PRECLARIFICATION_STOP.json and Git;
the owner clarified that unrelated concurrent jobs are permitted. A single
subsequent dispatch was accepted; no duplicate, rerun, cancellation of another
job or additional Session occurred. Candidate and historical artifacts were not
altered. Raw task, reasoning, tool/HTTP traces, evaluator files and patches remain
in the controlled private archive; Git contains safe derived records only.
''')


if __name__=='__main__':run()
