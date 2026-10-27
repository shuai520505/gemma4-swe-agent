"""Reproduce safe NOT_RUN records only when the no-dispatch gate really failed."""
import json
from .prepare import HERE,PRIVATE,ROOT,BASE,REF,sha,write,verify_history


def report():
    assert not (PRIVATE/'GPU_DISPATCH.json').exists()
    assert not (PRIVATE/'SAVEKERNEL_SEND.json').exists()
    identity=verify_history()
    gate=json.loads((HERE/'DYNAMIC_PREFLIGHT.json').read_bytes())
    assert gate['static_read_GO'] is False and gate['conflict_gate'] is False
    freeze=json.loads((HERE/'EXPERIMENT_FREEZE.json').read_bytes())
    build=json.loads((HERE/'BUILD.json').read_bytes())
    record=dict(status='EGRD_V032_GPU_ENVIRONMENT_BLOCKED',observed_UTC=gate['queried_UTC'],
        planned_ref=REF,actual_Notebook_ref=None,actual_Notebook_version=None,
        planned_New_Notebook_identity_unused=gate['slug_unused'],GPU_dispatches=0,SaveKernel_requests=0,
        real_Gemma_sessions=0,real_Gemma_requests=0,actual_GPU_devices=None,model_loaded=False,
        formal_competition_submission='NOT_RUN',owner_GPU_authorization=True,
        quota_gate=gate['quota_gate'],remaining_report_seconds=gate['remaining_report_seconds'],
        quota_reserved_report_seconds=gate['GPU_reserved_seconds'],
        no_conflicting_jobs_gate=False,recent_states=gate['recent_states'],
        actual_allocation_and_runtime_window='NOT_OBSERVED: no dispatch',
        action='Stopped before SaveKernel; no cancellation or modification of other jobs; no retry',
        payload_sha256=build['payload_sha256'],final_bound_Notebook_sha256=None,
        reason='A different GPU Notebook is QUEUED; another GPU Notebook status returns HTTP 404; cancellation acknowledgment is also preserved without inventing terminal completion.')
    write(HERE/'KAGGLE_GPU_EXECUTION_RECORD.json',record)
    results={}
    for arm in ('A','B'):
        row=dict(arm=arm,task_id=freeze['task_id'],status='NOT_RUN',
            reason='Mandatory current no-conflicting-GPU-jobs gate failed before dispatch',
            S0_sha256=identity['S0_sha256'],task_input=freeze['inputs'][arm],
            actual_model_usage=dict(sessions=0,requests=0),
            completed=None,patch_submitted=None,submitted_patch_sha256=None,patch_applicable=None,
            changed_production_files=None,meaningful_behavioral_edit=None,
            target_probe_passed=None,positive_controls_passed=None,bounded_regression_passed=None,
            prompt_tokens=None,completion_tokens=None,received_tokens=None,charged_tools=None,
            Agent_seconds=None,worker_seconds=None,model_latency_seconds=None,
            evidence_received_at_actual_Gemma_boundary=None,evidence_used_for_edit=None,
            official_native_resolved=None,canonical_swebench_resolved=None)
        write(HERE/f'SESSION_{arm}_RESULT.json',row);results[arm]=row
        (HERE/f'PATCH_{arm}_AUDIT.md').write_text(
            f'# Arm {arm} patch audit\n\nNOT_RUN. No Agent Session, submitted patch, source edit or post-edit result exists for this study. '
            'All patch/evaluation fields remain null. This is not a failed repair outcome. '
            'The PR40 synthetic comment-only patch is engineering evidence and is not an Arm '+arm+' Gemma repair.\n',encoding='utf8')
    write(HERE/'TRUSTED_EVALUATION_RESULTS.json',dict(status='NOT_RUN',
        A=dict(status='NOT_RUN',target=None,positive_controls=None,regression=None),
        B=dict(status='NOT_RUN',target=None,positive_controls=None,regression=None),
        current_baseline_rerun='NOT_RUN: no Notebook dispatched',
        historical_PR40=dict(Notebook='141087018/v1',CPU_model='SCRIPTED_ONLY',gates=17,
            archive_sha256=identity['CPU_archive_sha256'],reverified_archive_integrity=True),
        official_native_resolved=None,canonical_swebench_resolved=None))
    write(HERE/'COST_COMPARISON.json',dict(status='NO_COMPARISON: both sessions NOT_RUN',
        research_GPU_dispatches=0,real_Gemma_requests=0,allocated_research_GPUs=0,
        billed_GPU_seconds=None,reason_billing_unknown='No study dispatch; no separate billing statement queried',
        A={k:results['A'][k] for k in ('prompt_tokens','completion_tokens','received_tokens','charged_tools','Agent_seconds','worker_seconds')},
        B={k:results['B'][k] for k in ('prompt_tokens','completion_tokens','received_tokens','charged_tools','Agent_seconds','worker_seconds')},
        initial_tokenized_counts=None,B_token_overhead=None,B_frozen_input_overhead_bytes=1575,
        actual_startup_seconds=None,actual_Notebook_seconds=None,
        remaining_account_quota_report_seconds=gate['remaining_report_seconds'],
        caution='Account usage is not experimental consumption; bytes are not token counts'))
    (HERE/'REPAIR_TRAJECTORY_COMPARISON.md').write_text('''# Trajectory comparison

No trajectories were generated. A and B are NOT_RUN; neither is a negative repair
observation. No localization, hypothesis, edit, verification, closure, adoption or
causal treatment effect can be compared. Historical scripted CPU counters are
not included as real model requests.

The sealed implementation preserves actual initial requests before forwarding,
HTTP responses and cancellation events, native trace/patch outputs, observed
source-version changes, independent trusted checks and cleanup. This pathway
was prepared but was not exercised by Gemma in this study.
''',encoding='utf8')
    (HERE/'AB_RESULT_ANALYSIS.md').write_text('''# A/B result analysis

**No comparative result exists.** The required resource/conflict gate failed
before SaveKernel. The owner explicitly required stopping when a mandatory
pre-inference gate failed or remained unknown. Available quota does not override
an observed queued job or establish that an inaccessible status is inactive.

S0 and task/evidence bytes remain frozen. The prepared treatment is solely the
original 1,575-byte input supplement; no Prompt, seed, output cap, Guard,
compaction, thought filtering, Skill or tool-schema intervention was introduced.
The shared experimental server disables prefix caching in both arms. Exact
historical serving equivalence to S0's formal 0.13 submission is unverified.

The evidence-to-patch hypothesis is neither supported nor falsified. Do not
interpret two missing observations as NEITHER_REPAIRS or infer any Public Score.
No new Agent capability improvement is justified by this blocked attempt.

Next action: resolve/read-only verify the queued and unknown GPU jobs, then
revalidate current resources, dependencies and the exact bound Notebook before
executing the same A→B study under applicable owner permission. Do not change the
receipt or candidate, cancel unrelated jobs, or dispatch while conflict remains.
This task has no automatic monitoring or future dispatch scheduled.
''',encoding='utf8')
    (HERE/'FINAL_DECISION.md').write_text(f'''# EGRD V0.3.2 final decision

**EGRD_V032_GPU_ENVIRONMENT_BLOCKED**

At {gate['queried_UTC']}, the final read-only preflight returned
`static_read_GO=false`, `conflict_gate=false`. The existing GPU Notebook
`wudangdexiaodoashi/the-boys-i-am-better` was QUEUED. Its separate
`the-boys-i-am-better-23d8c6` entry returned HTTP 404 for execution status;
metadata identifies it as GPU-enabled, not proven inactive. A third entry
reported CANCEL_ACKNOWLEDGED; this was not rewritten as completed. No other
Notebook was canceled, edited or redispatched.

Quota was {gate['remaining_report_seconds']} report seconds remaining, reserved
0, exceeding the conservative 41,200-second planning floor. This does not prove
accelerator allocation or remove the conflict. The earlier clean preflight is
archived; it was superseded by the mandatory fresh check.

| Required question | Observed answer |
|---|---|
| Actual GPU Notebook/version | None. Planned `{REF}` remains unused. |
| GPU dispatches / SaveKernel / real Sessions | 0 / 0 / 0 |
| Actual GPUs | None allocated to this study. 4×L4/TP4 is only the frozen request. |
| Model loaded | No. Version-2 metadata lists all eight expected assets; mounted byte verification was NOT_RUN. |
| Exact model/tokenizer/template used | None used. Expected identities are in MODEL_IDENTITY.json; no upstream HF revision invented. |
| Runtime used | No Kaggle runtime started. Planned vLLM 0.19.1, Torch 2.10.0+cu128, Python 3.12, CUDA 12.8 and pinned SDK. |
| Context / generation | Planned context32768, output16384, thinking4096, enabled; no explicit seed or later research Guard. Actual serving defaults not observed. |
| S0 bytes | Preserved: `{identity['S0_sha256']}`. |
| A/B input identity | Verified against PR40 CPU requests; only frozen supplement differs. No real-Gemma boundary was reached. |
| A / B completion | NOT_RUN / NOT_RUN; completion flags remain null. |
| A / B patch submission and hashes | None observed; null / null. |
| Production files edited | Unknown/not executed; null, not an observed empty repair attempt. |
| Target, controls, regression | All current study outcomes null; prior PR40 SCRIPTED_ONLY engineering evidence retained separately. |
| Tokens/tools/time | Per-session fields null; real model requests0. No character-to-token conversion. |
| B evidence use | Not observable; no B inference. |
| Treatment hypothesis | Not tested; no repair-effect conclusion. |
| Statistical scope if eventually run | One exposed Django task, one attempt per arm; descriptive development-only evidence. |
| Next capability improvement | None selected from missing outcomes; first complete the frozen diagnostic after conflicts are resolved. |

## Gate accounting

- PASS: exact starting commit, historical archives/manifests, S0 ZIP/members,
  original task/Issue and frozen A/B inputs; previous 17-gate CPU archive verified.
- PASS: 12 new offline checks and 17 applicable PR40 regressions, payload
  compilation/closure, JSON checks, privacy scan and git diff whitespace check.
  These are engineering tests, not Gemma adoption or repair evidence.
- PASS: authenticated read-only Kaggle resources, model version metadata and
  available account quota, unique private planned Notebook identity.
- FAIL/UNKNOWN: current conflicting jobs; no assumption that HTTP404 means idle.
- NOT_RUN: actual 4×L4 allocation, accepted runtime window, mounted weights and
  tokenizer hashing, runtime SDK recheck, model startup/TP4, initial serving token
  counts, native real-model Runner, submitted-patch evaluation and runtime cleanup.
- AUTHORIZED: bounded one-dispatch/two-session owner grant, unused. The blocker is
  not lack of owner authorization. No delayed execution was scheduled.

The original CPU environment is not rebuilt. Local cached Python3.12 lacks
swegemma, so no new local full-Compiler claim is made. Exact actual-runtime
Compiler/hash checks are sealed before loading, but were not run here.

**Official Native Resolved: NOT_EVALUATED. Canonical SWE-bench: NOT_EVALUATED.
Formal Kaggle submission: NOT_RUN.** S0 remains the best-observed formal baseline.

Source base: `{BASE}`. Frozen runtime payload:
`{build['payload_sha256']}`. Final quota-bound Notebook was not generated because
the fresh gate failed; there is no actual execution identity or result archive.
''',encoding='utf8')
    update_manifest()


