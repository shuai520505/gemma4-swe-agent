"""Safe derived readiness report. Never invent unexecuted GPU outcomes."""
import json
from pathlib import Path
import re
import subprocess
from .prepare import HERE, ROOT, MEER, put, sha


def run():
    manifest=json.loads((HERE/'EXECUTION_MANIFEST.json').read_bytes())
    build=json.loads((HERE/'PAYLOAD_BUILD.json').read_bytes())
    cpu=json.loads((HERE/'CPU_BINDING_ACCEPTANCE.json').read_bytes())
    dynamic=json.loads((HERE/'readonly01/preflight/DYNAMIC_PRECHECK.json').read_bytes())
    rows=[dict(**row,status='NOT_RUN',actual_Agent_session=False,native_resolved=None,
          official_patch_submitted=None,final_patch_sha256=None,TaskResult_sha256=None,JUnit_sha256=None,
          reason='Gate F: no separate six-session GPU authorization')
          for batch in manifest['batches'].values() for row in batch]
    put('SESSION_RESULTS.json',dict(experiment_id=manifest['experiment_id'],status='GPU_READY_NOT_AUTHORIZED',
        real_Gemma_sessions_completed=0,real_Gemma_model_requests=0,sessions=rows))
    put('NATIVE_OUTCOMES.json',dict(outcome='NOT_RUN',sessions=[{k:r[k] for k in ('run','instance_id','arm','status','native_resolved','TaskResult_sha256','JUnit_sha256')} for r in rows],
        A_resolved=None,B_resolved=None,C_resolved=None,denominator_completed=0,
        baseline_failures_are_not_Agent_failures=True))
    put('MECHANISM_EVENTS.json',dict(status='NOT_RUN',analysis_category='INCONCLUSIVE',
        sessions=[dict(run=r['run'],arm=r['arm'],skill_discovered=None,skill_invocations=None,
             executed_assertions=None,verdicts=None,duplicate_checks_suppressed=None,stale_evidence=None,
             acted_on_evidence=None,mechanism_bypassed=None) for r in rows],
        Skill_invocation_rate=None,mechanism_bypass_frequency=None,
        prior_and_current_scripted_CPU_results_excluded=True))
    put('RESOURCE_USAGE.json',dict(GPU_Notebooks_dispatched=0,GPU_SaveKernel=0,real_Gemma_sessions=0,
        real_Gemma_model_requests=0,formal_Competition_Submissions=0,
        received_real_Gemma_tokens=None,real_Gemma_latency_seconds=None,GPU_billing_seconds=None,
        CPU_Notebooks_dispatched=1,CPU_SaveKernel=1,CPU_Notebook_id=cpu['Notebook_id'],CPU_version=1,
        CPU_status='COMPLETE',CPU_MODEL='SCRIPTED_ONLY',CPU_owned_sessions=3,
        CPU_scripted_HTTP_requests=sum(r['actual_HTTP_requests'] for r in cpu['records']),
        account_quota_snapshot=dynamic['raw_quota'],remaining_report_seconds=dynamic['remaining_report_seconds'],
        snapshot_last_HTTP_utc=dynamic['HTTP'][-1]['utc'],
        accounting_limitations=['Account-level quota is not a per-experiment bill',
        'No GPU allocation means hardware/model/real token costs remain unmeasured',
        'SDK profile objects did not expose usable enable_gpu values: empty account_GPU_sessions is not proof of no active experiment',
        'PR27 Batch2 remains UNKNOWN; exact status read is403, not proof of rejection']))
    put('RAW_ARCHIVES.json',dict(raw_contents_public=False,archives=[dict(
        purpose='Targeted shared GPU worker/Guard/Skill CPU validation',Notebook_id=cpu['Notebook_id'],version=1,
        path=cpu['private_archive_path'],sha256=cpu['archive_sha256'],bytes=cpu['archive_bytes'],CRC_valid=True)],
        inherited_source_proofs=manifest['evidence']))
    # Check historical MEER files byte for byte; new files are outside its scope.
    historical=json.loads((MEER/'INTEGRITY_MANIFEST.json').read_bytes())
    for n,h in historical['files'].items():
        assert sha((MEER/n).read_bytes())==h,n
    changes=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
    assert all(n.startswith('meer/v01/gpu01/') for n in changes)
    baseline='d5c60b4a6490cc54c0eb9c65de7a966c2cc1fced'
    commits=subprocess.check_output(['git','log','--format=%H %s',baseline+'..HEAD'],cwd=ROOT,text=True).splitlines()
    put('SOURCE_REVIEW.json',dict(repository='shuai520505/gemma4-swe-agent',
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        PR31_head_at_start='749d0a488f0e1ea6da2a324c30b0f02e531f40ef',PR31_open_draft_unmerged=True,
        PR30_head_at_read=baseline,PR30_open_draft_unmerged=True,
        history_files_rehashed=len(historical['files']),ancestor_commits_since_PR30=commits,
        intervening_task_usage_review=dict(scope='Available project result/execution/metrics JSON and branch commits since PR30; not a global claim about all account/private activity',
            matching_result_files=['u_re/v04/experiments/prospective_admission_01/TASK_ADMISSION_RESULTS.json',
                                   'u_re/v04/experiments/prospective_admission_01/NATIVE_BASELINE_RESULTS.json'],
            new_Gemma_exposure_found=False,external_activity_requires_runtime_recheck=True)))
    (HERE/'GPU_PREFLIGHT.md').write_text(f'''# GPU_READY_NOT_AUTHORIZED

Read source PR31 `749d0a4` and its actual open/unmerged PR30 base `d5c60b4`; continued the existing MEER branch. This task explicitly does not provide Gate F authorization. No GPU Notebook was saved, no Gemma inference occurred, and no formal competition submission was created.

| Gate | Evidence-backed status | Remaining condition |
|---|---|---|
| A artifact | PASS: all three original ZIPs, CRCs, member bytes and extracted candidate files rehashed | Recheck at authorized dispatch |
| B task | PASS within available project records: actual private admission archive re-read; source/version-bound native TaskResult/JUnit, input identities, aliases and cleanup checked | Independent external/intervening activity recheck at dispatch; no task substitution |
| C environment | STATIC_PINS_AND_CPU_PASS: exact official wheels/source, generation, task environment, six tools/Skill schema and shared Guard bound | Allocated GPU CUDA/PyTorch/vLLM, eight actual model/tokenizer/template hashes and real Gemma Skill compatibility are RUNTIME_RECHECK_REQUIRED |
| D resources | READ_ONLY_PLAN_ONLY: quota API reports {dynamic['remaining_report_seconds']} seconds available and0 reserved | Actual4L4 allocation, complete10000s window and conflicting-job clearance are not established by a quota response |
| E execution | PREPARED; targeted shared Worker/Guard/Skill CPU PASS on {cpu['Notebook_id']}/v1 | GPU-only coordinator/model lifecycle NOT_RUN; owner grant must be inserted and final outer Notebook bytes/once-only dispatch claim frozen before any future save |
| F authorization | **NOT_AUTHORIZED** | Separate explicit owner authorization for these six sessions, both batches, exact artifacts and resource ceilings |

Gate C/D are not falsely promoted to an actual GPU runtime pass. `NOTEBOOK_BUILD.json` hashes both un-dispatched outer Notebook templates; `PAYLOAD_BUILD.json` pins the shared205-file production closure. Both templates deliberately stop on missing authorization before dependency installation or model access. There is no GPU dispatch function in this addition. Trusted operator must verify the owner grant: a model-created JSON flag is not authorization.

Live read-only evidence: `readonly01/preflight/DYNAMIC_PRECHECK.json` and finite status read. The model API lists all8expected filenames, which is availability metadata, not content-hash verification. Its quota is an account snapshot, not this experiment's bill. The inherited profile filter produced an empty GPU list because usable enable_gpu fields were absent; it is explicitly not proof of no active job. PR27 Batch2 exact status remains403/UNKNOWN, unchanged. These readings must be refreshed before an authorized dispatch.

The selected tasks retain original negative baselines. fastapi_14459 has2ordinary snapshot assertion failures plus2exact paired duplicate finalizer records and0independent environment errors under the unchanged PR26 reader; no raw error was removed and no old verdict was rewritten.
''',encoding='utf-8')
    (HERE/'INTEGRITY_AUDIT.md').write_text(f'''# Independent integrity audit

All three frozen candidate ZIP digests match the requested A/B/C values. No candidate was regenerated. All member hashes and extracted source bytes match. B/C differ only in the frozen skill script; A/B also differ in the SkillToolset interface, so B/C remains the primary mechanism contrast.

Re-read original CPU140511729/v1 private archive `{manifest['evidence']['CPU_archive_sha256']}` and all196source members, real TaskResult/JUnit/patch hashes, helper verdicts and the bypass counterexample. Re-read actual PR30 admission140412111/v1 archive `{manifest['evidence']['admission_archive_sha256']}` and independently hashed both tasks' native outputs. Re-read PR30 final production acceptance source closure from its private archive; no summary boolean substitutes for these bytes.

New shared production payload `{build['payload_sha256']}`. Targeted CPU{cpu['Notebook_id']}/v1 confirms every shared production member against that payload, official Worker+common Context Guard+Compiler/ADK/Runner+chroot+all six tools+native SkillToolset+patch/submit+trusted native TaskResult/JUnit+cleanup. Scripted transport is CPU-only; the GPU Worker explicitly rejects it. The GPU coordinator is source-constructed from GPU03 using asserted exact anchors; import paths are absolute after package rebinding. Its GPU lifecycle has not been executed in this task.

The only runtime validation change is to a research-layer six-entry-only check so it can accept the official SkillToolset already proven by MEER CPU03. Official Compiler, Runner, tools/schema/counting, generation settings, native Verifier and frozen PR26 result reader are unchanged. The same Guard is used for A/B/C. The HTTP observer still uses a sibling directory until Runner creates its exclusive Agent output directory.

The initial undispatched local build had two package-relative coordinator imports that would resolve incorrectly after rebinding. Corrected before dispatch; original bytes remain in `undispatched_build01.zip`,0SaveKernel. CPU dispatch's original UNKNOWN_STOP remains intact; resource/version/source/output confirmation is read-only, not a rewritten receipt or duplicate save.

Historical MEER manifest: {len(historical['files'])}files rehashed unchanged. Only new meer/v01/gpu01 files are committed. Private raw HTTP, native tests, complete patches and model/task traces are outside Git; public data is source, hashes and derived metadata. Original PR27 UNKNOWN is preserved.
''',encoding='utf-8')
    (HERE/'COMPARATIVE_ANALYSIS.md').write_text('''# INCONCLUSIVE — six real-Gemma sessions NOT_RUN

| Task | A EGR | B MEER | C Prompt-only |
|---|---|---|---|
| fastapi_14297 | NOT_RUN / null | NOT_RUN / null | NOT_RUN / null |
| fastapi_14459 | NOT_RUN / null | NOT_RUN / null | NOT_RUN / null |

Primary B/C mechanism contrast, B/A deployment contrast and C/A interface-overhead contrast have no real-Gemma observations. Skill adoption rate, bypass frequency, relative tokens/latency, meaningful verification, repair changes and paired Native Resolved differences are UNKNOWN. Zero completed sessions is not0/2 repair performance. Prior scripted successes are excluded.

`measure.py` is a post-run observer, never a runtime controller. It preserves missing usage as null, derives invocation/verdict events from actual tool responses and source-change intervals from actual filesystem observations. Issue relevance, meaningful regression coverage, semantic claims and whether a model acted on evidence require human raw-trace review; the observer does not invent those measurements. Local SUPPORTED is never substituted for Native Resolved. Normal submit calls are counted separately from independently confirmed successful submissions.

Existing CPU bypass evidence shows the skill remains optional. The next authorized matched experiment should first measure actual Skill adoption and B/C behavior. Do not redesign global orchestration before those observations. No evidence currently supports replacing EGR or claiming a repair-success improvement.
''',encoding='utf-8')
    (HERE/'FINAL_DECISION.md').write_text(f'''# GPU_READY_NOT_AUTHORIZED

Prepared the frozen six-session comparison without changing artifacts or task order. A/B/C ZIP digests remain the preregistered originals. Main comparison B/C; deployment B/A; interface cost C/A. Existing PR31 remains draft, stacked on unmerged PR30.

Independent artifact/task/archive checks pass. A targeted actual Kaggle CPU run {cpu['Notebook_id']}/v1 COMPLETE validates the new research Worker compatibility adapter with the shared Context Guard, official single-Agent Runner and Skill execution for all three arms. It produces owned synthetic patches, native true/JUnit and clean shutdown only under SCRIPTED_ONLY communication. It is not real Gemma repair evidence or an actual GPU lifecycle pass.

Frozen shared production ZIP SHA256 `{build['payload_sha256']}`. CPU raw archive SHA256 `{cpu['archive_sha256']}`. All205shared production members rechecked against recovered CPU output.8offline fail-closed/artifact/Guard/binding tests pass. Actual scope this task:1CPU SaveKernel/3owned scripted sessions,0GPU SaveKernel,0realGemma sessions/requests,0formalCompetitionSubmissions.

1. A artifact gate PASS. B task gate PASS within the reviewed project records and original evidence. C pinned environment/CPU compatible, actual model/runtime checks pending. D readonly quota/availability metadata only, actual allocation/window/conflict checks pending. E source-bound templates/worker prepared and CPU-validated; final external owner-grant binding/outer Notebook SHA and exclusive dispatch record remain required. F separate authorization ABSENT.
2. Actual GPU inference: NO. Six real sessions:0completed,allNOT_RUN. No Native Resolved outcomes for A/B/C.
3. Skill invocation rate/bypass frequency, relative token/latency costs and repair differences:UNKNOWN,not0. There is no real-Gemma evidence of improvement over EGR.
4. Next priority is the existing matched Skill-adoption/evidence-use experiment once explicitly authorized and dynamic gates pass. A global execution controller would be a new separately audited mechanism,not part of this frozen experiment.
5. Do not replace the current competition candidate. No formal submission was made or changed. Preserve failures, native negative baselines and prior PR27 Batch2UNKNOWN. A403status lookup is not proof of rejection or no activity.

Stop here. This task's instruction explicitly says it is not Gate F authorization. No future automation or GPU save is scheduled by this work.
''',encoding='utf-8')
    # Public safety scan includes decoded notebook source (the embedded shared
    # ZIP is source only; no raw private archive is ever inserted).
    files={}
    for path in HERE.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts or path.name in ('AUTH_STATUS.json','INTEGRITY_MANIFEST.json'):
            continue
        raw=path.read_bytes()
        if path.suffix in ('.py','.md','.json','.ipynb'):
            text=raw.decode('utf-8-sig')
            assert not re.search(r'KGAT_[A-Za-z0-9_.-]+|X-Goog-Signature=[0-9A-Fa-f]{16,}|"Authorization"\s*:',text),str(path)
        files[path.relative_to(HERE).as_posix()]=sha(raw)
    put('INTEGRITY_MANIFEST.json',dict(files=files,historical_files_verified=len(historical['files']),
        frozen_candidate_bytes_unchanged=True,secret_scan=True,GPU_dispatched=False))
    print(json.dumps(dict(status='GPU_READY_NOT_AUTHORIZED',CPU_Notebook=cpu['Notebook_id'],new_files=len(files))))


if __name__=='__main__':run()
