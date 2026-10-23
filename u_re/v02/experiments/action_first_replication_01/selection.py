"""Metadata-only preregistration, run before any new baseline or model result."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ID = 'U-RE-V02-ACTION-FIRST-REPLICATION'
PREFIX = ID + ':17:'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')

def freeze():
    assert not (HERE/'TASK_POOL_FREEZE.json').exists(), 'Never overwrite a frozen pool'
    old = ROOT/'u_re/v01/experiments/action_priority_01'
    catalog = ROOT/'u_re/v01/experiments/mechanism_02/TASK_POOL_METADATA.json'
    previous = old/'gpu_readiness_01/TASK_POOL_FREEZE.json'
    ledger = old/'integrated_cpu_01/TASK_ADMISSION_LEDGER.json'
    metadata = json.loads(catalog.read_bytes())['rows']
    pool = json.loads(previous.read_bytes())
    excluded = set(pool['excluded_ids'])
    entries = [dict(instance_id=i, reason='Inherited conservative exclusion; no reservation released', evidence=str(previous.relative_to(ROOT)), model_executed='UNKNOWN', reference_exposed='UNKNOWN') for i in sorted(excluded)]
    used = {r['instance_id']:r for r in json.loads(ledger.read_bytes())['rows']}
    for row in pool['next_max8_in_order']:
        ident = row['instance_id']; excluded.add(ident)
        entries.append(dict(instance_id=ident, reason='Prior Action-First first8 screening reservation; retain even if NOT_RUN', evidence=str(previous.relative_to(ROOT)), baseline=used.get(ident,{}).get('status','NOT_RUN'), model_executed=ident in ('fastapi_9425','fastapi_14786'), reference_exposed='UNKNOWN'))
    # Same base or same Issue aliases are conservatively excluded even under a
    # different instance_id. Snapshot byte aliases are checked before screening.
    historical = [r for r in metadata if r['instance_id'] in excluded]
    for row in metadata:
        aliases = [r['instance_id'] for r in historical if r['repo']==row['repo'] and (r['base_commit']==row['base_commit'] or r['issue_sha256']==row['issue_sha256']) and r['instance_id']!=row['instance_id']]
        if aliases and row['instance_id'] not in excluded:
            excluded.add(row['instance_id']);entries.append(dict(instance_id=row['instance_id'],reason='Same frozen base or Issue as excluded identity',aliases=aliases,evidence=str(catalog.relative_to(ROOT))))
    allowed = sorted((dict(r, sort_sha256=sha((PREFIX+r['instance_id']).encode())) for r in metadata if r['instance_id'] not in excluded), key=lambda r:(r['sort_sha256'],r['instance_id']))
    assert len(metadata)==129 and len({r['instance_id'] for r in metadata})==129
    source_files=[catalog,previous,ledger,ROOT/'u_re/v01/experiments/mechanism_02/EXCLUSION_LEDGER_V02.json',Path(__file__)]
    candidates={'A':('u_re/v01/submission_noegv.zip','2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608'),'B':('u_re/v01/experiments/action_priority_01/submission_action_v01.zip','70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8'),'historical_Full':('u_re/v01/submission_full.zip','887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821')}
    for path,h in candidates.values(): assert sha((ROOT/path).read_bytes())==h
    write(HERE/'TASK_POOL_FREEZE.json',dict(experiment_id=ID,source_pool_count=129,remaining_count=len(allowed),scope='SAME_REPOSITORY_REPLICATION' if len({r['repo'] for r in allowed})==1 else 'MULTI_REPOSITORY',metadata_source_sha256=sha(catalog.read_bytes()),sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in source_files},excluded_ids=sorted(excluded),exclusion_entries=entries,ranked_rows=allowed,next_max16_in_order=allowed[:16],snapshot_alias_check='Before any baseline: hash all129 snapshots; alias with excluded identity STOP; repeated prospective snapshot STOP. No silent replacement.',history_scope='Inherited PR1-19 audit plus PR20-24 first8 reservation and actual screening/model registrations. No claim about unrecorded exposure or pretraining.',candidates={k:dict(path=v[0],sha256=v[1]) for k,v in candidates.items()}))
    write(HERE/'REPLICATION_PROTOCOL.json',dict(experiment_id=ID,status='PREREGISTERED_BEFORE_NEW_BASELINES',seed=17,ranking='SHA256('+repr(PREFIX)+' + instance_id), ascending, instance_id tie break',max_checks=16,target_tasks=4,selection='First four BASELINE_ELIGIBLE in frozen order; stop immediately at four; no outcome-based replacement',primary='Native Resolved',hypotheses={'H1':'Higher paired Native Resolved probability','H2':'More production edits before stop','H3':'More valid submits and fewer post-submit operations','H4':'Fewer context stops without production repair','H5':'Possible extra Token/tools cost'},eligibility='Original empty patch native verify_task, discriminating Issue-related assertion failure, no independent environment error, matching identities, source provenance, JUnit/TaskResult agreement, cleanup complete',reject_continue=['Known independent missing inline_snapshot or pytest-httpbin','Non-discriminating all-pass base'],conditional='Target-caused collection failure is not formally eligible without separate validation; no baseline reclassification',stop=['Unknown collection/setup/internal error','Identity/snapshot alias conflict','JUnit/TaskResult conflict','Source/provenance drift','Isolation or cleanup failure'],run_order=[dict(run=2*i+j+1,task='T'+str(i+1),arm=a,batch=1+i//2) for i,arms in enumerate((('A','B'),('B','A'),('A','B'),('B','A'))) for j,a in enumerate(arms)],budget=dict(agent_seconds=300,charged_tools=60,command_seconds=120,context=32768,max_output_tokens=16384,safety=1024,input_cap=15360,thinking=4096,seed=17),GPU_authorization=dict(max_Notebooks=2,max_sessions=8,each_batch_sessions=4,each_platform_seconds=10000,GPU='4xL4',TP=4,model='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',vllm='0.19.1',retry_authorized=False,formal_submission=False),secondary_metrics=['First production source hash change (operation-end upper bound)','First locally supported assertion with matching production revision','First observed applicable production patch (not merely nonempty)','Explicit successful submit and post-submit tools','Final production patch SHA and diagnostic-only changes','Agent and Worker wall time','Charged tools and actual HTTP requests/responses','Received prompt/completion tokens; missing remains null','Repeated unchanged tests/searches with input/source epoch','Context guard request input growth and stop state','Native TaskResult/JUnit','Infrastructure errors and cleanup'],context_guard='Unchanged; independently record guard stop and resolved; correctness at guard only supported by unchanged production patch plus native result, otherwise null',analysis='Task-level paired descriptive counts Both/A-only/B-only/Neither/Unknown. Four tasks, same-repository dependence. No statistical proof, score conversion or single-mechanism claims. GPU03 is separate exploratory cohort; show independent and combined summaries. Token costs include failures and unknown usage flags.',partial='At16 insufficient preserve actual2-3 tasks; only predeclared task batches with available admitted tasks may run, report deviation. No historic fill-in or enlarged pool.',publication='Raw evaluator, patches, private traces and signed links outside Git; public safe derived metadata only'))

if __name__=='__main__': freeze()
