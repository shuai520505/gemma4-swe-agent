"""Recompute acceptance facts and final audit. Never rewrites raw observations."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
import yaml
from .build import HERE,ROOT,write,sha,S1


def load(p):
    return json.loads(p.read_text())


def emit(name,value):
    write(HERE/name,(json.dumps(value,indent=2)+'\n').encode())


def parts(path):
    out=[]
    for line in path.read_text().splitlines():
        row=json.loads(line)
        for p in row.get('event',{}).get('content',{}).get('parts',[]):
            for kind in ('function_call','function_response'):
                if kind in p:
                    out.append(dict(kind=kind,recorded_monotonic=row['recorded_monotonic'],**p[kind]))
    return out


def finalize():
    results=HERE/'results/cpu02';gate=load(results/'validation/cpu_gate.json')
    assert gate['passed'] and gate['stage']=='full' and gate['legacy']['passed']
    assert gate['failures']==gate['errors']==gate['skipped']==0
    candidates=load(HERE/'CANDIDATES.json')
    assert load(HERE/'registrations/cpu01.json')['candidate']==load(HERE/'registrations/cpu02.json')['candidate']==candidates
    cases={p.parent.name:load(p) for p in (results/'validation/cases').glob('*/case_result.json')}
    timing={}
    for arm in ('noegv','full'):
        r=cases[arm+'_deadline'];assert 299<=r['native_agent_seconds']<315
        assert r['HTTP_cancelled'] and r['HTTP_audit']['passed'] and r['HTTP_audit']['rows'][-1]['usage'] is None
        timing[arm]=r['native_agent_seconds']
        assert cases[arm+'_exact_tools']['counted_tools']==60
        config=yaml.safe_load((HERE/f'candidate_{arm}/eval_config.yaml').read_text())['evaluation']
        assert config==dict(timeout_seconds=120,max_tool_calls=60,max_time_minutes=5.0)
        for path in (results/'validation/cases').glob(arm+'_*/boundary.json'):
            boundary=load(path)
            assert boundary['budget_seconds']==(10 if path.parent.name.endswith('near_closure') else 300)
            assert boundary['tools_limit']==config['max_tool_calls'] and boundary['command_seconds']==config['timeout_seconds']
    assert cases['full_closed_loop']['counterexample_revision_retest']
    assert cases['full_wrong_test']['successful_edits']==1
    assert cases['full_submit_failure']['successful_submits']==1
    assert any(e['result']['status']=='error' for e in cases['full_submit_failure']['submit_responses'])
    assert cases['full_post_submit_negative']['successful_submits']==2
    assert cases['full_post_submit_negative']['tools_after_first_successful_submit']
    command_events=[json.loads(v) for v in (results/'validation/cases/full_command_limit/events.jsonl').read_text().splitlines()]
    command_seconds=max(e['elapsed_seconds'] for e in command_events if e['kind']=='sandbox_command_end')
    assert 119<=command_seconds<135
    for path in (results/'validation/cases').glob('*/cleanup.json'):
        assert load(path)['complete'] and load(path)['leftover_sandboxes']==0
    tokens=load(results/'validation/prompt_tokens.json')
    assert tokens==load(HERE/'results/cpu01/validation/prompt_tokens.json')
    emit('CPU_MECHANISM_EVENTS.json',dict(counterexample_revision_retest=parts(results/'validation/cases/full_closed_loop/adk_events.jsonl'),
        wrong_expectation=parts(results/'validation/cases/full_wrong_test/adk_events.jsonl'),
        repeated_submission_negative=parts(results/'validation/cases/full_post_submit_negative/adk_events.jsonl'),
        scope='Posthoc extraction of actual native event order/timestamps, not model claims or online enforcement. Raw case summaries with null monotonic remain intact.'))
    runtime_paths=['u_re/v01/'+n for n in ('cpu.py','runner_cases.py','audit.py','tests/test_runner.py','tests/test_static.py','build.py')]
    registry=load(HERE/'registrations/cpu02.json')
    for n in runtime_paths:
        assert sha((ROOT/n).read_bytes())==registry['source_hashes'][n],n
    emit('CPU_CONFIG_BINDING_AUDIT.json',dict(passed=True,native_deadline_seconds=timing,command_max_seconds=command_seconds,
        evaluated_YAML_matches_actual_boundary_values=True,critical_runtime_sources_match_executed_registry=runtime_paths,
        private_scoring_eval_config_loader='NOT_AVAILABLE_NOT_EXECUTED',
        host_builder_note='prepare_cpu.py extended after CPU02 freeze only to build evaluator-only CPU03; actual CPU02 source stays in raw.zip/registration.'))
    historical=load(HERE/'HISTORY_REFERENCES.json');digest=hashlib.sha256();count=0
    names=subprocess.check_output(['git','-c','core.longpaths=true','ls-tree','-r','--name-only',S1],cwd=ROOT).decode().splitlines()
    for n in sorted(names):
        p=ROOT/n
        assert p.is_file(),n
        digest.update(n.encode()+b'\0'+hashlib.sha256(p.read_bytes()).digest());count+=1
    assert count==historical['raw_checkout_tracked_files'] and digest.hexdigest()==historical['raw_checkout_aggregate_sha256']
    changed=subprocess.check_output(['git','-c','core.longpaths=true','diff','--name-only',S1],cwd=ROOT).decode().splitlines()
    assert all(n.startswith('u_re/') for n in changed),changed
    for row in historical['references']:
        assert sha(subprocess.check_output(['git','show',row['commit']+':'+row['path']],cwd=ROOT))==row['blob_sha256']
    emit('HISTORY_FINAL_AUDIT.json',dict(passed=True,base=S1,inherited_files_unchanged=count,
        raw_checkout_aggregate_sha256=digest.hexdigest(),only_new_namespace_changed=True,referenced_historical_blobs_unchanged=True))
    admission=load(HERE/'results/cpu03/validation/cpu_gate.json')
    identities=load(HERE/'results/cpu03/validation/task_identities.json')
    selection=load(HERE/'GPU_TASK_SELECTION_DRAFT.json')
    prior=load(ROOT/'s1/experiments/egv_mechanism_smoke_01/protocol.json')
    emit('GPU_EXPERIMENT_PROTOCOL_DRAFT.json',dict(experiment_id='U-RE-V01-MECHANISM-01',status='DRAFT_EXECUTION_NOT_AUTHORIZED' if admission['passed'] else 'DRAFT_BASELINE_BLOCKED',
        selection=selection,candidates=candidates,task_identities=identities,clean_baselines=admission,
        model_source='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',expected_model_files_from_frozen_S1=prior['model_files'],
        model_weights_revalidated_now=False,CPU_tokenizer_identity=tokens['tokenizer_files'],
        expected_wheel_hashes=load(results/'wheel_hashes.json'),expected_task_wheel_hashes=load(results/'task_wheel_hashes.json'),
        official_versions=load(results/'validation/versions.json'),CPU_gate_sha256=sha((results/'validation/cpu_gate.json').read_bytes()),
        CPU_raw_sha256=sha((results/'raw.zip').read_bytes()),GPU_Notebook_sha256=None,GPU_payload_sha256=None,
        current_GPU_quota='NOT_QUERIED',GPU_execution_authorized=False,GPU_executed=False,
        resource_plan=dict(agent_runs=4,maximum_Agent_seconds=1200,conservative_total_window_seconds=8640,
                           reported_quota_requirement='REQUIRES_REAL_UNIT_AND_WINDOW_ADMISSION'),
        primary=['native_official_resolved','resolved_tasks_under_fixed_total_budget'],
        registration_blockers=['separate explicit GPU authorization','actual current resource/window admission','frozen executable Notebook/payload','GPU runtime model/request/idle identity checks']+([] if admission['passed'] else ['clean-baseline task admission blocked; no task replacement']),
        note='No task substitutions after registration; negative algorithms continue unless infrastructure/integrity/resource STOP. No current formal submission recommendation.'))
    new=gate['tests_run'];old=gate['legacy']['tests_run']
    cpu=f'''# Official Linux CPU acceptance

CPU02 v1 COMPLETE: **{old+new}/{old+new} test methods passed**, no failures/errors/skips. The existing entry point actually ran{old} methods (38 original official API/tool tests,5 static tests,28 S1 tests); the folder name legacy77 is a historical label, not the count. The new suite ran{new}:13 U-RE Runner methods,3 package tests,10 HTTP lifecycle tests and13 structured Verifier tests. Compiler/empty-State gates for both candidates and CPU tokenizer measurement are additional explicitly recorded checks, not extra test-count inflation.

Commands: `python -m u_re.v01.prepare_cpu cpu02 full`, `python -m u_re.v01.launch_cpu cpu02`. Saved wudangdexiaodoashi/gemma4-u-re-v01-cpu02 version1 uses pinned official Linux image, enableGpu=false, enableTpu=false, offline inputs. Exact Notebook/payload SHA and one-save HTTP receipt are in registrations/cpu02_build.json and results/cpu02/SAVE_REQUEST.json/SAVE_RESPONSE.json. Within that Notebook: `python -m u_re.v01.cpu <new-output> full`. Collection downloads the canonical original ZIP, verifies CRC and every manifest entry; source is preserved inside raw.zip. One oversized output-listing page request returnedHTTP400; recovery read the same completed version with default page size, without compute rerun. CPU01 failures and its distinct frozen source remain unchanged.

Actual public packages: swegemma0.2.11,adk-submission0.2.13,adk-eval-core0.1.0,google-adk1.36.1,google-genai2.11.0,litellm1.82.4,pytest8.4.2,transformers5.13.1. GPU count was asserted0. No model server/inference ran; only HTTP model replies were scripted. Native Compiler, empty-State ADK Runner, tool schemas, Git edits, assertions, budget counting and submit were real. Observers do not return fake tool results, end invocations or change scoring logic.

| Requirement | Actual evidence under results/cpu02/validation |
|---|---|
| A basic repair/test/diff/submit, both arms | cases/noegv_basic and full_basic, returned.patch/native_trace.json |
| B failing real assertion→production revision→same assertion passes | cases/full_closed_loop; CPU_MECHANISM_EVENTS.json joins actual ordered events |
| C wrong self-test expectation | cases/full_wrong_test: wrong assertion fails, correct production retained, SPEC checked and correct checks pass |
| D no-progress | cooperative case avoids unchanged repeat; repeat_negative deliberately repeats and offline audit detects1; it is not Runtime-blocked |
| E closure and retry | basic cases finish after one successful submit; submit_failure uses an actual temporary Git-metadata failure, recovery and successful retry |
| E negative termination guarantee | full_post_submit_negative executes a real check and a second identical successful submit after first success; Runtime does not immediately stop per-tool |
| F300s native deadlines | NoEGV {timing['noegv']:.6f}s; Full {timing['full']:.6f}s. Both unfinished HTTP replies cancelled with usage=null and patch persisted |
| F60 counted operations | both exact_tools cases reach60; extra counted edit denied, free status/submit still work |
| F120s command | actual maximum command {command_seconds:.6f}s; real process absent and delayed write absent after wait |
| F near closure/cancellation | ten-second supplemental fixture submits near its end; separate actual external CancelledError propagates and patch survives |
| G package and request | three-member CRC/hash equality, six legal tools, no child, full Prompt in actual HTTP system instruction, Issue JSON retained |

The unchanged frozen HTTP auditor only admits native deadline cancellation; the deliberate external-cancel fixture records the real boundary and leaves that auditor's unexplained_cancellation flag intact instead of falsely calling it a native deadline. Missing-response usage is null/partial. Scripted usage is synthetic and is never reported as Gemma Token cost. Ten-second supplemental timing is not substituted for the two300s measurements. Private scoring scripts/inference.py is not available: candidate YAML is matched to actual EvalConfig/boundary values, not claimed to have run through the private scoring loader.

CPU03 is a separate evaluator-only task-identity/clean-baseline inspection; it runs zero Agents/models. Its results do not count toward U-RE repair rate or the110 scripted-test total. Admission={admission['passed']}; details in results/cpu03/validation. No task is replaced if its gate blocks. These baseline tests are not shown to either candidate.

**CPU_PASS is compatibility and observability evidence. GPU_ALGORITHM_VALIDATED remains false.** Compliant Mock scripts do not prove autonomous evidence selection, error recognition, soft phase timing, no-progress judgment or reliable closure by real Gemma. The two arms are not algorithmically compared using scripted responses.
'''
    write(HERE/'CPU_VALIDATION.md',cpu.encode())
    decision=f'''# Candidate decision — U-RE V0.1

CPU technical feasibility: GO, {old+new}/{old+new} actual official Linux methods passed plus both Compiler/empty-State gates. GPU algorithm evidence: GPU_NOT_TESTED. GPU execution: NOT_AUTHORIZED; resource/Notebook admission NOT_DONE. Formal submission: NO-GO pending representative complete-run throughput and confirmed clocks. Candidate ZIPs have never changed since the initial5288e18 source commit.

| Question | Conclusion and actual evidence |
|---|---|
| Q1 one Agent/four functions | Yes as one declarative LlmAgent Prompt workflow, not four enforced Runtime states; ARCHITECTURE.md, candidate_full/agent.yaml |
| Q2 no AgentTool/Jev | Yes; both three-member ZIPs contain only YAML/Prompt, six tools and no executable/controller/child/external backend; CANDIDATES.json/static tests |
| Q3 S1 EGV inheritance | Validity/provenance/novelty/counterexample-repair/retest/old behavior retained generically; PROMPT_DIFF.md and frozen S1 references; no reference repair copied |
| Q4 factor match | Only EGV Prompt block differs; same YAML bytes/config/budget/closure/progress, ordinary testing allowed in A; CANDIDATE_EXACT.diff |
| Q5 official Compiler/Runner | Both real Compiler and explicit empty-State Runner passed; compiler_empty_state_gate.json and captured HTTP instructions |
| Q6 real CPU repair loop | Yes with scripted model only; failed real check, actual production edit, same check passes; cases/full_closed_loop/native_trace.json and CPU_MECHANISM_EVENTS.json |
| Q7 immediate hard stop | No per-tool guarantee. Successful submit plus final text ends native loop; negative script executes more tools before that final text. No official plugin/tool altered; BUDGET_GUARD.md |
| Q8 loop/re-submit risk | Remains Prompt-dependent. Negative controls expose repeated checks and duplicate successful submits; no hard progress controller is falsely claimed |
| Q9 current300s/60 | Both real native300s waits and both60-count boundaries passed; command120s/cleanup tested; CPU_CONFIG_BINDING_AUDIT.json |
| Q10 whole-run timeout | Material under cap/setup-heavy or larger-task assumptions; actual population risk unmeasured.360 sensitivity rows, separate platform clock, empirical quantilesnull; GLOBAL_BUDGET_ASSESSMENT.md |
| Q11 GPU protocol | DRAFT only, two proposed independent tasks, current identity/baseline evidence attached. No GPU Notebook, run, training or formal Submission; GPU_EXPERIMENT_PROTOCOL_DRAFT.json |
| Q12 enter first GPU test | Candidate is technically eligible for a separately authorized mechanism proposal. Execution is NO-GO until explicit authorization, actual resource/window checks, executable freeze and GPU identity/HTTP/cleanup gates. CPU03 baseline eligible={admission['passed']}; if false, that additionally blocks the fixed draft without task substitution |

No U-RE Public Score or resolved improvement exists. S0 remains the historically confirmed0.13; T50057402336 timed out with score=null, not zero. Do not expand to20–30 tasks or submit formally from these CPU data. A future two-task pair tests mechanisms first; no population superiority or gold-medal inference is licensed.
'''
    write(HERE/'CANDIDATE_DECISION.md',decision.encode())
    files={}
    for p in sorted(HERE.rglob('*')):
        rel=p.relative_to(HERE)
        if p.is_file() and p!=HERE/'INTEGRITY_MANIFEST.json' and not {'_local','download','__pycache__'}.intersection(rel.parts):
            raw=p.read_bytes();files[rel.as_posix()]=dict(bytes=len(raw),sha256=sha(raw))
    manifest=dict(version='U-RE-V0.1',files=files,self_excluded=True,
        scope='Candidate packages, current code, all immutable CPU raw archives and expanded observations; local redundant download/pycache excluded',
        inherited_history_audit='HISTORY_FINAL_AUDIT.json',GPU='GPU_NOT_TESTED',formal_submission=False,
        root_sources={'u_re/__init__.py':sha((ROOT/'u_re/__init__.py').read_bytes()),'u_re/.gitattributes':sha((ROOT/'u_re/.gitattributes').read_bytes())})
    write(HERE/'INTEGRITY_MANIFEST.json',(json.dumps(manifest,indent=2)+'\n').encode())
    print(json.dumps(dict(CPU_tests=old+new,passed=True,deadlines=timing,command_seconds=command_seconds,
        manifest_files=len(files),GPU='GPU_NOT_TESTED',task_baselines_eligible=admission['passed']),indent=2))


if __name__=='__main__':
    finalize()
