"""Publishable checkpoint from actual CPU receipts and one accepted dispatch."""
import hashlib,json,shutil,zipfile
from pathlib import Path
from datetime import datetime,timezone
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda n:json.loads((D/n).read_bytes())
cpu=read('CPU_FROZEN_RECEIPT_MANIFEST.json');assert cpu['status']=='CPU_INTEGRATION_PASS_WITH_DECLARED_METADATA_LIMITATIONS'
build=read('gpu-notebook/BUILD.json');accepted=read('gpu-notebook/DISPATCH_ACCEPTANCE.json')
dispatch=read('gpu-notebook/dispatch/DISPATCH_RECORD.json');assert dispatch['SaveKernel_requests']==1
assert sha(D/'gpu-notebook/study.ipynb')==build['notebook_sha256']
copies=D/'cpu-receipts';copies.mkdir(exist_ok=True)
for n in ('SDK_SNAPSHOT_IDENTITIES.json','SOURCE_TREE_VERIFICATION.json','RUNTIME_OVERLAY_IDENTITIES.json'):
    shutil.copyfile(D/'cpu-final-download/evidence'/n,copies/n)
with zipfile.ZipFile(D/'cpu-final-download/r2a-final-cpu-overlay.zip') as z:
    runtime=json.loads(z.read('source/gemma_pair/GPU_ENVIRONMENT_LOCK.json'))
manifest=dict(scope='R2/A independent research pilot; no formal competition submission',
    status='DISPATCH_ACCEPTED_RESULTS_PENDING',frozen_execution_plan_sha256=sha(D/'EXECUTION_PLAN.json'),
    candidate_sha256=read('EXECUTION_PLAN.json')['candidate_sha256'],planned_sessions=read('EXECUTION_PLAN.json')['sessions'],
    CPU_proof=cpu,accepted_dispatch=accepted,dispatch_build=build,
    GPU_authorization_sha256=sha(D/'gpu-notebook/GPU_AUTHORIZATION.json'),
    evaluation_approval_sha256=sha(D/'APPROVED_EVALUATION_AMENDMENT.json'),
    original_baseline_spec_anomaly_sha256=sha(D/'BASELINE_SPEC_ANOMALY.json'),
    model_source=runtime['model_source'],expected_model_files=runtime['model_files'],
    expected_model_files_classification='FROZEN_EXPECTATIONS_NOT_YET_REOBSERVED_FROM_GPU_OUTPUT',
    expected_server_config=runtime['VllmConfig'],expected_generation=cpu['Compiler']['R2']['generation'],
    Agent_limits=dict(seconds=480,charged_tools=28,turns=80,command_seconds=240),
    host_lifecycle_reserve_seconds=1680,archive_cleanup_reserve_seconds=900,
    maximum_Notebook_seconds=18000,maximum_dispatches=1,no_retries=True)
(D/'GPU_DISPATCH_PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
status=dict(gate='R2A_GPU_RUNNING_PENDING_EVIDENCE',observed_at_utc=datetime.now(timezone.utc).isoformat(),
    implemented_candidate='A: R2-Early-Decision',candidate_sha256=manifest['candidate_sha256'],
    human_evaluation_amendment='APPROVED_BEFORE_REAL_MODEL_REQUESTS',
    CPU_integration=cpu['status'],CPU_plumbing_replay='PASS_PLUMBING_ONLY_NOT_REPAIR_EVIDENCE',
    frozen_historical_files_verified=74,planned_independent_tasks=4,planned_real_sessions=8,
    SaveKernel_requests=1,accepted_notebook=accepted['url'],
    real_Gemma_sessions_completed=None,real_Gemma_requests=None,not_run_sessions=None,
    missing_counts_reason='UNKNOWN_UNTIL_RAW_GPU_EVIDENCE_IS_RECOVERED',
    capacity='CAPACITY_UNVERIFIED_ACTUAL_ALLOCATION_EVIDENCE_NOT_YET_RECOVERED',
    official_hidden_Native_Resolved=None,canonical_SWEbench_Resolved=None,
    new_competition_submission=False,R3_created=False,selective_retry=False)
(D/'STUDY_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
report=f'''# Candidate A running checkpoint

Gate: **R2A_GPU_RUNNING_PENDING_EVIDENCE**. The four-task/eight-session pilot has been dispatched once. Actual completed sessions, repair counts, tokens and hardware observations remain UNKNOWN until raw evidence is recovered. No repair gain or score increase is claimed.

Candidate A implements the frozen single-bullet R2-Early-Decision design. A ZIP: `{manifest['candidate_sha256']['A']}`. Frozen R2: `{manifest['candidate_sha256']['R2']}`. Non-prompt files, six R2 deadline rules, model, tools, generation and 480s/28calls/80turns/240s Agent budgets are unchanged. All 74 protected historical file hashes passed read-only verification.

Actual Kaggle CPU version 3 passed original-target reproduction, the declared independent infrastructure controls, six non-root Python 3.11.9/network-denial isolation checks, unchanged source/check fingerprints, real SDK compilation, tool/edit/submit capture, native/independent evaluation and cleanup. The comment-only simulated patch remains unresolved in both evaluators. CPU archive SHA256: `{cpu['archive_sha256']}`. This is plumbing evidence, not repair capability evidence.

The human approved the independent exact-node/semantic primary endpoint before any real model request. Raw SDK verdicts stay unchanged. Record the confirmed SDK prefix-matching limitation, the truncated Pylint node as UNKNOWN and the original xarray Dask co-failure mislabeled PASS_TO_PASS. The latter is never waived for repair success: the complete unchanged test file and every original unambiguous target/control must pass, with a relevant effective production fix and separate semantic approval. See APPROVED_EVALUATION_AMENDMENT.json, BASELINE_SPEC_ANOMALY.json and EVALUATOR_IMPLEMENTATION.md.

The one accepted Notebook is [{accepted['actual_ref']}]({accepted['url']}), kernel ID {accepted['kernel_id']}, version {accepted['version']}. Kaggle derived its canonical slug from the title; DISPATCH_ACCEPTANCE.json preserves both requested and actual references. There was **one** SaveKernel request, no redispatch. HTTP 200 and the canonical acceptance receipt confirm creation; they do not establish a repair or completed session.

The pre-dispatch API observation was 99122.314 available quota seconds, zero reserved, above the frozen 73200-second admission line. Maximum Notebook execution is 18000 seconds. The first runtime phase requires exactly four actual NVIDIA L4 devices, readable memory and CUDA access before model loading. Hardware capacity remains unconfirmed to the local auditor until its raw nvidia-smi/torch evidence is recovered. All eight model hashes must then match. Expected resource budget retains at most five node-hours, with the inherited ten-quota-hour estimate; actual quota change will be reported separately.

Preserve the original eight-session order. Ordinary unresolved repairs remain in the record; infrastructure, unrelated required-control, context/backend, source-integrity, evidence or cleanup failure stops the remaining suffix as NOT_RUN. Never selectively rerun. No formal competition submission or R3 is authorized by this pilot.

Next: recover the single Notebook's actual output, verify allocation/model/configuration/order/evidence/cleanup, review every production patch independently and compare only genuinely observed paired outcomes. Frozen R2 formal submission 57843305 was still PENDING at 2026-11-01T05:24:52Z; it was queried, never resubmitted.
'''
(D/'FINAL_STATUS.md').write_text(report,encoding='utf8')
print(json.dumps(dict(gate=status['gate'],accepted_ref=accepted['actual_ref'],CPU=cpu['status'],actual_repairs='UNKNOWN')))
