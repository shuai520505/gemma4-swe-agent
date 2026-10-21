"""Seal honest blocked preparation; no invented CPU/GPU result or selected pair."""
import csv
import hashlib
import io
import json
from pathlib import Path
import platform
import shutil
import importlib.util
import subprocess
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name,value):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    data=value.encode() if isinstance(value,str) else (json.dumps(value,indent=2)+'\n').encode()
    if p.exists():
        assert p.read_bytes()==data,'Never rewrite evidence: '+str(p)
        return
    with p.open('xb') as out:out.write(data)


def main():
    protocol=json.loads((HERE/'SELECTION_PROTOCOL.json').read_text())
    ranked=json.loads((HERE/'RANKED_POOL.json').read_text())['rows']
    exclusions=json.loads((HERE/'EXCLUSION_LEDGER_V02.json').read_text())
    assert len({r['repo'] for r in ranked})==1
    auth=json.loads((HERE/'evidence/AUTH_AVAILABILITY.json').read_text())
    assert auth['existing_cache_auth_available'] is False
    assert not list((HERE/'results').rglob('SAVE_REQUEST.json')) if (HERE/'results').exists() else True
    rows=[]
    for r in ranked:
        rows.append(dict(r,exclusion_check=True,cpu_entered=False,status='not_run',
            reason='Kaggle import authentication blocked before Notebook save; pool also lacks a second repository',
            identity=dict(instance_id=r['instance_id'],repo=r['repo'],base_commit=r['base_commit'],issue_sha256=r['issue_sha256'],
                snapshot_sha256=None,test_overlay_sha256=None,task_record_sha256=None,status='METADATA_ONLY_NOT_RUNTIME_BOUND'),
            test_total=None,passed=None,failed=None,errors=None,skipped=None,xfailed=None,setup_errors=None,collection_errors=None,
            native_exit_code=None,error_category=None,environment_admitted=None,
            rejection_reason='not evaluated; no algorithm or environment failure attributed to task',evidence='evidence/AUTH_AVAILABILITY.json'))
    write('TASK_SCREENING_LEDGER.json',dict(experiment_id=protocol['experiment_id'],status='TASK_ADMISSION_BLOCKED',
        selection_commit='ac20c4745027c6068571292898b45c4ea0cfb630',selection_protocol_sha256=sha(HERE/'SELECTION_PROTOCOL.json'),
        candidate_pool_count=129,excluded_count=len(exclusions['excluded_task_ids']),ranked_count=len(ranked),max_checks=8,checked=0,selected=[],rows=rows,
        stop=['one_repository_only_in_conservative_available_pool','Kaggle_import_authentication_unavailable'],
        CPU_Notebook_saved=False,CPU_baselines_run=0,Agent_runs=0,model_calls=0,GPU_runs=0,formal_submissions=0))
    write('TASK_IDENTITY_MANIFEST.json',dict(experiment_id=protocol['experiment_id'],status='FINAL_PAIR_NOT_BOUND',selected=[],
        metadata_only=[r['identity'] for r in rows],metadata_pool_sha256=sha(HERE/'TASK_POOL_METADATA.json'),
        unresolved='No new official task mount/native baseline; final snapshot/test-overlay hashes and discriminating behavior not validated. No final pair exists.'))
    write('PAIR_PROTOCOL.json',dict(experiment_id=protocol['experiment_id'],status='BLOCKED_NO_PAIR_FROZEN',
        prospective_order=[dict(slot=1,task=None,arm='A'),dict(slot=2,task=None,arm='B'),dict(slot=3,task=None,arm='B'),dict(slot=4,task=None,arm='A')],
        candidate_A='U-RE-NoEGV',candidate_B='U-RE-Full',candidates=protocol['candidates'],
        task_selection='Never assign both tasks to the only remaining repository or free a reserved task to fill the design.',
        isolation='New independent session/workspace/verifier/output directory for every arm; no prior arm Patch/Trace/results in model inputs.',
        primary=['native_resolved','resolved_tasks_under_fixed_total_budget'],execution_authorized=False))
    old=json.loads((ROOT/'u_re/v01/GPU_EXPERIMENT_PROTOCOL_DRAFT.json').read_text())
    write('GPU_EXECUTION_DRAFT.json',dict(experiment_id=protocol['experiment_id'],status='BLOCKED_NOT_AUTHORIZED',
        execute=False,gpu_authorized=False,formal_submission=False,GPU_Notebook_generated=False,GPU_Notebook_saved=False,
        execution_stub_sha256=sha(HERE/'gpu_execution_stub.py'),selected_tasks=[],
        model='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',devices='4xNVIDIA L4',tensor_parallel=4,
        context_capacity=32768,context_safety=1024,model_files_expected_from_history=old['expected_model_files_from_frozen_S1'],
        wheel_hashes_expected_from_history=old['expected_wheel_hashes'],task_wheel_hashes_expected_from_history=old['expected_task_wheel_hashes'],
        versions_expected_from_history=old['official_versions'],generation=protocol['candidates']['generation'],
        budget=protocol['candidates']['budget'],agent_count=1,tools=['get_status','run_command','read_file','edit_file','write_file','submit_patch'],
        current_GPU_quota=None,current_quota_unit=None,actual_GPU_window_seconds=None,actual_GPU_model_route=None,
        runtime_model_hashes_verified=False,resource_admission=False,GPU_algorithm_validated=False,
        Notebook_sha256=None,payload_sha256=None,
        required_new_authorized_build='Unconditional frozen stub exits before imports. A future authorized build must be independently reviewed and frozen; never unlock this file in place.',
        future_start_gates=['two distinct admitted task repositories and exact input identities','current raw quota/units and4L4 capacity','approved complete session window',
            'model/tokenizer/all wheel SHA','official compiler/Runner and request semantics','context admission','HTTP lifecycle/partial usage','native JUnit','request idle and cleanup','separate explicit user authorization']))
    components=dict(model_startup=1200,dependency_initialization=600,two_baselines=960,four_workers=4440,
                    four_request_idle_checks=240,final_shutdown_export=600,safety_reserve=900)
    assert sum(components.values())==8940
    write('RESOURCE_PLAN.json',dict(scope='Hypothetical four-run planning caps, not measured U-RE/Gemma time or approved platform allocation',
        seconds=components,total_seconds=8940,proposed_window_seconds=10000,headroom_seconds=1060,
        each_worker=dict(sandbox_prepare=180,agent=300,patch_save_apply=60,verifier_prepare=180,Phase2=300,archive_cleanup=90,total=1110),
        each_baseline=dict(prepare=150,native_verification=300,cleanup=30,total=480),
        max_Agent_seconds_four=1200,wall_hours_proxy=8940/3600,four_L4_device_hours_proxy=4*8940/3600,
        quota_billing_rate=None,actual_CPU_baseline_times=None,actual_Gemma_P50=None,actual_Gemma_P90=None,actual_Gemma_P95=None,
        actual_GPU_session_window=None,current_quota=None,resource_admitted=False))
    table=[]
    for n in (60,80,100,120,140):
        for agent in (90,180,300):
            for setup in (5,20,60):
                for verifier in (30,120,300):
                    table.append(dict(tasks=n,assumed_average_Agent_seconds=agent,assumed_setup_seconds=setup,
                        assumed_verifier_seconds=verifier,patch_budget_seconds=n*(agent+setup)+600,
                        platform_wall_if_verification_serial=1200+n*(agent+setup+10+verifier)+900,
                        empirical_probability=None))
    buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
    write('WHOLE_RUN_SCENARIOS.csv',buf.getvalue())
    write('evidence/LOCAL_ENVIRONMENT.json',dict(queried_at_utc=datetime.now(timezone.utc).isoformat(),platform=platform.platform(),
        python=platform.python_version(),swegemma_available=bool(importlib.util.find_spec('swegemma')),
        adk_submission_available=bool(importlib.util.find_spec('adk_submission')),docker_executable=shutil.which('docker'),
        official_Linux_substitute_used=False,credential_values_logged=False))
    write('evidence/RULES_ACCESS.json',dict(queried_at_utc=datetime.now(timezone.utc).isoformat(),
        overview_url='https://www.kaggle.com/competitions/gemma-4-developer-agent/overview',overview_body_lines=0,
        code_requirements_url='https://www.kaggle.com/competitions/gemma-4-developer-agent/code-requirements',code_requirements_result='inaccessible via web tool',
        fresh_official_window_verified=False,private_scoring_clock_semantics_available=False,
        twelve_hour_total='User-stated competition constraint retained as scenario assumption, not newly verified page body'))
    write('README.md','''# U-RE-V01-MECHANISM-02 — independent blocked preparation

New study, not a continuation or replacement of U-RE-01. Frozen unchanged NoEGV/Full candidates, one31B Agent,six tools,300s/60 charged tools/120s command. Primary question is the incremental EGV instruction's net repair/cost effect, not testing vs no testing. NoEGV can run ordinary tests and revise from counterexamples.

Actual status: TASK_ADMISSION_BLOCKED.129 metadata tasks audited,79 conservatively excluded,50 remaining—all FastAPI. Thus the distinct-repository design is currently impossible. Kaggle SDK additionally cannot authenticate from current/local cached credentials; no CPU SaveKernel request was sent. Official native CPU baselines run=0; all test counts/identities requiring runtime remain null. Local prospective-policy tests pass; they are not native task or model results.

Selection rule/source/ledger/ranking were committed as ac20c4745027c6068571292898b45c4ea0cfb630 before attempted CPU work. CPU-only payload frozen in98efddb72733f2b76aefc6a340a513494a0b9527. No algorithm/candidate/task-selection rule was loosened after seeing pool composition or authentication failure. Four ignored historical archives were recovered with exact existing SHA and honestly labelled, before the rule freeze; see evidence/HISTORICAL_ARTIFACT_RESOLUTION.json and retained initial pre-freeze source attempt.

Read EXECUTION_READINESS.md, TASK_ADMISSION_REPORT.md and EXCLUSION_LEDGER_V02.json. No selected GPU pair is claimed. GPU JSON and unconditional stop stub are specifications only; no GPU Notebook was generated/saved, no Gemma inference or formal submission. Old experiment, PR10 diagnosis, CPU02's110/110, CPU03 failure and all candidates remain unchanged.
''')
    write('TASK_ADMISSION_REPORT.md','''# Actual task screening — BLOCKED / zero new baselines

The prospective algorithm was committed before any new baseline: ac20c47, full selection source SHA in SELECTION_PROTOCOL.json. Input metadata129, exclusions79, eligible-to-screen50, all from fastapi/fastapi. Other supplied repositories are entirely excluded by inherited used/reserved/analyzed/uncertain records. Explicitly:48 Rich,13 Requests,1 HTTPX and17 FastAPI tasks are excluded. This is a conservative availability audit, not a statement that all excluded tasks had Gemma runs or reference exposure. Unknown flags remain UNKNOWN. The audit inspects730 unique relevant Git blobs from verified PR1–10 heads plus28 inherited source pins;4 of those pins identify ignored local archives recovered byte-for-byte rather than tracked objects.

The frozen first eight ranks are fastapi_14262,fastapi_13537,fastapi_15280,fastapi_14266,fastapi_14430,fastapi_14487,fastapi_13207,fastapi_12942. They are **not executed or selected**. Ranking uses only the declared SHA prefix+ID; no Issue difficulty, repair outcome/test count/reference patch is a ranking input. Reusing another repository's reserved task or changing the exclusion union would violate this freeze.

CPU-only Notebook source was built and hash-frozen, then the attempted launcher stopped at `from kaggle import api`: SDK authentication could not validate current credentials. A distinct existing cached access-token source also failed import authentication; no new credential/account was created. No SaveKernel request or CPU task command was issued. The launcher's owner-listing/save operations occur only after successful import in the same checked Python process, so there is no shell fallthrough or ambiguous accepted version. AUTH_AVAILABILITY.json records the actual status without secrets. Initial terminal help was not persisted as a raw file; the saved receipt is the subprocess status/source summary, not a fabricated HTTP response.

Local Windows has no installed official swegemma/adk-submission and is not used to imitate Linux. No mock baseline is substituted. TASK_SCREENING_LEDGER.json retains all50 ranked rows, cpu_entered=false,status=not_run,test statistics=null; zero failures/resolved are inferred. No JUnit, native TaskResult or clean-baseline identity exists for a new task in this study. TASK_IDENTITY_MANIFEST.json is metadata-only with snapshot/test-overlay hashes null and selected=[]; this is deliberately not a completed runtime identity freeze.

Result: TASK_ADMISSION_BLOCKED for two independent reasons—one-repository pool and unavailable Kaggle CPU authentication. Current credentials becoming usable alone would not solve repository diversity. Preserve max8 and original exclusions; no sample expansion or reordering. No further Requests dependency investigation or task replacement was performed.
''')
    write('PAIR_PROTOCOL.md','''# Prospective pair design — no task pair registered

PAIR_PROTOCOL.json leaves all four task slots null. If a later independently reviewed/registered study can admit two distinct repositories, the intended order is task1 NoEGV→Full, task2 Full→NoEGV. This study has no qualified pair and must not fill slots silently after its blocked outcome.

Both arms keep byte-identical frozen candidate configurations except the existing EGV Prompt block. Same31B QATv2,oneAgent,sixofficialtools,300s/60chargedtools/120s commands,output16384,thinking4096,seed17; sampling/include_thoughts remain omitted as frozen, not silently changed to true/default estimates. Context32768/safety1024 are planned common research admission settings. Separate sessions, working trees, evaluator sandboxes and result paths per arm; same task inputs/native tests. Agent receives only public Issue and clean source, never evaluator overlay, other arm Patch/Trace/output or reference answers. Ordinary algorithm failures continue unless actual infrastructure/integrity/resource STOP.

Only two tasks are independent units, not tool calls/test counts. Report complete paired outcomes and discordant pairs with unknown/not_run retained. No population superiority claim or formal leaderboard inference from a two-task mechanism study. NoEGV can execute ordinary tests/counterexample repair; this is an EGV instruction increment comparison.
''')
    write('METRIC_DEFINITIONS.md','''# Predeclared endpoints and evidence rules

Primary: unmodified native resolved, and complete resolved task count under the same total budget. Preserve native resolved/test_exit_code/output and add separate resolved/failed/unknown/not_run audit fields. Unknown/not_run are never false. Compare A-only success,B-only success,both success,both failure,plus incomplete pairs. Give complete-pair denominator; do not present an incomplete run as overall resolution rate. No model outcomes exist in this study.

Secondary: Agent and worker wall clocks,first actual production diff,first candidate with externally supported correctness evidence,charged tool count,LLM calls,HTTP dispatch/response/terminal counts,actual response prompt/completion usage,explicit successful submit,first-submit→Agent-end gap,post-submit tools/duplicate submits,unchanged-condition repeat checks,and diagnostic residue. Distinguish successful file edit from correct fix. Successful submit is not an immediate Runtime stop guarantee; count its extra actions rather than patching the official tool.

EGV events require actual tool/output/source support: discriminating assertion targeting Issue behavior,current workspace execution,valid counterexample,subsequent relevant production revision,and actual targeted retest eliminating it. Record old-behavior checks and added regression failures. Unsupported self-authored expectations are not proof of bad production code. Test text/self-report alone is not mechanism evidence. NoEGV can exhibit these behaviors too; annotate both arms symmetrically. Grade direct assertion/provenance,indirect evidence,import-only and unknown separately.

Count legitimate repeats after changed source/input/hypothesis separately from identical no-information checks. Attribute EGV time/tool/token increments only when traces permit; otherwise unknown. Usage without a response stays null/partial and is never filled with zero. Report observed totals and missingness,not falsely complete cost. Cost per success is undefined with zero confirmed successes. Track independent task pairs,not per-test/model-call pseudoreplicates. P50/P90/P95,cap fraction and useful-revision rate need real Gemma data and remain null here.
''')
    write('RESOURCE_BUDGET.md','''# Four-run research budget and separate formal-run risk

RESOURCE_PLAN.json newly totals8940 seconds,not the historical8640 and not an approved window: model startup1200,dependency setup600,two clean baseline budgets960,four workers4440,four idle checks240,shutdown/export600,reserve900. Each worker1110=prepare180+Agent300+Patch60+Verifier prepare180+nativePhase2 300+archive/cleanup90. Each baseline480=prepare150+verification300+cleanup30. All are conservative planning assumptions/caps,not measured U-RE or guaranteed upper bounds. They cannot excuse shortened native verification. Proposed10000s window leaves1060s,only if actually granted and still available from session start. Four Agent caps total1200s. Device-hour proxy4*8940/3600=9.93 L4-hours; actual billing/quota units and multiplier are UNKNOWN.

Before any future model inference and every arm: verify enough actual remaining window/quota for all registered remaining workers,baselines,request recycle and final archive. Include time already spent installing/hashing/loading. Stop on unverified idle or cleanup,unknown quota units,insufficient window or wrong GPU. No changing arm order,run count or native verifier to fit. GPU readiness is not granted by arithmetic. Current GPU allocation/quota/window/model routing and all GPU runtime hashes are NOT_QUERIED/NOT_VERIFIED; CPU auth is blocked. No GPU Notebook exists. Official overview returned zero body lines and code-requirements page was inaccessible; this is not fresh confirmation of platform limits (evidence/RULES_ACCESS.json).

Formal scoring is a separate No-Go. WHOLE_RUN_SCENARIOS.csv has135 explicitly hypothetical scenarios across60/80/100/120/140 tasks,averageAgent90/180/300s,setup5/20/60s,serialVerifier30/120/300s. Patch-envelope model=N*(Agent+setup)+600 reserve; platform model=1200+N*(Agent+setup+10cleanup+Verifier)+900export. Actual placement/overlap of these clocks in private scoring is unverified. The user-stated12h=43200 is a planning constraint,not newly verified page text. Per-task Agent time excludes setup in published Harness semantics; that does not establish the global/private Notebook clock.

At300s averageAgent and20s setup,the patch envelope is19800/26200/32600/39000/45400s for60/80/100/120/140 tasks;140 already exceeds43200. With serial120s Verifier,the platform model is29100/38100/47100/56100/65100s;100 tasks exceeds12h. These are sensitivity calculations,not empirical probabilities. Include unsuccessful/capped tasks in averages; do not infer distributions from old simple tasks. Actual U-RE P50/P90/P95,cap fraction,submit rate,verification time and cost/success remain unknown. Keep original GLOBAL_BUDGET_ASSESSMENT.md and360-scenario historical evidence untouched. Formal57402336 timeout/PublicScore=null is not proof of500s or EGV causation. No formal submission is recommended without representative complete-run throughput and confirmed clock/limit semantics.
''')
    write('STOP_RULES.md','''# STOP and non-promotion rules

Selection freeze: original candidates/config/source hashes must match; reference/evaluator data never enters Agent input. Max8 actual CPU checks and two different repositories are fixed. Explained known Requests recursive provider blockers are rejected with raw evidence and do not repeat PR10 investigation. Non-discriminating all-pass bases are rejected. Missing/conflicting JUnit,unexplained collection/setup/internal/executor failure,identity/source drift,wrong workspace execution,cleanup failure or unresolved severe history conflict causes global STOP. Do not change criteria,expand the pool/release reservations/reorder/change tasks based on results.

Current stop: all50 remaining tasks have the same repository and Kaggle authentication blocks CPU launch. Checked=0; no task outcome inferred. No fully registered pair or GPU-ready state exists. Old U-RE-01 remains DRAFT_BASELINE_BLOCKED.

Future GPU requires a separate authorized build,actual quota/units,4L4/TP4,model/tokenizer/wheel/task identities,request generation/context semantics,full native Phase2/JUnit,HTTP cancellation/usage,server request recycle and process/sandbox cleanup. Frozen stub always exits before imports and the JSON says execute=false/gpu_authorized=false/formal_submission=false. No GPU Notebook may be saved now. A normal assertion failure,Agent syntax regression,omitted verification,repeat submit or cap exhaustion is an algorithm observation,not an excuse to retry/change task. Missing usage stays partial. Failed integrity/resource gates stop remaining arms; preserve unknown/not_run and do not splice history. No official scoring tool/Runner modification.
''')
    write('EXECUTION_READINESS.md','''# Final gate table and Q1–Q12

| Gate | Actual status |
|---|---|
| Frozen U-RE candidate integrity |PASS; original ZIP/member/Prompt/YAML hashes unchanged |
| Historical U-RE CPU110/110 |Unchanged historical compatibility evidence,not rerun |
| New local prospective policy tests |PASS6/6 before freeze; final policy/readiness suite PASS13/13; no native task/model inference |
| Metadata/exclusion/ranking freeze |Committed ac20c47 before attempted CPU work |
| Two-repository candidate availability |BLOCKED:50/50 remaining tasks are FastAPI |
| New official Linux CPU baselines |NOT_RUN:SDK authentication blocked before save |
| Final paired task identities |NOT_BOUND; selected=[] |
| GPU resource/window/model/request runtime |UNKNOWN/NOT_VERIFIED |
| GPU execution authorization |NOT_AUTHORIZED |
| Algorithm evidence |GPU_NOT_TESTED; no repair-rate claim |

| Question | Answer / evidence |
|---|---|
| Q1 independent study |Yes,newMECHANISM-02 namespace/basePR10; old protocol and diagnostic unchanged; HISTORY_AUDIT.json |
| Q2 frozen ZIPs |Both exact ZIP+member pins retained; CANDIDATE_INTEGRITY.json |
| Q3 historical/reserved tasks |PR1–10 actual heads,730 scoped Git blobs,28 inherited pins including4 SHA-matched local archives;79 exclusions. Unknown model/reference history kept UNKNOWN; EXCLUSION_LEDGER_V02.json |
| Q4 prospective freeze |Yes,ac20c47 contains source/rules/pool/ledger/ranking before attempted CPU; SELECTION_PROTOCOL.json |
| Q5 actual CPU checks |0. All50 not_run,statistics=null; launcher failed API import before save; AUTH_AVAILABILITY.json and TASK_SCREENING_LEDGER.json |
| Q6 two admitted repositories |No; all50 available metadata rows are FastAPI,and no new native baseline ran |
| Q7 final input hashes |No selected runtime identity. Metadata Issue/base hashes exist; snapshot/overlay/task-record remain null; TASK_IDENTITY_MANIFEST.json |
| Q8 fairness/order |Unchanged300s/60tools/model/generation/isolation declared;ABBA is a proposed pattern only,task slots null; PAIR_PROTOCOL.json |
| Q9 reproducible GPU plan/resource budget |Specification,metrics,STOP and CPU build are preserved;8940s hypothetical plan. No executable authorized GPU build or admitted window |
| Q10 remaining gates |Task diversity+native CPU admission/auth,full identity freeze,current quota/4L4/window,model/tokenizer/wheels/route/request/cleanup and separate authorization |
| Q11 zero GPU/inference/submission |Yes. No CPU Notebook save either; only local policy tests and metadata/source checks |
| Q12 promote or block |Continue TASK_ADMISSION_BLOCKED; not GPU_READY_FOR_AUTHORIZATION. Restoring auth alone cannot make the one-repository pool satisfy this protocol |

Do not silently remove conservative old exclusions to obtain a second repository. A future exposure/reservation review or expanded public pool must be separately justified/versioned before any new baseline,without rewriting this blocked registration. No need to request GPU execution now.
''')
    # Exact archive membership audit, not only top-level ZIP hash.
    import zipfile
    candidates={}
    for arm in ('noegv','full'):
        p=ROOT/f'u_re/v01/submission_{arm}.zip'
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            members={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}
        expected=protocol['candidates']['candidates'][arm]
        assert sha(p)==expected['zip_sha256'] and members==expected['members']
        candidates[arm]=dict(zip_sha256=sha(p),members=members,CRC=True)
    write('CANDIDATE_INTEGRITY.json',dict(passed=True,candidates=candidates,source_commit='cd7fe8e19950003b59819c7accf7292ce2e151b9',same_model_tools_budget=True))
    before=json.loads((HERE/'evidence/INITIAL_HISTORY.json').read_text())
    assert all(sha(ROOT/p)==h for p,h in before.items())
    write('HISTORY_AUDIT.json',dict(passed=True,base='794e5fc3b487b0d7a57002268fac88aa12a34851',inherited_files_unchanged=len(before),
        original_U_RE_01_status='DRAFT_BASELINE_BLOCKED',old_protocol_sha256=sha(ROOT/'u_re/v01/GPU_EXPERIMENT_PROTOCOL_DRAFT.json'),
        PR10_diagnosis_unchanged=True,CPU02_110_unchanged=True,CPU03_failure_unchanged=True))
    print(json.dumps(dict(status='TASK_ADMISSION_BLOCKED',CPU_baselines=0,remaining_pool_repositories=1,generated_scenarios=len(table))))


if __name__=='__main__':main()