def update_manifest():
    build=json.loads((HERE/'BUILD.json').read_bytes())
    files={p.name:sha(p.read_bytes()) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='INTEGRITY_MANIFEST.json'}
    sources={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in [ROOT/'candidates/s0/submission.zip',ROOT/'egrd/v031/S0_AGENT_LOCK.json',ROOT/'egrd/v031/TASK_IDENTITY_LOCK.json',ROOT/'egrd/v031/EVIDENCE_RECEIPT.json',ROOT/'egrd/v0311/INTEGRITY_MANIFEST.json']}
    private_provenance={}
    for parent in ('official-serving-source','conflict-recovery'):
        for p in sorted((PRIVATE/parent).rglob('*')):
            if p.is_file() and p.suffix!='.ipynb':private_provenance[p.relative_to(PRIVATE).as_posix()]=sha(p.read_bytes())
    folder=json.loads((HERE/'DYNAMIC_PREFLIGHT.json').read_bytes())['preflight_private_record']
    from pathlib import Path
    for p in sorted(Path(folder).iterdir()):
        if p.is_file():private_provenance['final-preflight/'+p.name]=sha(p.read_bytes())
    write(HERE/'INTEGRITY_MANIFEST.json',dict(public_files=files,historical_references=sources,
        private_runtime_payload_sha256=build['payload_sha256'],private_provenance=private_provenance,
        raw_model_or_patch_archives=None,reason='No dispatch or model session occurred',
        historical_results_modified=False,frozen_candidates_modified=False))


if __name__=='__main__':report()
