"""Archive actual partial preparation; never infer CPU execution from a save."""
import difflib
import hashlib
import json
from pathlib import Path
from .register import HERE,ROOT,PREVIOUS,write


def main():
    auth=json.loads((HERE/'AUTH_STATUS.json').read_bytes())
    failed=json.loads((HERE/'results/cpu01/HOST_SAVE_FAILURE.json').read_bytes())
    assert auth['status']=='AUTH_READONLY_GO'
    assert failed['status']=='CPU_SAVE_UNCONFIRMED_STOP'
    ranked=json.loads((HERE/'RANKED_POOL.json').read_bytes())['rows']
    rows=[]
    for rank,r in enumerate(ranked,1):
        rows.append(dict(r,rank=rank,status='NOT_RUN',cpu_entered=None,
            platform_execution_status='UNKNOWN: save acceptance not confirmed',
            reason='No accepted Notebook version or native execution evidence; do not retry uncertain save',
            passed=None,failed=None,errors=None,skipped=None,xfailed=None,setup_errors=None,collection_errors=None,
            native_exit_code=None,baseline_resolved=None,environment_admitted=None,seconds=None,JUnit_sha256=None))
    write(HERE/'TASK_SCREENING_LEDGER.json',dict(experiment_id='U-RE-V01-FASTAPI-PILOT-01',
        status='TASK_ADMISSION_BLOCKED',execution_stop='CPU_SAVE_UNCONFIRMED_STOP',
        confirmed_cpu_checks=0,actual_platform_cpu_checks=None,max_checks=8,selected=[],rows=rows,
        SaveKernel_dispatches=1,SaveKernel_retries=0,accepted_Notebook_version=None,
        GPU=False,Agent_runs=0,model_calls=0,formal_submission=False))
    write(HERE/'TASK_IDENTITY_MANIFEST.json',dict(status='NO_ADMITTED_TASKS_BOUND',selected=[],
        metadata_rows=ranked,metadata_only=True,snapshot_sha256=None,test_overlay_sha256=None,task_record_sha256=None,
        note='Issue/base hashes inherited from frozen metadata are not a complete native runtime identity'))
    old=json.loads((PREVIOUS/'GPU_EXECUTION_DRAFT.json').read_bytes())
    draft=dict(old,experiment_id='U-RE-V01-FASTAPI-PILOT-01',status='BLOCKED_CPU_SAVE_UNCONFIRMED',
        execute=False,gpu_authorized=False,formal_submission=False,gpu_algorithm_validated=False,
        selected_tasks=[],runtime_model_hashes_verified=False,resource_admission=False,
        GPU_Notebook_generated=False,GPU_Notebook_saved=False,
        execution_stub_sha256=hashlib.sha256((HERE/'gpu_execution_stub.py').read_bytes()).hexdigest())
    write(HERE/'GPU_EXECUTION_DRAFT.json',draft)
    write(HERE/'PAIR_PROTOCOL.json',dict(experiment_id='U-RE-V01-FASTAPI-PILOT-01',status='DRAFT_NO_ADMITTED_PAIR',
        prospective_order=[dict(slot=i+1,arm=a,instance_id=None) for i,a in enumerate(['A','B','B','A'])],
        budget=dict(agent_seconds=300,counted_tools=60,command_seconds=120),
        candidate_pins=json.loads((PREVIOUS/'CANDIDATE_INTEGRITY.json').read_bytes()),
        tasks_bound=False,execution_authorized=False,single_repository_scope=True,
        independence='clean separate workspace/ADK session/Verifier sandbox for every arm; no Trace/Patch/output exchange'))
    write(HERE/'SAMPLE_DEPENDENCE_AUDIT.json',dict(selected_tasks=[],different_instance_ids_verified=None,
        Issue_identity_overlap=None,production_target_overlap=None,test_contract_overlap=None,
        reason='No native CPU evidence or selected pair; do not invent a semantic overlap assessment from IDs',
        future_method='After selection compare exact Issue hashes/text, base identities, native test node IDs/overlay contracts and relevant target paths without reading reference repairs; report overlap, never replace by subjective difficulty',
        inference_limit='Two FastAPI tasks are correlated within one repository; no cross-project generalization claim'))
    write(HERE/'CANDIDATE_INTEGRITY.json',(PREVIOUS/'CANDIDATE_INTEGRITY.json').read_bytes())
    write(HERE/'RESOURCE_PLAN.json',(PREVIOUS/'RESOURCE_PLAN.json').read_bytes())
    before=json.loads((HERE/'evidence/INITIAL_HISTORY.json').read_bytes())
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in before.items())
    write(HERE/'HISTORY_AUDIT.json',dict(base='582a016fb0c836222b6a3d653bb732e0c5e6130d',
        inherited_files_unchanged=len(before),passed=True,old_MECHANISM_01_unchanged=True,
        old_MECHANISM_02_unchanged=True,old_CPU110_unchanged=True,candidates_unchanged=True))
    diff=''.join(difflib.unified_diff((PREVIOUS/'screen.py').read_text().splitlines(True),
        (HERE/'screen.py').read_text().splitlines(True),fromfile='mechanism02/screen.py',tofile='fastapi_pilot01/screen.py'))
    write(HERE/'evidence/SCREENING_SOURCE_DIFF.patch',diff)
    documents={
    'README.md':'''# U-RE-V01-FASTAPI-PILOT-01

Independent FastAPI-only pilot; not a continuation or rewrite of blocked MECHANISM-01/02. Test the incremental EGV instruction within the same single31B Agent,300s/60tools/120s command. NoEGV retains ordinary testing. No cross-project or repair-rate improvement claim.

Current AUTH_READONLY_GO, but TASK_ADMISSION_BLOCKED / CPU_SAVE_UNCONFIRMED_STOP. One CPU-only SaveKernel dispatch; observer JSON parsing failed before a durable response receipt. No accepted version/native baseline/JUnit is available. Read-only reconciliation is inconclusive; no retry. Confirmed baseline count0; actual platform execution count unknown. All50 rows retain NOT_RUN/null as unobserved results,not confirmed failures or a proof that the platform never started work.

Selection committed77ad023 before SaveKernel, approved offline CPU build/evidence committed e6db9ac. All79 exclusions/exact50 ranks and both candidates unchanged. Final local suite14/14 passed; these are local integrity/controller checks,not official Linux baseline passes. No GPU,Agent,Gemma or formal Submission was requested. See EXECUTION_READINESS.md,AUTH_DIAGNOSIS.md,TASK_ADMISSION_REPORT.md and seals.
''',
    'AUTH_DIAGNOSIS.md':'''# Kaggle authentication diagnosis

At2026-10-21T06:12:19Z existing effective credentials initialized SDK successfully. IntrospectToken HTTP200 active=true,username matches expected owner; owner ListKernels HTTP200. AUTH_STATUS.json is AUTH_READONLY_GO. Both calls are read-only despite POST transport. No SaveKernel occurs in this diagnostic. Credential file bytes are equal before/after; no refresh,rotation,replacement,login,account switch,SDK update or environment modification. Credential values/headers/cookies are never persisted.

Python3.11.9,kaggle2.2.2,kagglesdk0.1.35. CLI installed console entrypoint is kaggle.cli:main from the same2.2.2 distribution; package __init__ constructs KaggleApi and calls authenticate on import,including CLI imports. Version/source hashes are in AUTH_STATUS.json; no separate CLI authentication/network attempt was needed.

Source path: __init__.py authenticate → _load_config(file then KAGGLE_ environment) → _authenticate_with_access_token → get_access_token_from_env → _introspect_token → read-only IntrospectToken. Effective access-token loading prefers notebook token-file (when in Kaggle),then KAGGLE_API_TOKEN value/path,then ~/.kaggle/access_token and access_token.txt. Legacy fallback requires username+key; a kaggle.json token field alone is not the explicit access-token loader. OAuth fallback can refresh/save/delete; this diagnostic blocks those mutations. No OAuth credentials file exists. Config username matches expected identity; env token equals config token but differs from the unused cached access-token file. The effective env token is accepted; cached-token validity is untested. Current files parse and are readable. Windows ACL exposure was not independently assessed.

Historical failure: old AUTH_AVAILABILITY.json records import failure but no raw introspection HTTP status/body. SDK _introspect_token collapses HTTP400/403/404 and inactive/missing-username replies into None; authenticate may then print help and SystemExit1. This is a lossy error path,not proof of expiry. Old root cause remains AUTH_UNKNOWN. Current success without intervention does not establish which historical credential/network/service condition changed. No AUTH_CONFIG_ERROR,AUTH_SDK_COMPATIBILITY_ERROR or expiry claim is justified. No same failed request was repeatedly attempted.

Separate CPU save failure is not an import authentication failure: after successful owner listing one SaveKernel request was sent,then the host response observer raised requests.exceptions.JSONDecodeError. Its raw HTTP response/status were not durably saved,so no server rejection/network cause is inferred. Reconciliation ListKernels HTTP200 plus GetKernelSessionStatus403 is inconclusive (missing/wrong/private resource can yield403). It does not invalidate current read-only authentication or prove Notebook save permission denied. No credentials action is currently needed; resolve uncertain Notebook acceptance before any new CPU save.
''',
    'TASK_ADMISSION_REPORT.md':'''# Native CPU admission: no verified result

Scope is now two distinct FastAPI instance IDs; all79 exclusions and exact50 ranks preserved. First8 remain14262,13537,15280,14266,14430,14487,13207,12942 with fastapi_ prefix. Max8 actual native checks,first two eligible,not easier/test-count selection. Selection commit77ad023 predates the CPU attempt.

One offline CPU-only Notebook save request at2026-10-21T06:17:01.841556Z,slug wudangdexiaodoashi/gemma4-u-re-fastapi-pilot01-cpu01; GPU=false,TPU=false,model inputs absent,Agent/model calls absent. Local upload audit checked186 payload members and exact approved runtime source/wheels. At SDK2.2.2 kernels_push the Notebook JSON is reserialized; WIRE_NOTEBOOK_IDENTITY.json proves source and embedded payload match the frozen build despite byte-format hash difference.

The response recorder called response.json before persisting HTTP metadata and raised JSONDecodeError. The execution-time host source is preserved at evidence/cpu_host_at_dispatch.py.txt and commit e6db9ac; HOST_SAVE_FAILURE.json is an honest terminal-status receipt,not reconstructed raw HTTP evidence. We do not know original response status/body. Search listing afterward returned[]; a bounded100-row owner listing has no exact match and direct status returned403. Neither proves absence or rejection. No repeat save or second Notebook was launched. Accepted version=null,confirmed native baselines=0,actual platform checks=null.

No JUnit,TaskResult,stdout or cleanup result exists for a new native baseline. Do not manufacture them. All50 rows remain NOT_RUN/null with platform_execution_status UNKNOWN. No selected tasks or admitted identity. No sample dependence or behavior correctness inference. Two eligible tasks have NOT been obtained; actual CPU environment admission remains blocked. No GPU algorithm result.

Next operational prerequisite is read-only reconciliation of this exact Notebook/owner in Kaggle UI or an authoritative accepted-version/status response. If it exists,collect that run's original outputs; do not resave. If platform confirms it was never accepted,record that evidence before planning a separately identified CPU attempt with the non-masking host observer. Do not change rank,exclusions,candidates or the max8 accounting.
''',
    'PAIR_PROTOCOL.md':'''# Future FastAPI-only paired protocol — DRAFT, NOT AUTHORIZED

No tasks are bound. After first two native-baseline-eligible distinct FastAPI IDs are selected under the precommitted max8 rule:Task1 A→B,Task2 B→A. Four independent runs ABBA,not fourAgents. A=unchangedNoEGV,B=unchangedFull; both singleGemma31BQATv2,sixofficialtools,300sharedseconds/60chargedtools/120commandseconds; output16384,thinking4096,seed17,sampling/include_thoughts remain frozen omitted values. Only Full adds the EGV instructions; NoEGV can test and revise normally.

Before future GPU inference bind exact Issue,base,snapshot,test-overlay/task-record and candidate/member SHA,model/tokenizer/wheels/Compiler/Runner/Verifier sources,Notebook/payload and actual request parameters. Separate clean workspaces,ADK sessions,Verifier sandboxes and evidence directories per arm. No Patch,Trace,test outputs,diagnostic findings or solution ideas transferred to another run. Evaluator-only tests stay evaluator-side. Same model service is acceptable only with independent contexts and verifiable idle/cleanup.

Report same-Issue,target-path,test-contract overlap without subjective replacement after outcomes. Same-project samples do not establish cross-repository generalization. Analysis retains all assigned tasks,including noEGVbehavior,algorithm failure,unknown/not_run; no selecting only counterexample-producing runs. No current native identities or resource window are admitted. GPU execution requires separate authorization after all gates.
''',
    'RESOURCE_BUDGET.md':'''# Resource and whole-run budget — hypothetical, not admitted

Rechecked inherited8940s plan:1200 model startup+600 dependency initialization+960 two baselines+4440 four workers+240 idle checks+600 shutdown/export+900 reserve. Each worker1110=180sandbox+300Agent+60Patch+180Verifier preparation+300native Phase2+90archive/cleanup. Baseline480=150prepare+300native tests+30cleanup. Agent caps alone total1200s. Proposed10000s window would leave1060s arithmetic headroom; no platform window approval exists.

Nothing measured here establishes these overhead caps. Current native CPU durations are unavailable,not zero. No current GPU quota/device/window/model/tokenizer/wheel/request routing/cleanup check was made. L4×4 device-hour proxy=9.933,not billed quota; billing units/rate unknown. Future first inference and every new arm need remaining-resource admission for all remaining registered work,including Verifier/JUnit/exports/cleanup. No shortening Phase2 to finish.

Formal scoring has an independent global budget risk:300s per-task caps do not guarantee12h completion for60/80/100/120/140 hidden tasks; failures cost time too. Hidden task count and Gemma P50/P90/P95/cap-hit/explicit-submit rates remain unknown. Preserve mechanism02 WHOLE_RUN_SCENARIOS.csv as labelled sensitivity assumptions,not empirical timeout probabilities. Native patch budget and Notebook wall limit may differ; no current official whole-run clock semantics are newly verified. T50057402336 timeout score remains null,not zero. No formal Submission recommended or requested.
''',
    'METRIC_DEFINITIONS.md':'''# Future metric definitions

Primary:native official resolved and complete tasks repaired under fixed total budget. Preserve native fields. Unknown/not_run never become confirmed false. Report paired Aonly,Bonly,both,neither plus incomplete outcomes; with n2 no population superiority/significance claim and no cross-project inference.

Secondary:Agent and Worker wall time; first production diff vs first independently evidenced correct Patch time (distinct);chargedtools vs LLMcalls vs HTTPdispatch/responses (distinct);received prompt/completion tokens with missing/cancelled usage null/partial;explicit successful submit ratio;first success→Agent end latency;post-success tools/repeat submissions;unchanged-source/input/environment no-information repeated tests;diagnostic residues.

EGV mechanism requires actual tool/behavior/provenance evidence:valid target assertions,workspace production execution,real counterexample,production revision caused by it,discriminating retest removing it,and relevant old-behavior regression. Model self-description never suffices. Attribute time/tools/tokens conservatively from events; ambiguity unknown. No counterexample denominator→loop rate null,not100%. Ordinary NoEGV tests/counterexample revisions count equally. Report added EGV cost and failed tasks,not only successful loops.
''',
    'STOP_RULES.md':'''# STOP rules

CPU launch requires AUTH_READONLY_GO,exact frozen protocol/rank/exclusions/candidates and audited GPU=false/TPU=false/no-model/offline build. Max8;select first2 eligible distinctIDs. Known evidenced environment blockers may be recorded and skipped under rule;unexplained identity,JUnit,source,test,Verifier,cleanup or evidence failure stops. No fake fixture,test edits,reference repair,network install,ranking change or extending sample count. All-pass baseline is non-discriminating.

Current STOP is CPU_SAVE_UNCONFIRMED_STOP. Exactly one SaveKernel dispatch recorded; initial HTTP response is unavailable,accepted version unconfirmed. Never repeat save on uncertainty. Do not infer baselines ran/did not run from missing outputs or ambiguous403. Collect existing authoritative status/output before any new CPU identity/attempt;account all observed checks within max8.

GPU defaults execute=false,gpu_authorized=false,formal_submission=false,gpu_algorithm_validated=false;unconditional stub exits before allocation/import/request. No GPU Notebook exists. Future CPU_GO still needs complete input/model/wheel/request/resource/window/cleanup gates and separate explicit GPU authorization. Ordinary algorithm failures must not become excuses to retry future assigned tasks. No formal score submission or LoRA authorized.
''',
    'HOST_OBSERVER_FIX.md':'''# Host-only response observation correction

Initial e6db9ac observer parsed JSON while constructing the save receipt. For a non-JSON response that throws before status is recorded and replaces the downstream SDK result/error. The old source/actual exception chain are retained. Original HTTP status/body cannot be recovered and are left null.

New response_observer.py captures timestamp/status/content-type/byte-count first;non-JSON marks json_response=false without throwing. It never copies arbitrary body/headers/cookies;whitelisted version/id/status only. Recorder file-write failure cannot change the SDK's original response/error path. cpu_host now always restores Session.send in finally. Local tests cover non-JSON502,empty204,JSON200,credential field exclusion and file-write failure. These are host regression fixtures,not Kaggle baseline results.

This correction was NOT deployed into a re-save/retry of this study. Frozen CPU Notebook,payload,rank,protocol and candidate bytes remain identical. Old host source is preserved and all actual Save evidence refers to it. Existing output-directory guard prevents another launch under cpu01. No second CPU request,hotfix into a running Notebook or GPU work occurred.
''',
    'EXECUTION_READINESS.md':'''# Actual gates and Q1–Q12

AUTH_READONLY_GO;CPU task admission BLOCKED;GPU resources UNKNOWN;GPU execution NOT_AUTHORIZED;GPU_ALGORITHM_VALIDATED=false. Local tests14/14 PASS (evidence/final_local_tests.log); these are not official native tests. Confirmed native baseline results0;actual platform execution unknown following save-receipt failure. No admitted pair.

|Question|Actual answer / evidence|
|---|---|
|Q1 auth failure stage/root|Old import authenticate/SystemExit1,root AUTH_UNKNOWN because no raw introspection response;current source chain verified;AUTH_DIAGNOSIS.md|
|Q2 auth recovered|Current SDK init+IntrospectToken200 active/expectedidentity+ownerListKernels200;AUTH_STATUS.json. No causal repair intervention claimed|
|Q3 credentials|No values uploaded/logged/replaced;file bytes equal;no refresh/account change;AUTH_STATUS.json,CPU_BUILD_AUDIT.json|
|Q4 independent study|New FastAPI-only namespace/new preregistration;old01/02 unchanged;HISTORY_AUDIT.json|
|Q5 exclusions/rank|All79 excluded and exact50rank bytes retained;EXCLUSION_AUDIT.json|
|Q6 prospective freeze|77ad023 policy/rank/source committed,pushed before Save; e6db9ac CPU build prior dispatch;SELECTION_PROTOCOL.json|
|Q7 actual baselines|Confirmed0,actual platform count unknown;one Save,no accepted version,parse error;HOST_SAVE_FAILURE.json,read-only reconciliation|
|Q8 eligible tasks|None demonstrated;all50 unobserved NOT_RUN/null;TASK_SCREENING_LEDGER.json|
|Q9 candidates|ZIP/member/Prompt/YAML unchanged;CANDIDATE_INTEGRITY.json|
|Q10 final pairing|ABBA/model300s/60/120 fixed as design;no task/snapshot/overlay identity bound;PAIR_PROTOCOL.json,TASK_IDENTITY_MANIFEST.json|
|Q11 execution bounds|Only CPU save requested,GPU=false/model sources absent;noAgent/Gemma/formalSubmission;SAVE_REQUEST.json,CPU_BUILD_AUDIT.json|
|Q12 GPU request|No:resolve CPU save,obtain two real native admissions,bind identities,then resource/model/request/window/cleanup and separate authorization;GPU_EXECUTION_DRAFT.json|

No authentication credential action is currently required. To resume operations first inspect exact Kaggle notebook slug/account and retrieve accepted version/status/output if any; ambiguous403 and truncated owner listing do not prove nonexistence. Do not blindly resave. No claimed EGV repair benefit or new leaderboard score.
'''}
    for name,text in documents.items():write(HERE/name,text)
    print(json.dumps(dict(status='TASK_ADMISSION_BLOCKED',auth=auth['status'],confirmed_baselines=0,selected=[])))


if __name__=='__main__':main()
