"""Read-only static evidence audit. Never imports FastAPI, Kaggle or Verifier."""
import ast
import hashlib
import json
from pathlib import Path
import tomllib
import xml.etree.ElementTree as ET
import zipfile

HERE=Path(__file__).resolve().parent
PILOT=HERE.parent
REC=PILOT/'attempts/cpu02/reconciliation_01'
NATIVE=REC/'native_evidence/validation/01-fastapi_14262'
ROOT=HERE.parents[4]


def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(path):return json.loads(Path(path).read_bytes())


def event_category(*, assertion=False, target_issue=False, base_absent=False,
                   trace_at_target=False, workspace_proven=False,
                   missing_unrelated_dependency=False):
    """Draft V2 rules, with explicit evidence predicates,not text matching."""
    if missing_unrelated_dependency:return 'ENVIRONMENT_COLLECTION_FAILURE'
    if assertion:return 'TARGET_BEHAVIOR_FAILURE'
    if all((target_issue,base_absent,trace_at_target,workspace_proven)):
        return 'TARGET_CAUSED_COLLECTION_FAILURE'
    return 'UNEXPLAINED_COLLECTION_FAILURE'


def draft_admission(categories, *, integrity=True, independent_validation=False):
    if not integrity:return 'STOP_INTEGRITY'
    if 'UNEXPLAINED_COLLECTION_FAILURE' in categories:return 'STOP_UNEXPLAINED'
    if 'ENVIRONMENT_COLLECTION_FAILURE' in categories:return 'ENVIRONMENT_BLOCKED'
    if 'TARGET_CAUSED_COLLECTION_FAILURE' in categories:
        # This tool cannot promote conditional evidence into official admission.
        return 'CONDITIONALLY_ELIGIBLE'
    if categories and all(x=='TARGET_BEHAVIOR_FAILURE' for x in categories):return 'NEGATIVE_BASELINE_CANDIDATE'
    return 'NOT_EVALUATED'


