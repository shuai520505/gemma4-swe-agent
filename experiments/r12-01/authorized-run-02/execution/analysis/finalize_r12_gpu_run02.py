"""Archive-backed analysis only. Never dispatch or infer with a model."""
import hashlib,json,zipfile
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs/r12_gpu_run02'; RUN=ROOT/'work/gemma-r12-01/authorized-gpu-02'
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
r=json.loads((OUT/'R12_GPU_RESULTS.json').read_bytes())
before=json.loads((RUN/'QUOTA_IMMEDIATELY_BEFORE_DISPATCH.json').read_bytes())
after=json.loads((RUN/'QUOTA_AFTER.json').read_bytes())
archive=ROOT/'work/gemma-r12-01/gpu-run02-output/gemma-r12-authorized-gpu-02.zip'
frozen=json.loads((ROOT/'outputs/r12_final_gpu_readiness/GPU_DISPATCH_PACKAGE_MANIFEST.json').read_bytes())
expected={'BASELINE':'944e1d23ce5e93a77af3e993834487e829487aff0a92ec7fe3e115590bfaf9f1','R1':'c0cd26d1084a8a480689db57012e0b0900a33c5fb9951b38aa0101a456c8f2a1','R2':'af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5'}
checks=[]; failures=[]
with zipfile.ZipFile(archive) as z:
    assert {c:sha(z.read('extension/candidates/'+c+'.zip')) for c in expected}==expected
    for session in r['sessions']:
        i=session['index'];prefix=f"execution/sessions/{i:02d}_{session['candidate']}_{session['instance_id']}/"
        config=json.loads(z.read(prefix+'CONFIGURATION.json'))
        assert config['budget']==dict(max_time_minutes=8,max_tool_calls=28,max_turns=80,timeout_seconds=240)
        assert config['generation']==dict(max_output_tokens=8192,temperature=.2,top_p=.95,thinking_config=dict(include_thoughts=True,thinking_budget=4096))
        assert config['candidate']==session['candidate']
        cp=zipfile.ZipFile(__import__('io').BytesIO(z.read('extension/candidates/'+session['candidate']+'.zip')))
        assert sha(cp.read('prompts/system.md'))==config['instruction_sha256']
        checks.append(dict(index=i,candidate=session['candidate'],instance_id=session['instance_id'],configuration=config,checks='PASS'))
        for line in z.read(prefix+'adk_events.jsonl').splitlines():
            event=json.loads(line).get('event',{})
            for part in (event.get('content') or {}).get('parts',[]):
                response=part.get('function_response')
                if response:
                    body=response.get('response') or {}
                    if body.get('error') or body.get('status')=='error':
                        failures.append(dict(index=i,tool=response.get('name'),response=body))
    assert [(x['task'],x['candidate']) for x in r['pair_summary']['records']]==[(s['instance_id'],s['candidate']) for s in frozen['sessions']]
    assert r['pair_summary']['complete'] and not r['pair_summary']['not_run']
    assert all(s['metrics']['evidence_complete'] and s['cleanup'] and s['evaluation']['cleanup'] for s in r['sessions'])
    assert r['server_cleanup']['complete'] and r['owned_root_recovery']['complete']
    for name in ['GPU_ALLOCATION.json','execution/MODEL_IDENTITY.json','execution/PAIR_RESULTS.json','execution/SERVER_CLEANUP.json','OWNED_ROOT_RECOVERY.json','NOTEBOOK_SUPERVISOR.json','execution/SERVER_CONFIGURATION.json']:
        dest=OUT/'raw-receipts'/name;dest.parent.mkdir(exist_ok=True,parents=True);dest.write_bytes(z.read(name))
stats={}
for c in expected:
    ss=[s for s in r['sessions'] if s['candidate']==c]
    stats[c]=dict(validated_repairs=sum(s['status']=='VALIDATED_REPAIR' for s in ss),sessions=3,
        explicit_submits=sum(bool(s['patch_submitted']) for s in ss),valid_explicit_submits=sum(s['status']=='VALIDATED_REPAIR' and s['patch_submitted'] for s in ss),
        missing_parameter_edit_calls=sum(x['tool']=='edit_file' and bool(x['missing']) for s in ss for x in s['metrics']['invalid_calls']),
        attempted_tools=sum(s['metrics']['attempted_calls'] for s in ss),charged_tools=sum(s['charged_tools'] for s in ss),
        llm_calls=sum(s['llm_calls'] for s in ss),agent_seconds=sum(s['agent_seconds'] for s in ss),worker_seconds=sum(s['worker_seconds'] for s in ss),
        observed_tokens={k:sum(s['metrics']['observed_usage'][k] for s in ss) for k in ('prompt_tokens','completion_tokens','total_tokens')},
        token_usage_complete=all(s['metrics']['usage_complete'] for s in ss))
