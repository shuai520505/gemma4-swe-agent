"""Reproducible descriptive audit; semantic judgements are explicitly human-readable."""
import hashlib,json,statistics,zipfile
from datetime import datetime,timezone
from pathlib import Path
D=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads((D/p).read_bytes())
def save(p,x):
    q=D/p;q.parent.mkdir(parents=True,exist_ok=True)
    q.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def main():
    manifest=load('GPU_DISPATCH_PACKAGE_MANIFEST.json');plan=load('EXECUTION_PLAN.json');metrics=load('GPU_BEHAVIOR_METRICS.json')
    diagnoses=load('POST_RUN_CPU_SEMANTIC_DIAGNOSTICS.json')
    assert all(r.get('passed',True) for r in diagnoses['sympy']['cases'] if r['arm'] in ['A','R2'])
    reviews=[
      ('INVALID_REPAIR','Only zeros_like annotation changes; no runtime change to polyval/timedelta conversion. Added diagnostic scripts are unrelated to the requested fix. Frozen target and original co-target still fail.'),
      ('NO_PATCH','480-second Agent deadline; recovered patch is empty. Reproduction/analysis without a production change does not repair the Issue.'),
      ('INVALID_REPAIR','Only new .pylintrc and dummy.py. No regexp CSV parser implementation change; bad-names configuration does not fix commas inside quantifiers.'),
      ('INVALID_REPAIR','Only new .pylintrc and foo.py reproducer. No change to argument regexp tokenization; the trusted target still fails.'),
      ('PARTIAL_REPAIR','Timeout fallback changes actual prepend_prolog and passes all 10 frozen tests. However it recognizes only =,-,~ through SECTIONING_CHARS; ^,*,+,# still split role heading and underline. Post-run CPU counterexamples demonstrate an incomplete Issue-level fix.'),
      ('PARTIAL_REPAIR','Actual production regex change passes all 10 frozen tests and preserves simple docinfo. It distinguishes :mod:`...`, but :py:mod:`...` and :std:ref:`...` still match the first colon word and split headings. CPU diagnostics reproduce this independent of underline choice. New test_regex.py was temporarily created then removed: an additional prompt-level test-file instruction violation, not tampering with trusted tests.'),
      ('VALIDATED_REPAIR','Actual EvaluateFalseTransformer adds all six relational AST operators with evaluate=False, recursively transforms operands and handles chained relations. 29/29 frozen tests; CPU source-based checks confirm all six operators, chained and nested expressions and unchanged evaluate=True. New compare_operators mapping before the later visitor is a first edit but not yet a functional repair. Bounded approval, not universal equivalence; unusual custom globals/local dictionaries and all unsupported operator mixtures have not been exhaustively tested.'),
      ('VALIDATED_REPAIR','Actual visit_Compare handles six relations and recursive operands, and constructs And for chains. 29/29 frozen tests and same additional CPU checks pass; evaluate=True path remains intact. ast.NameConstant is consistent with this pinned source but deprecated in newer Python. Bounded approval; arbitrary custom namespace behavior and unsupported operator mixtures are not exhaustively established.')]
    with zipfile.ZipFile(D/'gpu-output/r2a-real-gpu-01.zip') as z:
        read=lambda n:json.loads(z.read(n))
        pair=read('execution/PAIR_RESULTS.json');allocation=read('GPU_ALLOCATION.json')
        assert allocation['status']=='GPU_ALLOCATION_CONFIRMED' and allocation['torch_count']==4
        assert all(d['name']=='NVIDIA L4' and d['memory_bytes']>0 for d in allocation['torch_devices'])
        assert read('execution/MODEL_IDENTITY.json')['files']==manifest['expected_model_files']
        config=read('execution/SERVER_CONFIGURATION.json')['config']
        for k,v in manifest['expected_server_config'].items():assert config[k]==v,(k,config[k],v)
        assert [(r['index'],r['candidate'],r['result']['task_id']) for r in pair['records']]==[(r['index'],r['candidate'],r['task']) for r in plan['sessions']]
        assert read('ONE_TIME_RUN_MANIFEST.json')['original_execution_plan_sha256']==sha((D/'EXECUTION_PLAN.json').read_bytes())
        assert read('ONE_TIME_RUN_MANIFEST.json')['approved_evaluation_sha256']==sha((D/'APPROVED_EVALUATION_AMENDMENT.json').read_bytes())
        assert read('execution/SERVER_CLEANUP.json')['complete'] and read('OWNED_ROOT_RECOVERY.json')['complete']
        tool_schemas=[];wire_counts=[];semantics=[];actions=[];iso=[]
        for r in metrics['rows']:
            i=r['index'];prefix=f"execution/sessions/{i:02d}_{r['candidate']}_{r['task_id']}/"
            cfg=read(prefix+'CONFIGURATION.json');assert cfg['generation']==manifest['expected_generation']
            for name in z.namelist():
                if name.startswith(prefix) and name.split('/')[-1].startswith('ISOLATION_'):
                    receipt=read(name);iso.append(dict(path=name,receipt=receipt))
            http=[json.loads(l) for l in z.read(prefix+'model_transport/http_wire.jsonl').decode().splitlines()]
            requests=[h for h in http if h['kind']=='http_request']
            agent_count=0;summary_settings=[]
            for h in requests:
                b=h['body']
                assert b['thinking_token_budget']==4096 and b['chat_template_kwargs']['enable_thinking'] is True
                assert b['model'].endswith('/gemma-4-31b-it-qat-w4a16-ct/2')
                if b.get('tools'):
                    assert b['temperature']==0.2 and b['top_p']==0.95
                    assert b.get('max_completion_tokens',b.get('max_tokens'))==8192
                    agent_count+=1;tool_schemas.append(sha(json.dumps(b['tools'],sort_keys=True).encode()))
                else:
                    assert 'Please summarize the conversation' in str(b['messages'])
                    summary_settings.append({k:v for k,v in b.items() if k!='messages'})
            wire_counts.append(dict(index=i,requests=len(requests),agent_requests=agent_count,SDK_compaction_requests=len(summary_settings),summary_request_settings=summary_settings))
            calls=load(f"results/{i:02d}_{r['candidate']}_{r['task_id']}/TOOL_ACTIONS.json")
            errors=[];missing_edits=0;budget_denials=0;statuses=0
            for c in calls:
                if c['name']=='get_status':statuses+=1
                rr=(c.get('response') or {}).get('response',{})
                if c['name']=='edit_file' and not all(k in c['args'] for k in ['filepath','old_string','new_string']):missing_edits+=1
                if isinstance(rr,dict) and rr.get('error_type'):
                    errors.append(dict(t=c['t'],name=c['name'],error_type=rr['error_type'],message=rr.get('error_message'),call_id=c.get('id')))
                    budget_denials+=rr['error_type']=='BudgetExceeded'
            actions.append(dict(index=i,candidate=r['candidate'],task_id=r['task_id'],get_status_calls=statuses,missing_required_edit_arguments=missing_edits,budget_denials=budget_denials,tool_errors=errors,classification_note='CommandError includes intentional bug reproductions, failed grep and expected lint diagnostics; not every nonzero command is an invalid tool call. Native task failures are separate.'))
            decision,reason=reviews[i-1]
            semantics.append(dict(index=i,candidate=r['candidate'],task_id=r['task_id'],sdk_native_resolved=r['sdk_native_resolved'],independent_test_pass=r['independent_test_pass'],review_classification=decision,semantic_approved=decision=='VALIDATED_REPAIR',rationale=reason,strict_protocol_eligible=i<6,post_stop_observation=i>=6,raw_patch_sha256=sha(z.read(prefix+r['patch_kind']+'.patch'))))
        assert len(set(tool_schemas))==1
        assert len(iso)==16 and all(r['receipt']['exit_code']==0 and 'NONROOT_CHROOT_NETWORK_DENIED' in r['receipt']['stdout'] for r in iso)
        for name,expected in plan['candidate_sha256'].items():assert sha((D/'candidates'/f'{name}.zip').read_bytes())==expected
        save('GPU_RESOURCE_AND_IDENTITY_AUDIT.json',dict(evidence_type='REAL_GPU_OBSERVATION',status='IDENTITY_ALLOCATION_AND_CLEANUP_PASS',exact_order=True,candidate_hashes={k:sha((D/'candidates'/f'{k}.zip').read_bytes()) for k in ['R2','A']},model_files_verified=8,tool_schema_sha256=tool_schemas[0],request_settings_checked=wire_counts,actual_GPU_allocation=allocation,isolations=iso,server_cleanup=read('execution/SERVER_CLEANUP.json'),owned_root_recovery=read('OWNED_ROOT_RECOVERY.json'),generic_supervisor_caveat='Top reused supervisor reports unknown/official_result_missing because it expects the old single official_result artifact; child coordinator exited0 and has PAIR_RESULTS plus all eight SESSION_RESULT receipts. This is a schema limitation, not a replacement of the raw unknown status.'))
        save('INDEPENDENT_SEMANTIC_REVIEW.json',dict(reviewer='Codex, separate post-run semantic audit stage; same analyst, unblinded, not an independent external human or second reviewer',endpoint='User-approved exact required-test + effective production fix + semantic approval',post_run_diagnostics='Exploratory CPU source-based counterexamples. Frozen tests/expectations and SDK results are unchanged. Both Sphinx arms are treated consistently as partial.',rows=semantics))
        save('GPU_TOOL_ERROR_AUDIT.json',dict(rows=actions))
        before=load('gpu-notebook/QUOTA_IMMEDIATELY_BEFORE_DISPATCH.json');after=load('gpu-notebook/QUOTA_AFTER_TERMINAL.json')
        delta=after['used_seconds']-before['used_seconds']
        final=read('NOTEBOOK_FINAL_STATUS.json')
        comparison={}
        for c in ['R2','A']:
            ms=[r for r in metrics['rows'] if r['candidate']==c];ss=[r for r in semantics if r['candidate']==c]
            comparison[c]=dict(metrics['aggregate'][c],planned_sessions=4,completed_sessions=4,descriptive_semantic_validated=sum(r['semantic_approved'] for r in ss),partial_repairs=sum(r['review_classification']=='PARTIAL_REPAIR' for r in ss),native_SDK_resolved=sum(r['sdk_native_resolved'] for r in ms),mean_agent_seconds=statistics.mean(r['agent_seconds'] for r in ms),validated_explicit_submits=sum(r['semantic_approved'] and metrics['rows'][r['index']-1]['patch_submitted'] for r in ss),strict_protocol_eligible_sessions=sum(r['strict_protocol_eligible'] for r in ss),strict_protocol_eligible_validated=sum(r['semantic_approved'] and r['strict_protocol_eligible'] for r in ss))
        save('PROTOCOL_DEVIATIONS.json',dict(status='STRICT_STOP_RULE_DEVIATION',first_detected_session=6,first_tool_elapsed_seconds=47.16585621200011,errors=['sphinx-build: command not found','locale.Error: unsupported locale setting'],evidence='results/06_A_sphinx-doc__sphinx-11445/TOOL_ACTIONS.json',cause='CPU admission checked trusted Python tests but not the Issue CLI path/locale. Stop classifier inspected verifier/environment receipts but did not classify infrastructure errors embedded in Agent tool responses.',required_frozen_action='Stop the remainder immediately on environment/infrastructure errors; sessions 7/8 should not have started.',actual_action='Runtime continued and physically executed sessions 7/8. Preserve actual records; do not falsely relabel them NOT_RUN.',analysis_action='Session6 is environment-affected and sessions6-8 excluded from confirmatory interpretation. All-eight comparisons below are descriptive/exploratory. Remaining strict-prefix observations are unbalanced and cannot establish candidate superiority.',additional_limitations=['Same-analyst unblinded semantic review','Post-run extra cases are exploratory, not a preregistered enlarged test endpoint','A temporarily wrote test_regex.py then removed it; prompt instruction violation, no trusted test mutation observed','Raw reused outer supervisor unknown/official_result_missing schema mismatch retained'],reruns=0))
        results=dict(status='R2A_PILOT_AUDIT_COMPLETE_INCONCLUSIVE',scientific_gate='NO_CANDIDATE_PROMOTION_PROTOCOL_DEVIATION',physically_completed_sessions=8,planned_sessions=8,not_run=[],gpu_dispatches=1,retries=0,formal_submissions_this_study=0,comparison_descriptive_only=comparison,confirmatory_comparison=None,official_hidden_competition_resolved=None,canonical_swebench_resolved=None,official_charged_seconds=None,official_task_count=None,account_quota_delta_seconds=delta,account_quota_delta_hours=delta/3600,quota_scope='Observed account balance change across job, not a per-session official competition billing receipt or guaranteed exclusive job attribution.',quota_after=after,first_cell_elapsed_seconds=final['first_cell_elapsed_seconds'],model_load_seconds=read('execution/MODEL_LOAD_COMPLETED.json')['seconds'],first_cell_four_GPU_device_hours=4*final['first_cell_elapsed_seconds']/3600,raw_SDK_and_exact_tests='2/4 each; unchanged',descriptive_semantic_validated='1/4 each after rejecting both incomplete Sphinx fixes; both validated Sympy observations occur after the strict stop boundary.',A_agent_seconds_reduction_percent=100*(1-comparison['A']['agent_seconds']/comparison['R2']['agent_seconds']),token_cost_comparison='A observed total1082892 complete; R2 observed887623 is a lower bound because two timeout requests have UNKNOWN usage. No definitive full-cost ratio.',recommendation='Retain frozen R2 as current established candidate. A is not demonstrated superior and is not promoted or submitted. Fix CPU CLI/locale admission and tool-response infrastructure stop coverage in a separate prospective infrastructure change before any separately designed new experiment; do not replay this one.',updated_at_utc=datetime.now(timezone.utc).isoformat())
        save('R2A_GPU_RESULTS.json',results)
        save('STUDY_STATUS.json',results)
        print(json.dumps(results,indent=2))
if __name__=='__main__':main()
