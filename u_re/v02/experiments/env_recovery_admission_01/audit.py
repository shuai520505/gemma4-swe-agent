"""Derive public results and locks from version-bound private CPU evidence."""
import ast,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from .dependencies import HERE,ROOT,ID,sha,write

def archive_binding(path,attempt):
    path=Path(path).resolve();assert not path.is_relative_to(ROOT)
    cpu=HERE/attempt;receipt=json.loads((cpu/'execution/HTTP_RECEIPT.json').read_bytes())
    manifest=json.loads(sorted((cpu/'read_observations').glob('read-*/OUTPUT_MANIFEST.json'))[-1].read_bytes())
    assert manifest['status']=='COMPLETE' and manifest['version_bound_before_after']
    item=next(f for f in manifest['files'] if f['file']=='v02b-'+attempt+'.zip')
    assert item['Notebook_id']==receipt['Notebook_id'] and item['version']==receipt['accepted_version']==1 and item['complete']
    assert sha(path.read_bytes())==item['sha256']
    return dict(attempt=attempt,Notebook_id=receipt['Notebook_id'],version=1,status='COMPLETE',private_path=str(path),sha256=sha(path.read_bytes()),bytes=path.stat().st_size,CRC_valid=True)

def recovery(path,attempt='recovery02'):
    binding=archive_binding(path,attempt)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        load=lambda n:json.loads(z.read(n))
        build=json.loads((HERE/attempt/'BUILD.json').read_bytes())
        for n,h in build['payload_members'].items():assert sha(z.read('source/'+n))==h,n
        report=load('validation/ENVIRONMENT_RECOVERY.json');assert report['status']=='INDEPENDENT_DEPENDENCY_RECOVERED'
        assert report['owned_assertion_canary_passed'] and report['native_Verifier_source_unchanged'] and report['inputs_unchanged']
        assert report['recovered']==load('validation/RECOVERED_ENVIRONMENT.json')
        for row in report['rows']:
            assert row['evidence_ok'] and row['cleanup'] and row['source_unchanged'] and row['provenance']
            if row['environment']=='RECOVERED':
                p='validation/recovered/'+row['instance_id']+'/'
                assert sha(z.read(p+'phase2.junit.xml'))==row['JUnit_sha256']
                assert sha(z.read(p+'official_result.json'))==row['TaskResult_sha256']
                assert z.read(p+'before.json')==z.read(p+'after.json')
                assert not load(p+'official_result.json')['resolved']
        source=load('validation/SOURCE_API_AUDIT.json')
        assert source['exception_class_absent'] and source['source_is_original_workspace']
        old=json.loads((HERE/'ORIGINAL_DIAGNOSTIC_REFERENCE.json').read_bytes())
        with zipfile.ZipFile(old['private_raw_archive']) as original:
            assert sha(Path(old['private_raw_archive']).read_bytes())==old['raw_archive_sha256']
            original_source=json.loads(original.read('validation/original/fastapi_14609/PRIVATE_BASE_SOURCE.json'))
            assert original_source['fastapi/exceptions.py']['sha256']==source['exception_module_sha256']
        carry=next(r for r in report['rows'] if r['instance_id']=='fastapi_5077' and r['environment']=='RECOVERED')
        assert carry['counts']['failures']>0 and carry['counts']['errors']==0 and carry['native_exit_code']==1
        source_hashes=load('validation/official_source_hashes.json')
    safe_source={k:v for k,v in source.items() if k!='exception_classes'}
    write(HERE/'ENVIRONMENT_RECOVERY.json',dict(status='INDEPENDENT_DEPENDENCY_RECOVERED',source_archive=binding,original_source_archive=dict(Notebook_id=old['Notebook_id'],sha256=old['raw_archive_sha256']),rows=report['rows'],original_environment=report['original'],recovered_environment=report['recovered'],target_exception_source_audit=safe_source,old_experiments_modified=False,all_new_candidates_or_models_executed=False))
    prior=ROOT/'u_re/v01/experiments/action_priority_01/integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json'
    environment=dict(experiment_id=ID,status='FROZEN_AFTER_REAL_CPU_RECOVERY',fingerprint=report['recovered'],new_artifacts=json.loads((HERE/'NEW_DEPENDENCIES.json').read_bytes())['packages'],native_Verifier_source_sha256=source_hashes,approved_official_task_wheels_lock=str(prior.relative_to(ROOT)),approved_official_task_wheels_lock_sha256=sha(prior.read_bytes()),build_script_sha256=sha((HERE/'notebook.py').read_bytes()),native_adapter_sha256=sha((HERE/'runtime.py').read_bytes()),research_JUnit_reader_sha256=sha((HERE/'junit_audit.py').read_bytes()),network='Notebook Internet=false. All three fixed additional public wheels embedded and SHA checked; pip --no-index --no-deps. No per-task dependency installs.',native_task_source_sha256=sha((ROOT.parent/'official-inputs/tasks.jsonl').read_bytes()),task_project_version='Each immutable Snapshot supplies its own project code/editable version. Third-party environment is fixed, not selected by task result.',Agent_runtime='Original GPU03 chroot copy allowlist/fingerprint remains separate; evaluator-only files never copied. New package install is trusted-side research preparation, not an alteration to frozen Agent ZIP or official scoring environment.',recovery_archive_sha256=binding['sha256'])
    write(HERE/'V02B_ENVIRONMENT_LOCK.json',environment)
    carry=dict(carry,status='CARRIED_FORWARD_BASELINE_ELIGIBLE',category='CARRY',eligible=True,role='CARRIED_FORWARD_NOT_NEW',source_archive=binding)
    pool=json.loads((HERE/'TASK_POOL_FREEZE.json').read_bytes())
    sources={n:sha((HERE/n).read_bytes()) for n in ('runtime.py','policy.py','junit_audit.py','screen.py','dependencies.py')}
    protocol=dict(experiment_id=ID,status='FROZEN_BEFORE_FIRST_NEW_NATIVE_BASELINE',source_base='6f6b7500baa007ee317466b93329ce99cf58950e',pool_sha256=sha((HERE/'TASK_POOL_FREEZE.json').read_bytes()),environment_lock_sha256=sha((HERE/'V02B_ENVIRONMENT_LOCK.json').read_bytes()),approved_tasks_file_sha256=environment['native_task_source_sha256'],execution_sources=sources,max_new_checks=24,target_total=4,new_target=3,carry_migration=carry,screen_order=[r['instance_id'] for r in pool['next_max24_in_order']],classification=dict(A='Confirmed external dependency absence requires actual interpreter metadata and frozen declaration, or pre-established inline-snapshot. REJECT_CONTINUE.',B='Issue-supported absent workspace API/signature with explicit original source+trace correspondence; CONDITIONAL_TARGET_FAILURE, never formally eligible.',C='Only independently proven A+B components: REJECT_CONTINUE while environment component remains; no formal eligibility.',D='Any unclassified error, unobserved dependency state or mixed unknown component: STOP.',E='Input/source/Verifier/JUnit verdict/provenance/environment/cleanup mismatch: STOP.',snapshot_assertion='Only exact duplicate inline-snapshot0.21.1 teardown record paired to same-test snapshot call assertion, matching unique suite aggregates and verified upstream plugin source. Preserve all raw errors and native negative verdict; no independent environment error. Other duplicates/teardowns STOP.'),eligibility='Discriminating native call assertion in the original evaluator contract; all independent environment errors absent; original source/config/test identities and cleanup valid; offline Issue relation review before final selection lock.',order='T1 carried5077,then first3 new formally eligible in frozen queue. T1 A-B,T2 B-A,T3 A-B,T4 B-A. Stop at4 total.',conditional_upgrade='Not permitted in this screening round; conditional cases do not fill formal task quota.',stopping='First four total eligible, max24 new, or first D/E. No reorder, task replacement by expected success, reference lookup or per-task environment repair.',statistical_scope='Report carry1 and new3 separately, plus descriptive paired total. All FastAPI; small sample, no cross-repository or significance claim. No actual Gemma this round.',GPU_authorized=False,formal_submission=False)
    write(HERE/'V02B_PROTOCOL_LOCK.json',protocol)
    print(json.dumps(dict(environment_recovered=True,carry='fastapi_5077',queue=protocol['screen_order'],new_max=24)))

