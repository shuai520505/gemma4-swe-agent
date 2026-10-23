"""Freeze metadata-only prospective comparison, without running new tasks."""
import json
from .common import HERE, ROOT, ID, CONTROL_SHA, sha, write

def freeze():
    assert not (HERE/'GPU_REPLICATION_PROTOCOL.json').exists(), 'Never overwrite preregistration'
    catalog=ROOT/'u_re/v01/experiments/mechanism_02/TASK_POOL_METADATA.json'
    prior=ROOT/'u_re/v02/experiments/env_recovery_admission_01/TASK_POOL_FREEZE.json'
    old=json.loads(prior.read_bytes()); metadata=json.loads(catalog.read_bytes())['rows']
    reserved={r['instance_id'] for r in old['next_max24_in_order']}
    excluded=set(old['inherited_excluded_ids'])|set(old['prior_observed_ids'])|reserved|{old['carry']}
    historical=[r for r in metadata if r['instance_id'] in excluded]
    aliases=[]
    for row in metadata:
        hits=[r['instance_id'] for r in historical if r['repo']==row['repo'] and (r['base_commit']==row['base_commit'] or r['issue_sha256']==row['issue_sha256']) and r['instance_id']!=row['instance_id']]
        if hits and row['instance_id'] not in excluded:
            excluded.add(row['instance_id']); aliases.append(dict(instance_id=row['instance_id'],aliases=hits))
    prefix='U-RE-V04-EGR-REPLICATION:17:'
    ranked=sorted((dict(r,sort_sha256=sha((prefix+r['instance_id']).encode()),admission='NOT_ADMITTED',snapshot_sha256=None) for r in metadata if r['instance_id'] not in excluded),key=lambda r:(r['sort_sha256'],r['instance_id']))
    build=json.loads((HERE/'CANDIDATE_BUILD_MANIFEST.json').read_bytes())
    write(HERE/'GPU_REPLICATION_PROTOCOL.json',dict(
        experiment_id='U-RE-V04-EGR-REPLICATION',development_experiment=ID,status='PROSPECTIVE_PROTOCOL_FROZEN_TASK_ADMISSION_PENDING',
        GPU_authorized=False,GPU_dispatches_authorized=0,formal_submission=False,
        primary='Native Resolved, original trusted verify_task + TaskResult/JUnit agreement',
        candidates={'A':dict(name='Frozen Action-First V01',ZIP_sha256=CONTROL_SHA),'B':dict(name='Evidence-Guided Repair V04',ZIP_sha256=build['treatment_ZIP_sha256'])},
        factor='Only System instruction strategy replacement; YAML/model/tools/generation/budgets identical',
        budget=build['budget'],generation=build['generation'],model='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',
        environment_lock=dict(path='u_re/v02/experiments/env_recovery_admission_01/V02B_ENVIRONMENT_LOCK.json',sha256=sha((ROOT/'u_re/v02/experiments/env_recovery_admission_01/V02B_ENVIRONMENT_LOCK.json').read_bytes())),
        source_pool_count=len(metadata),inherited_exclusions=len(old['inherited_excluded_ids']),prior_observed_ids=old['prior_observed_ids'],preserved_prior_reservations=sorted(reserved),excluded_ids=sorted(excluded),additional_base_or_issue_aliases=aliases,
        remaining_count=len(ranked),repositories=sorted({r['repo'] for r in ranked}),scope='SAME_REPOSITORY_FASTAPI_ONLY',
        sources={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in (catalog,prior)},
        ranking='SHA256('+repr(prefix)+'+instance_id), ascending; instance_id tie-break; no difficulty/result selection',
        seed=17,target_tasks=2,max_new_baselines=min(8,len(ranked)),ranked_candidates=ranked,selected_tasks=None,
        selection='First two BASELINE_ELIGIBLE in frozen order; stop at two. At finite pool exhaustion report insufficient; never refill with development/reserved tasks.',
        identity_gate='Before screening, bind original snapshot/base/overlay/task-record/wheels/Verifier SHA; compare snapshot bytes with all excluded129 identities and between prospective candidates. Unknown source or alias conflict STOP; do not silently replace.',
        admission='Original empty Agent patch, no Prompt/Gemma; original native verifier executes, Issue-related ordinary behavioral failure, zero independent environment errors, original source and provenance, TaskResult/JUnit consistency, complete cleanup.',
        reject_continue=['Known independent dependency/fixture deficiency with established cause','All-pass nondiscriminating unpatched baseline'],
        conditional='Target-caused collection failure remains CONDITIONALLY_ELIGIBLE only; not counted among two formal tasks without separate validation.',
        stop=['Unknown collection/setup/internal failure','Task/snapshot/source identity or provenance conflict','Isolation/cleanup failure','TaskResult/JUnit disagreement'],
        future_order=[dict(run=1,task='T1',candidate='A'),dict(run=2,task='T1',candidate='B'),dict(run=3,task='T2',candidate='B'),dict(run=4,task='T2',candidate='A')],
        independence='Fresh session/history/chroot/workspace/UID lifecycle/patch/logs/trusted verifier per run. No previous candidate output or evaluator-only content enters Agent.',
        secondary_metrics={
            'first_supported_behavior_edit':'Operation-end upper bound of actual target production hash change, retrospectively linked to prior normal Issue/source/test evidence. Unknown support -> null; imports/debug/scratch excluded.',
            'repair_hypotheses':'Explicit falsifiable normal-input hypothesis plus expected discriminating observation. Human review with tool/model event hashes; earliest occurrence null unless all preceding events reviewed.',
            'repeated_search':'Same command/result/source epoch; potential utility assessed separately. Do not label every repeated token/search useless.',
            'broad_tests':'Unscoped full-suite invocation without concrete regression justification; explicit paths and actual scope retained privately.',
            'path_and_dependency_errors':'Count actual failed tool actions; distinguish expected first discovery from avoidable repetition and trusted native errors.',
            'cost':'Actual charged tools, Agent/Worker wall seconds, received prompt/completion tokens including failures; missing usage null plus coverage count.',
            'context':'Actual guard time/input, repair/submission state at guard, native resolved separately.',
            'submission':'Explicit successful tool response, repeated successful submits, tools after first success; native resolved is independent.',
            'patch':'Observed applicable patch and production hash; nonempty is not correctness. Native verifier is primary.'},
        execution_gates=['Two newly admitted tasks and exact run identities frozen before GPU','Same final production payload revalidated on CPU after execution changes','Frozen model/tokenizer SHA and approved runtime versions','Actual GPU/quota/full-window recheck','Chroot canary and evaluator isolation','New explicit human GPU authorization matched to final tasks/payload/resources'],
        proposal_only=dict(GPU='4xNVIDIA L4',TP=4,vllm='0.19.1',max_Notebooks=1,max_sessions=4,window_seconds=10000),
        interpretation='Development informed instruction design; PR24/27/28 tasks cannot be independent confirmation. Two FastAPI tasks give descriptive paired evidence only, no cross-repo/statistical superiority or Public Score conversion.',
        historical_unknown='PR27 Batch2 HTTP499 remains UNKNOWN. No reclassification or retry; new authorized experiments must independently check active-resource conflict.'))
    print(json.dumps(dict(remaining=len(ranked),ranked=[r['instance_id'] for r in ranked],GPU_authorized=False)))

if __name__=='__main__': freeze()