r['post_run_analysis']=dict(candidate_statistics=stats,all_nine_configuration_checks='PASS',frozen_candidate_sha256=expected,
    resource=dict(before=before,after=after,account_quota_delta_seconds=after['used_seconds']-before['used_seconds'],account_quota_delta_hours=(after['used_seconds']-before['used_seconds'])/3600,attribution='Account-wide observed delta; no claim of isolated per-job billing',max_notebook_seconds=18000,max_budget_quota_hours=10),
    failures=failures,official_native_resolved=None,canonical_swebench_resolved=None,
    supervisor_schema_caveat='Generic SubprocessManager status is unknown/official_result_missing because this research runner does not emit that generic official result. This raw status is preserved. All nine R12 SESSION_RESULT/R12_METRICS, protected evaluations, HTTP traces and cleanup records exist; PAIR_RESULTS.complete=true. Do not call this an official competition evaluation.',
    R3_recommendation='Positive pilot signal supports a separately frozen R3 evaluation proposal, particularly R1 parameter hygiene plus R2 delivery. No R3 built. Three tasks and one run per candidate/task cannot establish causality, statistical significance, broad superiority, or public score 0.5.')
save(OUT/'R12_GPU_RESULTS.json',r)
save(OUT/'CONFIGURATION_AND_HASH_AUDIT.json',dict(candidate_sha256=expected,all_nine_checks='PASS',sessions=checks))
save(OUT/'TOOL_FAILURE_AUDIT.json',failures)
save(OUT/'STATUS.json',dict(status='R12_GPU_RUN_02_COMPLETED',real_sessions=9,validated_repairs=6,no_redispatch=True,updated_at_utc=datetime.now(timezone.utc).isoformat()))
lines=['# R12 GPU Run 02 — final report','',
 'Nine of nine real Gemma sessions completed in frozen order on four actual NVIDIA L4 GPUs. Seven nonempty patches were retained; six satisfy the frozen repair endpoint after separate post-run semantic review. No selective reruns, R3 construction, or formal competition submission occurred.','',
 '| Candidate | Validated repairs | Valid explicit submits | Missing-parameter edits | Charged / attempted tools | Observed tokens | Agent seconds |',
 '|---|---:|---:|---:|---:|---:|---:|']
for c,s in stats.items():lines.append(f"| {c} | {s['validated_repairs']}/3 | {s['valid_explicit_submits']}/3 | {s['missing_parameter_edit_calls']} | {s['charged_tools']} / {s['attempted_tools']} | {s['observed_tokens']['total_tokens']:,}{'' if s['token_usage_complete'] else ' (incomplete)'} | {s['agent_seconds']:.2f} |")
lines+=['','| Session | Task | Candidate | Final endpoint | Agent outcome | First production edit interval (s) |','|---:|---|---|---|---|---|']
for s in r['sessions']:
    edit=s['metrics']['first_production_edit'];interval=f"{edit['lower_seconds']:.2f}–{edit['upper_seconds']:.2f}" if edit else 'Not observed (not zero)'
    lines.append(f"| {s['index']} | {s['instance_id']} | {s['candidate']} | {s['status']} | {s['agent_outcome']} | {interval} |")
