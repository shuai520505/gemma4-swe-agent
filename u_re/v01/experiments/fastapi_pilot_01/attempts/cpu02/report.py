"""Preparation records only. Never fabricate HTTP receipt or task execution."""
import hashlib
import json
from datetime import datetime,timezone
from .prepare import HERE,PILOT,ROOT,write


def main():
    spec=json.loads((HERE/'BUILD_FREEZE.json').read_bytes())
    preflight=json.loads((HERE/'evidence/READONLY_PREFLIGHT.json').read_bytes())
    assert preflight['identity_confirmed'] and preflight['slug_conflict'] is False
    assert not (HERE/'execution').exists() and not (HERE/'HTTP_RECEIPT.json').exists()
    write(HERE/'CPU02_PRECHECK.json',dict(state='CPU02_READY_FOR_AUTHORIZATION',can_dispatch_now=False,
        Gate_A=dict(status='READONLY_SNAPSHOT_PASS_RUNTIME_RECHECK_REQUIRED',identity_confirmed=True,
            evidence='evidence/READONLY_PREFLIGHT.json',queried_at_utc=preflight['queried_at_utc'],
            visible_slug_conflict=False,scope='API visibility,not an authoritative create-only server guarantee',
            credentials_refresh_or_rotation=False,future_snapshot_max_age_seconds=600),
        Gate_B=dict(status='PASS_STATIC_CPU_ONLY',configuration=spec['configuration']),
        Gate_C=dict(status='PASS_OFFLINE_INTEGRITY',Notebook_sha256=spec['Notebook_sha256'],wire_sha256=spec['wire_sha256'],
            payload_sha256=spec['payload_sha256'],selection_protocol_sha256=spec['selection_protocol_sha256'],
            candidate_pins=json.loads((PILOT/'CANDIDATE_INTEGRITY.json').read_bytes())['candidates']),
        Gate_D=dict(status='LOCAL_TEST_PASS_LIVE_NOT_TESTED',test_methods=20,
            cases='14 required faults plus SDK duplicate-send,corrupt claim,unexpected version and preparation/collection guards',
            max_dispatches=1,client_retry_limits_zero=True,redirects_disabled=True,crash_reentry_blocked=True),
        Gate_E=dict(status='NOT_AUTHORIZED',explicit_separate_CPU02_grant_received=False,
            reason='Current human instruction authorizes engineering only,explicitly requires a separate execution grant acknowledging CPU01 uncertainty'),
        GPU_authorized=False,algorithm_validated=False))
    write(HERE/'DISPATCH_JOURNAL.json',dict(execution_id=spec['execution_id'],slug=spec['slug'],state='PREPARED',
        at_utc=datetime.now(timezone.utc).isoformat(),authorization_status='NOT_AUTHORIZED',
        actual_SaveKernel_dispatches=0,accepted_version=None,HTTP_response_observed=False,
        intent_scope='Offline preparation preview,not AUTHORIZED/DISPATCH_STARTED;future durable events live in execution/events',
        **{k:spec[k] for k in ('base_commit','Notebook_sha256','wire_sha256','payload_sha256','selection_protocol_sha256','configuration','expected_candidates_in_order','sdk_versions')}))
    write(HERE/'NOTEBOOK_IDENTITY.json',dict(planned_slug=spec['slug'],accepted_version=None,Notebook_id=None,
        saved_at_utc=None,run_status='NOT_RUN',Notebook_sha256=spec['Notebook_sha256'],wire_sha256=spec['wire_sha256'],payload_sha256=spec['payload_sha256']))
    write(HERE/'CPU_RESULTS_MANIFEST.json',dict(execution_id=spec['execution_id'],status='NOT_RUN',version=None,
        outputs=None,TaskResult=None,JUnit=None,cleanup=None,CPU02_actual_native_checks=0,
        CPU01_actual_native_checks=None,overall_pilot_actual_checks=None))
    ranked=json.loads((PILOT/'RANKED_POOL.json').read_bytes())['rows']
    write(HERE/'TASK_SCREENING_LEDGER.json',dict(execution_id=spec['execution_id'],status='NOT_RUN',
        checked=0,max_checks=8,selected=[],rows=[dict(r,status='NOT_RUN',passed=None,failed=None,errors=None,
            skipped=None,xfailed=None,setup_errors=None,collection_errors=None,native_exit_code=None,
            eligible=None,seconds=None,JUnit_sha256=None) for r in ranked]))
    write(HERE/'PAIR_REGISTRATION_DRAFT.json',dict(status='DRAFT_NO_ADMITTED_PAIR',
        execution_source=spec['execution_id'],selected=[],
        order=[dict(slot=i+1,arm=a,instance_id=None) for i,a in enumerate(['NoEGV','Full','Full','NoEGV'])],
        candidate_pins=json.loads((PILOT/'CANDIDATE_INTEGRITY.json').read_bytes())['candidates'],
        model='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',
        agent_seconds=300,counted_tools=60,command_seconds=120,
        execute=False,gpu_authorized=False,formal_submission=False,gpu_algorithm_validated=False,
        sample_dependency='same FastAPI repository;after native selection audit Issue/target/test overlap without subjective replacement'))
    write(HERE/'evidence/FAULT_FIX_HISTORY.json',dict(first_log='fault_tests_01.log',initial_methods=14,initial_failures=11,
        failure='Journal used duplicate at_utc keyword in DISPATCH_STARTED intent before transport;all affected mocked transport counts0',
        old_source='dispatch_v00.py.txt',fix='distinct event_at_utc field;original intent timestamp retained',
        second_log='fault_tests_02.log',second_passed=14,
        expanded_log='preparation_tests_01.log',expanded_passed=18,final_log='final_local_tests.log',final_passed=20,
        live_SaveKernel_dispatched_during_tests=0,native_task_executions_during_tests=0))
    documents={
    'README.md':'''# U-RE-FASTAPI-PILOT-CPU02 — preparation only

CPU02_READY_FOR_AUTHORIZATION. No independent CPU02 execution grant has been received;no SaveKernel/Notebook run/version/GPU/Agent/Gemma/Submission was requested. This instruction authorizes engineering,not execution. Current0CPU02 native checks;no TaskResult/JUnit/HTTP receipt exists. Zero is known for CPU02 only;CPU01 actual platform execution remains unknown.

New planned slug wudangdexiaodoashi/gemma4-u-re-fastapi-pilot01-cpu02,independent output prefix. Exact evaluator payload is inherited from CPU01 and unchanged. Notebook changes only independent paths,execution label and an extra zero-CUDA assertion. All frozen U-RE candidate/Prompt/YAML/budget and79exclusions/50rank remain unchanged. Max8 native checks,first2 eligible distinctIDs,ABBA future design. No new selected task identity is claimed.

Durable one-dispatch controller:authorization+scope/hash checks before API work;permanent exclusive locks/dispatch claim;fsynced immutable events;HTTP metadata persisted before JSON parsing;no-retry adapter/redirects;preserved SDK return/error.20local fault/preparation tests passed,using installed SDK serialization/parser and mocked outer network. Not official Linux CPU baseline or real Gemma evidence. See CPU02_EXECUTION_PROTOCOL.md,CPU02_PRECHECK.json,LOCAL_VALIDATION.md andFINAL_DECISION.md.
''',
    'CPU01_UNKNOWN_CARRYOVER.md':'''# CPU01 remains SAVE_STATUS_UNKNOWN

Original sole SaveKernel2026-10-21T06:17:01.841556Z,slug ending cpu01. PR13 da207da archives independent read-only reconciliation:170API-visible rows,private resource positive control200,targetGetKernel403,no accepted version,UI unavailable. CPU01 actual platform/native execution count stays null. Do not query cpu01 again under this task or resave its slug.

CPU02 is an independent future attempt,not a retry that establishes CPU01 rejection. Separate explicit authorization must permit one newCPU-only Save+run and acknowledge CPU01 may already have been accepted. CPU02 success/failure cannot retroactively determine CPU01. Across attempts total actual native checks remain unknown;max8 is CPU02's registered screening cap,not a claim about unknown historical executions.
''',
    'CPU02_EXECUTION_PROTOCOL.md':'''# CPU02 execution protocol — NOT AUTHORIZED

Current engineering instruction is not a grant. No authorization artifact is generated in this preparation. Future trusted human instruction must identify U-RE-FASTAPI-PILOT-CPU02 and exact slug,permit one newCPU-only SaveKernel+run,and acknowledge CPU01 may have been accepted but remains unknown. Launch requires that trusted message reference,scope flags,exact Notebook/wire/payload/protocol hashes and actual sourceCommit. JSON fields alone cannot cryptographically prove human authorization;the operator must obtain evidence from a real human message,never test fixtures or an environment flag.

Before any dispatch:verify frozen source/ZIP/member/metadata/payload/protocol/79exclusions/50rank and installed SDK call-source pins. Obtain a fresh (<=600s) CPU02-only read identity/collision snapshot. Account match,read-only success,complete API-visible paging/no knownslug collision are required. Visibility is not a server-side create-only guarantee:installed SaveKernel has no audited create-only conditional field. Known collision or uncertain scope=>STOP. An unexpected accepted version!=1 is preserved as known acceptance but an integrity STOP;never retry or collect it as the registered new version.

launch.py without --authorization raises PermissionError before authentication/network. A separately supplied trusted grant and fresh --preflight are required. There is no authorize command or automatic grant. Live execution uses reviewed kagglesdk SaveKernel directly,once;Notebook JSON normalization matches frozen SDK-wire SHA. GPU/TPU/internet=false,model sources absent,machine_shape absent,private=true,requested CPU window7200s (not approved). The frozen original screening module is the only worker;no Agent/model is constructed. Native verification cap300s,worker6000s;platform/resource timing is not guaranteed.

State/events:PREPARED→AUTHORIZED→DISPATCH_STARTED→RESPONSE_RECEIVED→ACCEPTED_CONFIRMED or REJECTED_CONFIRMED or UNKNOWN_STOP;OUTPUT_COLLECTED follows only existing accepted terminal output collection. Auxiliary OBSERVER_RECORDING_FAILED is not an acceptance verdict. Root DISPATCH_JOURNAL.json is the actual offline PREPARED preview. Future runtime records are exclusive immutable execution/events files,with permanent execution.lock and dispatch.claim. No claim is deleted automatically. A partial/corrupt/existing dispatch claim blocks all resend;restart after known acceptance preserves that knowledge. A pre-send disk failure prevents dispatch;post-send disk failure preserves original SDK semantics but fails audit closed.

Immediately before transport fsync the claim/intent with executionID,slug,sourceCommit,Notebook/wire/payload/protocol SHA,CPU config,possible first8task IDs,SDK versions,UTC,authorization status and local request correlation ID. Then fsync DISPATCH_STARTED. Only then may transport run. HTTP response status/content-type/length/size/correlation metadata is durably written BEFORE JSON parsing. Parsing writes a separate whitelist receipt,never raw body/headers/tokens/cookies/signed URLs. Non-JSON/empty responses remain observed facts for that future response;no retrospective CPU01 reconstruction. Recorder errors do not replace the SDK return/error.

No automatic retries:SDK call/save wrapper source pins each have one call;controller checks one Save dispatch;Retry total/connect/read/status/redirect/other all0;allow_redirects=false;second SDK attempt blocked before transport. Persistent O_EXCL claims protect separate process reentry. Dedicated single-purpose process,not a concurrent SDK service. Client guarantee does not establish intermediaries/server never internally replay. fsync/claim behavior is tested for process exit,not arbitrary hardware/filesystem loss.

On known structured rejection preservecode+status and stop. On timeout/disconnect/parse/recording/incomplete ACK stopUNKNOWN,never resend,change config thenretry,upload tocpu01 or createcpu03. On accepted version1 read only the original version/status/output. Collector refuses before accepted event,requires exact resource/source/version stability and terminal status,limits requests/output sizes,saves raw artifacts/hashes and marks admission unaudited. It never executes downloaded code. A full native JUnit/TaskResult/input/cleanup audit is still required before tasks become eligible. Collector live transport has NOT been tested here;its no-version refusal is locally tested.
''',
    'SAVE_STATUS.md':'''# CPU02 save status — NOT_RUN

Preparation stateCPU02_READY_FOR_AUTHORIZATION;dispatch journalPREPARED only. Authorization absent. Actual new SaveKernel dispatches0. Accepted version/id/saveUTC=null;HTTP response not observed. HTTP_RECEIPT.json/HTTP_METADATA.json are intentionally absent,not prefilled. Existing controller unit-test receipts are synthetic temporary files,not Kaggle records. No new CPU/GPU Notebook has been saved or run.
''',
    'TASK_ADMISSION_REPORT.md':'''# CPU02 native task admission — NOT_RUN

No independent execution grant,noSave,no native verify_task invocation. Actual CPU02 checks0;all50task rowsNOT_RUN with unobserved test/exit/time/hash fields null. No baselineeligible task,no pair,no TaskResult/JUnit/cleanup. Historical110/110 compatibility is unchanged and not rerun or counted here.

Future CPU02 uses exact prior protocol/hash/rank/payload:129metadata−79conservative exclusions=50FastAPI,visit frozen order,max8native checks,first2eligible distinctIDs,ordinary behavioral assertions allowed,all-pass non-discriminating,environment/identity/evidence/cleanup errors handled by frozen rule. No task substitution,reference patch,unapproved dependency,test/Verifier edit. Evaluator-only tests never enter candidate or future Agent input. Raw original results must be archived before independent native admission classification. Stop after2eligible or max8;no sample expansion.
''',
    'RESOURCE_BUDGET.md':'''# Resource plan — no new compute authorized

CPU02 requested window7200s,worker6000s,nativeVerifier300s/task,max8checks. These are frozen planning/request values,not platform-approved allocation or measured CPU task durations. No model input/GPU/Agent/Gemma,zero model time. Only local tests and3read-only account/listing requests were executed in this preparation.

Future four-model-run plan remains historical8940s:startup1200+dependencies600+two baselines960+four workers4440+idle240+export600+safety900. Proposed10000swindow has1060s arithmetic headroom,not actual authorization/resources. No currentGPU quota/4L4/window/model-route identity was checked. U-RE Agent300s/60chargedtools/120command parameters are unchanged;CPU02 baseline verification is not Agent inference. Real resolved and costs remain unmeasured. Same-repository n2 would be an initial mechanism pilot,not general repair-rate evidence.
''',
    'LOCAL_VALIDATION.md':'''# Local test evidence and limits

Command:python -m unittest u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02.tests.test_dispatch u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02.tests.test_preparation -v

Final20/20PASS,release check4.304s,evidence/release_local_tests.log (earlier20pass retained atfinal_local_tests.log). Uses actual installed kagglesdk typed requests,HTTP serialization and response/error parsing;only outer requests.Session.send transport is replaced. All SaveKernel interactions in tests are local mocks;no real Kaggle Save/GPU/Agent/native task. Tests cover JSON200,non-JSON502,empty204,403,429,timeout,disconnect,disk observer failure,child os._exit afterdispatch before response,restart,wrong/existing slug,redaction,missing grant,GPU/TPU/model/network flags,second SDK send,torn claim,unexpected accepted version,payload/config/collector guards. Exact API retries0 and redirectsfalse are asserted in fake transport. Real launch with missing grant is run in a child process with any network forbidden and fails before SDKwork.

First14-method run failed11 before mocked transport due duplicate at_utc keyword in journal.append;fixed by distinct event_at_utc. Original source/failure log retained in evidence/dispatch_v00.py.txt,fault_tests_01.log andFAULT_FIX_HISTORY.json. Next14pass and expanded18pass retained. No failed real task or Save was hidden/retried.

Live collector/official Linux baseline compatibility isNOT_RUN. Controller is a research upload safety layer,not part of candidateZIP/official Agent tools. Existing six tools and official Verifier are untouched. No CPU02 authorization file is present. Future launch source must match sealed file hashes;do not overwrite frozen artifacts to force a pass.
''',
    'FINAL_DECISION.md':'''# CPU02_READY_FOR_AUTHORIZATION — execution blocked

Offline preparation is complete;not all live runtime gates are permanently Go. Separate CPU02 human execution authorization is absent. Current instruction explicitly forbids treating itself as that grant. No SaveKernel,Notebook version/run,GPU/Gemma/Agent/Submission. No real HTTP receipt/JUnit/TaskResult is generated. Future runtime still needs fresh identity/collision snapshot,source/SDK/ZIP verification and scope-bound grant. If absent,STOP before network.

|Question|Actual answer/evidence|
|---|---|
|Q1 CPU01unknown preserved?|Yes,SAVE_STATUS_UNKNOWN with actual platform countnull;CPU01_UNKNOWN_CARRYOVER.md and unchanged PR13|
|Q2 independentCPU02?|New plannedcpu02slug,path,executionID and Notebook hashes;BUILD_FREEZE.json;not an accepted resource|
|Q3 observer fault tests?|20local tests pass covering all14required fault classes;LOCAL_VALIDATION.md,evidence/final_local_tests.log|
|Q4 no automatic duplicate?|Permanent fsyncedclaims+reentry guard+no-retry adapter+redirectfalse+singleSDKsend pins locally verified;external server replay not guaranteed;SDK_RETRY_AUDIT.json|
|Q5 identity/CPU config?|Current read-only owner/listing succeeds,no API-visiblecpu02collision;CPU-only bytes verified;fresh runtime check remains required;CPU02_PRECHECK.json|
|Q6 candidates/exclusions/rank?|Exact ZIP/member/Prompt/YAML and79/50/protocol/payload unchanged;HISTORY_AUDIT.json,INTEGRITY_MANIFEST.json|
|Q7 separate execution grant?|No;GateE NOT_AUTHORIZED;no authorization artifact,CPU02_PRECHECK.json|
|Q8 actual Save requests?|0new actual SaveKernel;only3readonly API calls,all testdispatches mocked;DISPATCH_JOURNAL.json|
|Q9 accepted version/output?|None;null,NOT_RUN;NOTEBOOK_IDENTITY.json,CPU_RESULTS_MANIFEST.json|
|Q10 real native baselines?|CPU02zero,all test quantitiesnull;CPU01 and overall actual countsunknown;TASK_SCREENING_LEDGER.json|
|Q11 two admitted tasks?|No;selected=[],TASK_ADMISSION_REPORT.md|
|Q12 GPU authorization request ready?|No;first independentCPU02authorization,then real two-tasknativeadmission+identity freeze,then separateGPUresource/runtime/authorization gates;PAIR_REGISTRATION_DRAFT.json|

No algorithm benefit/new PublicScore is claimed. Do not repeat CPU01 queries or savecpu01. Future user may explicitly authorize one CPU02-only save+run while acknowledging CPU01unknown;until then keep this ready-but-not-authorized state. GPU remains separately NOT_AUTHORIZED even after CPU02 baseline success.
'''}
    for name,text in documents.items():write(HERE/name,text)
    print(json.dumps(dict(state='CPU02_READY_FOR_AUTHORIZATION',new_SaveKernel=0,authorization=False,local_tests=20)))


if __name__=='__main__':main()