def screening(path,attempt='screen01'):
    binding=archive_binding(path,attempt)
    protocol=json.loads((HERE/'V02B_PROTOCOL_LOCK.json').read_bytes())
    environment=json.loads((HERE/'V02B_ENVIRONMENT_LOCK.json').read_bytes())
    expected=json.loads((HERE/'APPROVED_INPUT_IDENTITIES.json').read_bytes())
    # Human Issue/native-contract review, made only after deterministic selection.
    # These are derived descriptions, never copied into any Agent input.
    contracts={
        'fastapi_5077':'Wrapped callables with forward-reference annotations: original native response assertion fails; migrated baseline remains discriminating.',
        'fastapi_11355':'Stringified dependency annotations: Issue requests evaluation support; original request returns validation failure instead of the expected normal response.',
        'fastapi_14463':'App-level Union responses with explicit content: Issue describes duplicate OpenAPI anyOf refs; original generated-schema equality assertion fails.',
        'fastapi_9555':'Wrapped coroutine/generator dependencies: Issue describes incorrect dependency-kind detection; original synchronous-generator assertion and asynchronous dependency calls fail during test execution, not collection.'}
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        load=lambda n:json.loads(z.read(n))
        build=json.loads((HERE/attempt/'BUILD.json').read_bytes())
        for n,h in build['payload_members'].items():assert sha(z.read('source/'+n))==h,n
        ledger=load('validation/TASK_ADMISSION_LEDGER.json')
        assert ledger['status']=='FOUR_TASKS_ADMITTED' and ledger['stop'] is None
        assert ledger['protocol_sha256']==sha((HERE/'V02B_PROTOCOL_LOCK.json').read_bytes())
        assert ledger['environment_lock_sha256']==protocol['environment_lock_sha256']
        assert load('validation/ENVIRONMENT_FINGERPRINT.json')==load('validation/FINAL_ENVIRONMENT_FINGERPRINT.json')==environment['fingerprint']
        assert load('validation/official_source_hashes.json')==environment['native_Verifier_source_sha256']
        assert [r['instance_id'] for r in ledger['rows']]==protocol['screen_order']
        checked=[r for r in ledger['rows'] if r['status']!='NOT_RUN']
        assert len(checked)==ledger['checked_new']==3 and len(ledger['selected'])==4
        assert [r['instance_id'] for r in checked]==protocol['screen_order'][:3]
        for r in checked:
            ident=r['instance_id'];p='validation/'+r['raw_directory']+'/'
            assert r['identity']==expected[ident]
            assert r['eligible'] and r['evidence_ok'] and r['cleanup'] and r['source_unchanged'] and r['provenance']
            assert r['counts']['failures']>0 and r['counts']['errors']==0 and r['native_exit_code']==1
            assert sha(z.read(p+'official_result.json'))==r['TaskResult_sha256']
            assert sha(z.read(p+'phase2.junit.xml'))==r['JUnit_sha256']
            assert not load(p+'official_result.json')['resolved']
            assert z.read(p+'before.json')==z.read(p+'after.json')
            cases=list(ET.fromstring(z.read(p+'phase2.junit.xml')).iter('testcase'))
            assert r['counts']==dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
        assert ledger['carry']==protocol['carry_migration']
        selected=[]
        for i,r in enumerate(ledger['selected'],1):
            assert r['instance_id'] in contracts
            selected.append(dict(task_label='T'+str(i),instance_id=r['instance_id'],role=r['role'],identity=r['identity'],native_baseline_counts=r['counts'],TaskResult_sha256=r['TaskResult_sha256'],JUnit_sha256=r['JUnit_sha256'],source_archive=r.get('source_archive',binding),environment_lock_sha256=protocol['environment_lock_sha256'],Issue_contract_review=contracts[r['instance_id']],formally_eligible=True))
    ledger.update(source_archive=binding,offline_contract_review_complete=True)
    write(HERE/'TASK_ADMISSION_LEDGER.json',ledger)
    write(HERE/'SELECTED_TASKS.json',dict(experiment_id=ID,status='FOUR_TASKS_FORMALLY_ADMITTED',tasks=selected,carry_count=1,new_count=3,scope='SAME_REPOSITORY_REPLICATION; carry analyzed separately; no Gemma runs in this round',environment_lock_sha256=protocol['environment_lock_sha256']))
    print(json.dumps(dict(Notebook_id=binding['Notebook_id'],checked_new=3,selected=[r['instance_id'] for r in selected],archive_sha256=binding['sha256'])))

if __name__=='__main__':
    import sys
    if sys.argv[1]=='recovery':recovery(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'recovery02')
    elif sys.argv[1]=='screen':screening(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'screen01')