lines+=['', '## Required conclusions','',
 '1. Completion: 9 workers, 9 saved session results, 9 real Gemma sessions with HTTP requests, 9 independent evaluations, no NOT_RUN suffix. PAIR_RESULTS.complete=true; no coordinator STOP.',
 '2. Repairs: BASELINE 1/3 (pytest), R1 2/3 (Django, pytest), R2 3/3 (all three). These are owned Issue-grounded development endpoints, not canonical SWE-bench or official competition scores.',
 '3. R1 parameter hygiene: BASELINE made five edit_file calls missing old_string (four Django, one xarray); R1 and R2 made zero. Three sessions per arm; this is an observed pilot difference, not a causal estimate.',
 '4. R2 first production edit: Django 256.18–256.40s and xarray 326.30–326.36s, while BASELINE never changed production code on either. On pytest R2 was slower (133.67–133.75s versus BASELINE 92.37–92.46s). R2 improves edit coverage, without evidence of uniformly faster edits.',
 '5. R2 valid explicit submissions: 3/3 versus R1 2/3 and BASELINE 1/3. BASELINE explicitly submitted on two sessions, but its xarray submission was empty. Django BASELINE timed out with a diagnostic-only fallback; R1 xarray timed out without any patch.',
 '6. R2 has the highest observed repair rate. With only three tasks and one run per pair, this does not establish general superiority or predict public leaderboard 0.5.',
 '7. Failures: BASELINE Django repeated four malformed edit calls, spent its deadline without a production fix, and retained only temp_app reproduction files. BASELINE xarray diagnosed the relevant code but omitted old_string, exhausted 28 charged calls, then submitted an empty patch; BudgetExceeded responses are recorded. R1 xarray reached its deadline without editing. These are tool-interface/model-action and time-allocation failures, not observed GPU/backend/environment failures. The data do not isolate the causal contribution of each.',
 '8. Usage is recorded per session and candidate in R12_GPU_RESULTS.json. Token totals for timed-out BASELINE Django and R1 xarray are incomplete observations, not exact totals or zero missing usage. Charged calls and attempted calls are reported separately.',
 '9. All nine required positive controls passed; no observed control regression and no task where an alternative loses a BASELINE success. Broader regression suites were NOT_RUN; absence of broader regressions is not established.',
 '10. Both independent candidates show positive signals, so the precondition for proposing a separately frozen R3 evaluation is met. A combination is not yet demonstrated better than R2; no R3 has been built or run.',
 '', '## Evidence and trust','',
 f"The original archive is {archive.stat().st_size:,} bytes; SHA256 `{r['archive_sha256']}`; CRC PASS. R12_SESSION_EVIDENCE_INDEX.json hashes every retained member, including raw HTTP requests, ADK events, native traces, token observations, explicit/fallback patches, independent checks and cleanup records. The raw archive remains in the local evidence folder and Kaggle Notebook output; it is not embedded in Git.",
 'Actual nvidia-smi and Torch evidence confirms exactly four NVIDIA L4 devices with CUDA access, each 23034 MiB according to nvidia-smi. All eight mounted model files match the frozen SHA256 map. Candidate ZIP hashes and all nine actual SDK generation/budget/prompt configurations pass the post-run audit. Original manifests and candidates were preserved.',
 'Semantic review used the pre-return rubric, frozen Issue statements, model diffs, locked base source context and independent evaluator receipts. It was performed separately from the tested Gemma sessions by the same orchestrating Codex agent, not by a blinded second human reviewer. Django value string conversion, xarray lazy metadata access, and pytest sentinel identity fixes were reviewed; diagnostic-only changes were rejected.',
 r['post_run_analysis']['supervisor_schema_caveat'],
 '', '## Resources, stop conditions and cleanup','',
 f"Observed account quota use rose from {before['used_seconds']:.3f} to {after['used_seconds']:.3f} seconds, a delta of {(after['used_seconds']-before['used_seconds'])/3600:.4f} quota-hours. Remaining at {after['observed_at_utc']}: {after['available_seconds_after_reservations']/3600:.4f} quota-hours, reserved {after['reserved_seconds']:.0f}s. This is an account-wide snapshot difference, not isolated job billing.",
 'Notebook logs reach archive creation at 4427.61s (about 73.8 minutes), below the 18000s limit and 10 quota-hour cap. The 73200-second prelaunch floor was satisfied by 108000 seconds available. Four physical GPU-hours per node-hour differ from platform quota accounting; no unit substitution was used.',
 'Normal failed repairs were retained and execution continued in order. Infrastructure, backend/context, dependency, positive-control, isolation, evidence or cleanup failure would stop admission and mark remaining sessions NOT_RUN; no such frozen R12 stop was recorded. All session evaluator/agent cleanup records, final server cleanup and owned-root recovery report complete. The generic supervisor caveat above is preserved, not rewritten as an official PASS.',
 'The first read-only artifact download was interrupted; a second read-only download recovered the same Notebook v1 output and passed CRC. No Notebook redispatch occurred.',
 '', '## Next executable operation','',
 'No further GPU operation is part of this frozen run. Review these results and freeze a separate R3 comparison protocol if desired; do not selectively rerun failed R12 pairs. Existing raw evidence can be downloaded and inspected without allocating GPU.']
(OUT/'R12_GPU_FINAL_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
state=json.loads((ROOT/'work/gemma-r12-01/STATUS.json').read_bytes());state.update(status='R12_GPU_RUN_02_COMPLETED',real_sessions=9,validated_repairs=6,final_report=str(OUT/'R12_GPU_FINAL_REPORT.md'));save(ROOT/'work/gemma-r12-01/STATUS.json',state)
print(json.dumps(stats,indent=2))