def analyze():
    issue=(HERE/'ISSUE_ORIGINAL.txt').read_bytes()
    identity=load(NATIVE/'task_identity.json')
    assert sha(issue)==identity['issue_sha256']=='63bfaef6461b9744eaf3a4ff2a1961b752638263ba8bd5c413761f5412255102'
    assert sha((HERE/'EVALUATOR_TEST_OVERLAY.txt').read_bytes())==identity['test_patch_sha256']
    before=load(NATIVE/'before_pytest_files.json');after=load(NATIVE/'after_pytest_files.json')
    assert before==after
    source_proof={}
    for name in ('fastapi/__init__.py','fastapi/param_functions.py','fastapi/params.py','pyproject.toml','requirements-tests.txt','tests/utils.py'):
        raw=(HERE/'base_source'/name).read_bytes()
        assert sha(raw)==before[name]==after[name],name
        source_proof[name]=dict(sha256=sha(raw),matches_runtime_before_after=True)
    tree=ast.parse((HERE/'base_source/fastapi/param_functions.py').read_text(encoding='utf-8'))
    node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='Depends')
    params=[a.arg for a in node.args.posonlyargs+node.args.args+node.args.kwonlyargs]
    assert params==['dependency','use_cache'] and node.args.kwarg is None
    issue_text=issue.decode()
    assert 'Depends(func, scope="function")' in issue_text and 'Depends(func, scope="request")' in issue_text
    imports=load(NATIVE/'import_audit/3cfb8d83126b467e940219b6e32aa62e/130-exit.json')
    for module in ('fastapi.param_functions','fastapi.params'):
        entry=imports['modules'][module];name=module.replace('.','/')+'.py'
        assert '/workspace/'+name in entry['realpath']
        assert entry['source_sha256']==before[name]
        assert any(x['filename']==entry['realpath'] for x in imports['executed_modules'])
    export=ast.parse((HERE/'base_source/fastapi/__init__.py').read_text())
    assert any(isinstance(n,ast.ImportFrom) and n.module=='param_functions' and any(a.name=='Depends' for a in n.names) for n in export.body)
    tests=[]
    for name,line in [('test_dependency_yield_scope.py',23),('test_dependency_yield_scope_websockets.py',26)]:
        source=(HERE/'evaluator_test_text/tests'/(name+'.txt')).read_text()
        parsed=ast.parse(source)
        calls=[n for n in ast.walk(parsed) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Depends']
        assert any(n.lineno==line and any(k.arg=='scope' and isinstance(k.value,ast.Constant) and k.value.value=='function' for k in n.keywords) for n in calls)
        tests.append(dict(file='tests/'+name,first_scope_call_line=line,
            category=event_category(target_issue=True,base_absent=True,trace_at_target=True,workspace_proven=True)))
    env_category=event_category(missing_unrelated_dependency=True)
    official=load(REC/'native_evidence/wheel_hashes.json');task=load(REC/'native_evidence/task_wheel_hashes.json')
    def canonical(s):return s.lower().replace('_','-').replace('.','-')
    wheels=[]
    for origin,collection in [('official',official),('task',task)]:
        for name,record in collection.items():
            distro=name.split('-')[0]
            if canonical(distro)=='inline-snapshot':wheels.append(dict(file=name,source=origin,record=record))
    assert not wheels
    requirements=(HERE/'base_source/requirements-tests.txt').read_text()
    req_line=next(i for i,x in enumerate(requirements.splitlines(),1) if x.startswith('inline-snapshot'))
    assert 'inline-snapshot>=0.21.1' in requirements
    config=tomllib.loads((HERE/'base_source/pyproject.toml').read_text(encoding='utf-8'))
    extras=config['project']['optional-dependencies']
    assert not any('inline-snapshot' in x for group in extras.values() for x in group)
    result=load(NATIVE/'official_result.json');execution=load(NATIVE/'phase2_execution.json')
    junit=(NATIVE/'phase2.junit.xml').read_bytes();capture=load(NATIVE/'phase2_junit_capture.json')
    cases=list(ET.fromstring(junit).iter('testcase'))
    assert len(cases)==3 and all(x.find('error') is not None for x in cases)
    assert result['test_exit_code']==execution['exit_code']==2 and result['agent_patch']==''
    assert sha(junit)==capture['sha256']
    ledger=load(REC/'TASK_SCREENING_LEDGER.json')
    assert ledger['rows'][0]['workspace_files_unchanged'] is True
    assert ledger['checked']==1 and ledger['status']=='TASK_ADMISSION_BLOCKED'
    return dict(task='fastapi_14262',base=identity['base_commit'],overall='MIXED_CAUSES',
        scope_attribution='TARGET_CAUSED_COLLECTION_CONFIRMED',base_feature='TARGET_FEATURE_ABSENT',
        Depends_definition_line=node.lineno,Depends_parameters=params,Depends_has_varkw=False,
        target_events=tests,environment_event=dict(category=env_category,dependency='inline-snapshot',
            module='inline_snapshot',status='DECLARED_BUT_NOT_INSTALLED',declaration='requirements-tests.txt',
            declaration_line=req_line,declared_specifier='>=0.21.1',approved_wheels=wheels,
            availability='APPROVED_WHEEL_UNAVAILABLE',recovery='OFFLINE_DEPENDENCY_RECOVERY_UNAVAILABLE',
            Requires_Python=None,transitive_dependencies=None,ABI_tags=None,
            version_incompatibility_proven=False,not_installable_by_runtime_extras=True),
        frozen_wheel_count=dict(official=len(official),task=len(task)),
        source_proof=source_proof,workspace_hash_count=len(before),before_after_equal=True,
        old_report_missing_snapshots_statement='INCORRECT_RAW_FILES_EXIST_AND_LEDGER_TRUE',
        JUnit_sha256=sha(junit),TaskResult_sha256=sha((NATIVE/'official_result.json').read_bytes()),
        V1_original='CPU_TASK_ADMISSION_BLOCKED',V2_draft_task_decision=draft_admission([x['category'] for x in tests]+[env_category]),
        V2_draft_target_only_decision=draft_admission([x['category'] for x in tests]),
        next_decision='ENVIRONMENT_RECOVERY_BLOCKED',
        new_Kaggle_requests=0,new_official_task_executions=0,GPU=0,Gemma=0,Agent=0,Submission=0)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    facts=analyze()
    if args.write:
        with (HERE/'STATIC_FINDINGS.json').open('x',encoding='utf-8') as f:json.dump(facts,f,indent=2);f.write('\n')
    print(json.dumps({k:facts[k] for k in ('overall','scope_attribution','next_decision','workspace_hash_count','before_after_equal','V2_draft_task_decision')}))
