"""Apply the inherited PR26 classifier, preserving the screen01 stop event."""
import json,zipfile
from .common import HERE,ROOT,ID,sha,write
from .audit import bind,native_counts
from u_re.v02.experiments.env_recovery_admission_01.policy import classify

CONTRACTS={
    'fastapi_14297':dict(relation='Original Issue describes optional sequence serialization failure; the native suite has three test-call failures on that behavior, including the same runtime exception. No collection/setup failure.',evidence_kind='Issue text + native failure call chain + original workspace source/provenance',independent_environment_errors=0),
    'fastapi_14459':dict(relation='Original Issue describes lost inherited OAuth2 scope metadata. Two native schema-equality call assertions exercise that contract. Their two additional teardown entries repeat the exact same snapshot mismatch; frozen PR26 parser and plugin SHA prove pairing, not independent environment errors.',evidence_kind='Issue text + original snapshot assertions + same-test exact teardown pairing + pinned inline-snapshot plugin source',independent_environment_errors=0)
}

def normalize(archive):
    binding=bind(archive,'screen01')
    originals={r['instance_id']:r for r in map(json.loads,(ROOT.parent/'official-inputs/tasks.jsonl').read_text(encoding='utf8').splitlines())}
    with zipfile.ZipFile(archive) as z:
        load=lambda n:json.loads(z.read(n));raw=z.read('validation/TASK_ADMISSION_RESULTS.json');ledger=json.loads(raw)
        identities=load('validation/TASK_IDENTITY_LOCK.json');assert identities['conflicts']==[]
        selected=[];rows=[];deltas=[];stop=None
        for original in ledger['rows']:
            ident=original['instance_id']
            if original['status']=='NOT_RUN':rows.append(dict(instance_id=ident,rank=original['rank'],status='NOT_RUN',eligible=None));continue
            root='validation/'+original['raw_directory']+'/'
            evidence=load(root+'BASELINE_EVIDENCE.json');audit=load(root+'audit.json')
            versions=load(root+'INTERPRETER.json')['versions']
            if root+'MISSING_DEPENDENCY_PROBE.json' in z.namelist():versions.update(load(root+'MISSING_DEPENDENCY_PROBE.json')['versions'])
            source=load(root+'PRIVATE_BASE_SOURCE.json')
            decision=classify(evidence,audit,source,originals[ident]['problem_statement'],versions)
            assert sha(originals[ident]['problem_statement'].encode())==evidence['identity']['issue_sha256']
            count=native_counts(z,root);assert count==evidence['counts']
            row=dict(evidence,rank=original['rank'],frozen_classifier_decision=decision,status=decision['status'],eligible=decision['eligible'],raw_original_status=original['status'],raw_original_category=original['category'])
            if decision['eligible']:
                assert ident in CONTRACTS and evidence['evidence_ok'] and evidence['cleanup'] and evidence['source_unchanged'] and evidence['provenance']
                assert evidence['native_resolved'] is False and evidence['native_exit_code']==1 and count['failures']>0
                assert not audit['infrastructure_stop']
                if count['errors']:
                    assert audit['snapshot_assertion_teardown_proven'] and audit['environment_errors']==0 and audit['duplicate_snapshot_finalizer_errors']==count['errors']
                review=dict(CONTRACTS[ident],Issue_sha256=evidence['identity']['issue_sha256'],TaskResult_sha256=evidence['TaskResult_sha256'],JUnit_sha256=evidence['JUnit_sha256'],research_reader_sha256=sha((ROOT/'u_re/v02/experiments/env_recovery_admission_01/junit_audit.py').read_bytes()),raw_archive_sha256=binding['sha256'])
                selected.append(dict(task_label='T'+str(len(selected)+1),**evidence['identity'],snapshot_tree_sha256=identities['all129'][ident]['snapshot_tree_sha256'],test_overlay_content_sha256=identities['all129'][ident]['test_overlay_content_sha256'],native_baseline_counts=count,native_resolved=False,TaskResult_sha256=evidence['TaskResult_sha256'],JUnit_sha256=evidence['JUnit_sha256'],environment_lock_sha256=sha((HERE/'ENVIRONMENT_LOCK.json').read_bytes()),source_archive=binding,source_unchanged=True,provenance_verified=True,alias_conflicts=[],cleanup=True,formal_admission_status='BASELINE_ELIGIBLE',Issue_relation_review=review,independent_environment_errors=0,snapshot_duplicate_teardown_count=audit.get('duplicate_snapshot_finalizer_errors',0)))
            if original['status']!=decision['status']:deltas.append(dict(instance_id=ident,original_status=original['status'],frozen_classifier_status=decision['status'],reason='Screen adapter wrongly imposed raw errors==0; inherited protocol requires no independent environment error and PR26 exact pairing already proves these duplicates'))
            rows.append(row)
            if decision['status']=='STOP':stop=dict(task=ident,reason=decision['reason']);break
        assert stop is None and len(selected)==2
        assert [r['instance_id'] for r in selected]==[r['instance_id'] for r in rows if r.get('eligible')][:2]
    write(HERE/'NORMALIZED_ADMISSION_VIEW.json',dict(experiment_id=ID,status='TWO_TASKS_FORMALLY_ADMITTED',source_archive=binding,original_screen_ledger_sha256=sha(raw),original_screen_status=ledger['status'],original_stop_preserved=ledger['stop'],classifier_path='u_re/v02/experiments/env_recovery_admission_01/policy.py',classifier_sha256=sha((ROOT/'u_re/v02/experiments/env_recovery_admission_01/policy.py').read_bytes()),classification_changes=deltas,rows=rows,checked=3,stop=None,historical_files_or_native_results_modified=False,threshold_change=False))
    write(HERE/'SELECTED_TASKS.json',dict(experiment_id=ID,status='TWO_TASKS_FORMALLY_ADMITTED',selection='First two eligible under unchanged inherited classifier plus raw Issue-contract review',tasks=selected,GPU_authorized=False))
    categories={'TARGET_BEHAVIOR_FAILURE':'TARGET_BEHAVIOR_FAILURE','NON_DISCRIMINATING':'NON_DISCRIMINATING','A':'ENVIRONMENT_BLOCKED','B':'CONDITIONAL_TARGET_FAILURE','C':'ENVIRONMENT_BLOCKED','D':'UNKNOWN_FAILURE','E':'INTEGRITY_FAILURE'}
    canonical=[]
    for row in rows:
        decision=row.get('frozen_classifier_decision')
        canonical.append(dict(instance_id=row['instance_id'],rank=row['rank'],status=row['status'],category=categories[decision['category']] if decision else None,eligible=row['eligible'],native_resolved=row.get('native_resolved'),counts=row.get('counts'),TaskResult_sha256=row.get('TaskResult_sha256'),JUnit_sha256=row.get('JUnit_sha256'),cleanup=row.get('cleanup'),Issue_relation_verified=row['instance_id'] in CONTRACTS if row.get('eligible') else None))
    write(HERE/'TASK_ADMISSION_RESULTS.json',dict(experiment_id=ID,status='TWO_TASKS_FORMALLY_ADMITTED',checked=3,rows=canonical,selected_ids=[t['instance_id'] for t in selected],source_archive=binding,raw_original_record=dict(path='SCREEN01_RAW_SUMMARY.json',status=ledger['status'],stop=ledger['stop'],raw_ledger_sha256=sha(raw)),normalization='Frozen PR26 classifier + exact snapshot-phase proof + Issue review. Original output bytes/status retained; no native result or threshold altered.',GPU_authorized=False))
    print(json.dumps(dict(selected=[t['instance_id'] for t in selected],errors_preserved=[t['native_baseline_counts']['errors'] for t in selected],independent_environment_errors=0,original_STOP_preserved=True)))

if __name__=='__main__':
    import sys
    normalize(sys.argv[1])
