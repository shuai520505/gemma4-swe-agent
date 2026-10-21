"""Read actual bounded query receipts; unknown never becomes absent or failed."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
from .query import HERE,PILOT,write,TARGET


def classify(identity):
    if identity.get('exists') is True:
        if identity.get('accepted_version') and identity.get('source_matches_original'):
            return 'SAVE_ACCEPTED_CONFIRMED'
        return 'SAVE_EXISTS_EXECUTION_UNKNOWN'
    # No authoritative negative response was obtained by this implementation.
    # Empty pages,403,parse errors and missing versions never establish absence.
    return 'SAVE_STATUS_UNKNOWN'


def main():
    ledger=json.loads((HERE/'READONLY_QUERY_LEDGER.json').read_bytes())
    identity=json.loads((HERE/'NOTEBOOK_IDENTITY.json').read_bytes())
    assert ledger['identity_confirmed'] and ledger['credential_files_unchanged']
    status=classify(identity)
    assert status=='SAVE_STATUS_UNKNOWN','A discovered version needs original-output recovery before final reports'
    assert len(ledger['HTTP'])==5
    assert ledger['pagination']['complete'] and ledger['pagination']['unique_rows']==170
    assert ledger['control_private_read_confirmed']
    write('VERSION_OUTPUT_MANIFEST.json',dict(target=TARGET,accepted_version=None,version_created_at=None,
        source_sha256=None,run_status=None,outputs=None,TaskResult=None,JUnit=None,cleanup=None,
        recovery_status='NOT_EVALUATED_NO_CONFIRMED_VERSION',output_requests=0,downloads=0,
        confirmed_native_baselines=0,actual_platform_execution_count=None))
    write('ASSESSMENT.json',dict(status=status,outcome='D',target=TARGET,exists=None,accepted_version=None,
        platform_execution_count=None,confirmed_native_baselines=0,negative_acceptance_proof=False,
        positive_private_read_control=True,pagination_complete_for_API_visible_scope=True,
        API_visible_records=170,API_calls=5,new_SaveKernel=0,Notebook_runs_requested=0,
        GPU_requests=0,model_requests=0,formal_submissions=0,output_requests=0,
        CPU_admission='NOT_EVALUATED',GPU_authorized=False))
    write('WEB_UI_AUDIT.json',dict(status='WEB_UI_NOT_ACCESSIBLE',
        inventory='Only Codex in-app browser and MCP app surfaces available; no tabs at inventory time',
        navigation_url='https://www.kaggle.com/code/'+TARGET,
        attempted_actions=['createBrowserTab:read-only public URL','getTab:read-only existing tab state'],
        results=['Timed out waiting for tab1 to navigate','JS execution timed out; kernel reset'],
        account_identity=None,login_attempts=0,version_or_output_UI_evidence=None,
        run_or_save_clicks=0,interpretation='Tool/page access unavailable,not a404/absence/permission or Save outcome proof',
        chronology='Browser inventory/open attempt occurred before API query commit; plan file already existed; no resource mutation'))
    sources={}
    for dist,name in [('kaggle','kaggle/api/kaggle_api_extended.py'),
                      ('kagglesdk','kagglesdk/kernels/services/kernels_api_service.py'),
                      ('kagglesdk','kagglesdk/kernels/types/kernels_api_service.py')]:
        path=Path(importlib.metadata.distribution(dist).locate_file(name));sources[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    write('SDK_READ_SEMANTICS.json',dict(versions=dict(kaggle='2.2.2',kagglesdk='0.1.35'),source_hashes=sources,
        kernels_list='SDK defaults HOTNESS;page_size clamped100,mine=True→PROFILE;user default empty;wrapper returns kernels only and discards next_page_token',
        typed_pagination='ApiListKernelsRequest supports page,page_size,page_token;ApiListKernelsResponse exposes next_page_token. Actual replies had no token and ended at page2 rows70.',
        GetKernel='Read-only current metadata+source;ApiKernelMetadata._current_version_number preserves unknown vs getter default. No historical version-list method found in this installed kernels service.',
        GetKernelSessionStatus='Previous403 on exact identity;not repeated in this reconciliation because no new version/identity information.',
        kernels_output='CLI wrapper parses version but does not propagate it to ListKernelSessionOutput;do not assume exact-version retrieval from suffix alone',
        no_arbitrary_response_bodies_saved=True,no_guessed_endpoint_calls=True))
    documents={
    'README.md':'''# FastAPI pilot SaveKernel reconciliation01 — read only

Independent supplement on PR12 head2b3fb4d;new files only under reconciliation_01. Original sole CPU SaveKernel2026-10-21T06:17:01.841556Z is unchanged. No rerun,new version,CPU/GPU allocation,Agent/model,Submission or credential mutation authorized or attempted.

Outcome D:SAVE_STATUS_UNKNOWN. Authenticated owner confirmed;complete bounded API-visible pagination2pages170unique rows contains no exact target. Known own private GetKernel control succeeds;target GetKernel returns403. This is stronger access/scope evidence than the old first-page search,but still not authoritative resource nonexistence or rejected-save proof. No accepted version,run status or output was recovered. Native confirmed results0;actual platform execution count unknown.

Read QUERY_PLAN.md,READONLY_QUERY_LEDGER.json,ORIGINAL_REQUEST_AUDIT.json,SAVE_STATUS_ASSESSMENT.md,CPU_RECOVERY_REPORT.md andNEXT_ACTION.md. UI attempts timed out without a usable logged-in page. No output requests because no version was found. All historical/candidate bytes remain unchanged. JSONDecodeError is not used to reconstruct the lost HTTP response.
''',
    'SAVE_STATUS_ASSESSMENT.md':'''# Save status: SAVE_STATUS_UNKNOWN (Outcome D)

Original identity is exact:wudangdexiaodoashi/gemma4-u-re-fastapi-pilot01-cpu01;one SaveKernel at2026-10-21T06:17:01.841556Z,private=true,GPU/TPU=false. Request content's SDK-wire SHA3532c95dbd3288866f3324b608ddf1e5a744ad3b9e01fe125f3a77d88ef3f070 matches frozen Notebook JSON normalization. Original file SHA23bae74d9ddd67bdf52b23b31a03d25cbebc08dfabb731441c20bd126d384f66. No raw Save status/content-type/body/accepted version was retained. JSONDecodeError only proves observer parse failure;prior non-JSON framing is not a confirmed wire observation. This supplement corrects interpretation without editing old reports.

Actual new queries2026-10-21T11:58:18Z–11:58:24Z:5HTTP POST read operations. IntrospectToken200 active/expectedowner. Explicit PROFILE+owner+DATE_CREATED+all languages/types,no search,page_size100:page1=100,page2=70,no next token,170unique rows. Complete for this API-visible query scope;one returned ref does not have the owner prefix,which further limits treating it as an authoritative ownership inventory. Target exact match absent. No list titles/source/full bodies persisted.

Known own private GetKernel control200 returns exact requests-fixture CPU identity,id139838876,version1,is_private=true. Its metadata last_run_time is only the actual API field,not a version creation timestamp or fresh run evidence. Target exact GetKernel (a different endpoint from old403 session status) returns403 PERMISSION_DENIED,"Permission 'kernels.get' was denied". Previous same-parameter GetKernelSessionStatus is not repeated.

This excludes a blanket inability to authenticate/read any own private notebook at query time. It does not distinguish absent,hidden/inaccessible/unlisted/no-version resource or other per-resource restrictions. Neither complete paging nor403 nor missing receipt is authoritative negative acceptance evidence. No support confirmation or unambiguous NOT_FOUND exists. Therefore C is not met. No returned target identity/version exists,so A/B are not met. Preserve exists=null,accepted_version=null,actual platform execution count=null,confirmed native results0. Do not retry SaveKernel.
''',
    'CPU_RECOVERY_REPORT.md':'''# Original CPU output recovery

NOT_EVALUATED_NO_CONFIRMED_VERSION. No target resource/version was confirmed;per authorization no output request or download was made. VERSION_OUTPUT_MANIFEST.json contains null version,creation timestamp,run status,output,JUnit,TaskResult andcleanup. Existing positive-control resource is not the target;its version/source/results are not substituted.

No claim that original CPU tasks ran,failed or never ran. Confirmed new native baseline result count0;actual platform execution count unknown. No downloaded code executed. No new CPU/GPU Notebook or SaveKernel,new version,rerun,Agent or Gemma request. The private control query reads only existing metadata/source in memory;its source is not saved or supplied to anAgent.
''',
    'TASK_ADMISSION_SUPPLEMENT.md':'''# Task admission supplement — NOT_EVALUATED

No new TaskResult/JUnit/task/snapshot/overlay/cleanup records recovered. No task status can be promoted. All original79 exclusions,50ranked FastAPI metadata rows,max8 selection rule,ABBA design,300s/60chargedtools/120s command and candidates remain unchanged. No selected pair;do not infer failed/resolved values or fill counts with0 from absent evidence. Original unobserved records stay as they were. This supplements rather than overwrites PR12's CPU_SAVE_UNCONFIRMED_STOP.

If a preexisting version is later confirmed,bind its source/payload/current-or-specific-version identity first,then collect original outputs read-only,validate archive/file hashes,JUnit/TaskResult/native command,input identity andcleanup under the precommitted rule. Every observed check must be counted toward max8. No evaluator-only tests/outputs/reference material enter future Agent input or candidate ZIP. No GPU algorithm evidence exists.
''',
    'NEXT_ACTION.md':'''# Next action and remaining gates

Maintain SAVE_STATUS_UNKNOWN and STOP. No new SaveKernel under this task,even if later evidence proves rejection. Do not infer0 actual platform runs or resave because outputs are unavailable. Current CLI/SDK read authentication is usable;no credential replacement/refresh is needed or authorized.

What can resolve uncertainty:an already authorized working browser/account view showing exact Notebook/version history/output;an authoritative exact-resource response with explicit nonexistence and verified scope;or Kaggle support confirming the original request/time/slug. This task does not authorize sending messages to support. Browser read attempts here timed out;no login,bypass orRun/Save clicks occurred. Repeating the same403 query without changed conditions is not useful.

If an existing version is found,recover that version's artifacts read-only,not a rerun. If explicit non-acceptance is confirmed,preserve proof and wait for separately authorized,new-identity CPU execution planning. Never revise the old protocol/rank/exclusions or candidates. After real CPU admission still require full task/runtime hashes,GPU quota/4L4/window/model/wheels/request/cleanup admission and separate GPU execution authorization. No formal Submission or model calls authorized here.
''',
    'FINAL_QA.md':'''# Q1–Q10 and evidence

|Question|Actual conclusion / evidence|
|---|---|
|Q1 exact original identity?|Yes:slug/time/private CPU/wire source hashes and dispatch source pin verified;ORIGINAL_REQUEST_AUDIT.json|
|Q2 current account/read permission?|Yes:IntrospectToken200 expectedowner,ListKernels200,own private GetKernel200;READONLY_QUERY_LEDGER.json|
|Q3 Notebook exists?|Unknown;170visible rows no exact match,target GetKernel403,UI unavailable;not authoritative absence;SAVE_STATUS_ASSESSMENT.md|
|Q4 accepted version/time?|Not found;version/creation time null;NOTEBOOK_IDENTITY.json|
|Q5 execution/status?|Unknown;old status403 not repeated;no exact target version;VERSION_OUTPUT_MANIFEST.json|
|Q6 original outputs/JUnit/TaskResult?|None recovered;0output requests/downloads because no version;CPU_RECOVERY_REPORT.md|
|Q7 task checks/admission?|Confirmed results0;actual platform execution count null;NOT_EVALUATED,no selected task;TASK_ADMISSION_SUPPLEMENT.md|
|Q8 new resource/model work?|None:5read-only HTTP dispatches,0Save/Run/GPU/model/Submission;allowlist blocks mutations;READONLY_QUERY_LEDGER.json,guard tests|
|Q9 frozen identities preserved?|Yes:all5805 inherited files,ZIP/member/candidate/rank/79exclusions/50rows unchanged;HISTORY_AUDIT.json,INTEGRITY_MANIFEST.json|
|Q10 what now?|OutcomeD SAVE_STATUS_UNKNOWN,STOP,no retry;need authoritative version or explicit rejection proof;NEXT_ACTION.md|

Browser tool timing and API-visible inventory limits are preserved. Local guard/evidence tests are not official CPU task passes or Gemma algorithm validation. No new repair-rate or leaderboard claim.
'''}
    for name,text in documents.items():
        p=HERE/name
        with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    print(json.dumps(dict(outcome=status,confirmed_native_results=0,platform_execution_count=None,output_requests=0)))


if __name__=='__main__':main()
