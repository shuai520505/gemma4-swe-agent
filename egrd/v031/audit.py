"""Offline checks and manifest only; never dispatch, infer or execute task code."""
import io
import json
import re
import subprocess
import unittest

from .prepare import HERE,ROOT,PRIVATE,PRIOR_PRIVATE,sha,write


def run():
    suite=unittest.TestSuite()
    replaced='egrd.v03.test_platform.Platform.test_frozen_candidates_and_history_unchanged'
    def add(node):
        if isinstance(node,unittest.TestSuite):
            for child in node:add(child)
        elif node.id()!=replaced:suite.addTest(node)
    for name in ('egrd.v031.test_preparation','egrd.v03.test_platform','egrd.v023.test_recovery'):
        add(unittest.defaultTestLoader.loadTestsFromName(name))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (PRIVATE/'OFFLINE_TEST_LOG.txt').write_text(stream.getvalue(),encoding='utf8',newline='\n')
    assert result.wasSuccessful(),stream.getvalue()
    forbidden=[rb'-----BEGIN [A-Z ]*PRIVATE KEY-----',rb'gh[pousr]_[A-Za-z0-9]{25,}',
        rb'github_pat_[A-Za-z0-9_]{25,}',rb'(?i)"(?:api_key|access_token|refresh_token)"\s*:\s*"[^"\s]{8,}"',
        rb'(?i)X-(?:Goog|Amz)-Signature=']
    files={p.relative_to(HERE).as_posix():p.read_bytes() for p in HERE.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.name not in ('INTEGRITY_MANIFEST.json','OFFLINE_VALIDATION.json')}
    original=json.loads((PRIVATE/'original_task.json').read_bytes())['problem_statement'].encode()
    probe=(PRIOR_PRIVATE/'probes/django__django-16333.py').read_bytes()
    regression=(PRIVATE/'regression.py').read_bytes()
    for name,body in files.items():
        assert b'\r\n' not in body,name
        assert not name.endswith(('.zip','.tgz','.whl','.ipynb','.log'))
        assert original not in body and probe not in body and regression not in body,name
        for pattern in forbidden:assert not re.search(pattern,body),(name,pattern)
        if name.endswith('.json'):json.loads(body)
        if name.endswith('.py'):compile(body,name,'exec')
    changed=subprocess.check_output(['git','diff','--name-only','5829838066b5c3cfb3037ebbf2613011c2d4f214'],cwd=ROOT,text=True).splitlines()
    assert all(n.startswith('egrd/v031/') for n in changed),changed
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    assert sorted(p.name for p in PRIVATE.glob('CPU_DISPATCH_V*.json'))==['CPU_DISPATCH_V1.json','CPU_DISPATCH_V2.json']
    validation=dict(offline_tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        inherited_scope_test_replaced_by_current_namespace_check=replaced,
        replacement_test='egrd.v031.test_preparation.Preparation.test_namespace_and_frozen_history_unchanged',
        JSON_parse='PASS',Python_compile='PASS',git_diff_check='PASS',
        public_raw_issue_probe_regression_scan='PASS',credential_pattern_scan='PASS_WITH_MANUAL_REVIEW',
        test_log_sha256=sha((PRIVATE/'OFFLINE_TEST_LOG.txt').read_bytes()),
        initial_local_test_fixture_error='Three null-device fixture tests initially had a Python class-scope NameError; corrected before final offline acceptance.',
        actual_CPU_versions=2,real_Gemma_requests=0,GPU=False,formal_submission=False,
        CPU_acceptance='BLOCKED',post_V2_fix='NOT_KAGGLE_VALIDATED',null_device_tests='SIMULATED_OS_CASES_ONLY')
    write(HERE/'OFFLINE_VALIDATION.json',validation)
    files['OFFLINE_VALIDATION.json']=(HERE/'OFFLINE_VALIDATION.json').read_bytes()
    old=json.loads((HERE/'CPU_BUILD_V2.json').read_bytes())['members']
    runtime_changes={n:dict(tested_sha256=h,current_sha256=sha((ROOT/n).read_bytes()))
        for n,h in old.items() if n.startswith('egrd/v031/') and (ROOT/n).is_file() and sha((ROOT/n).read_bytes())!=h}
    assert set(runtime_changes)=={'egrd/v031/cpu_preflight.py','egrd/v031/sandbox_adapter.py'}
    references=['candidates/s0/manifest.json','candidates/s0/submission.zip','s1/frozen_integrity.json',
        's1/results/s0-score-observation.json','egrd/v03/INTEGRITY_MANIFEST.json','egrd/v03/TASK_REPRODUCTIONS.json',
        'egrd/v03/DATASET_MANIFEST.json','egrd/v03/DEPENDENCY_LOCK.json','egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json',
        'egrd/v022/submission_N.zip','egrd/v022/submission_D.zip']
    write(HERE/'INTEGRITY_MANIFEST.json',dict(base_commit='5829838066b5c3cfb3037ebbf2613011c2d4f214',
        public_files={n:sha(b) for n,b in sorted(files.items())},
        historical_references={n:sha((ROOT/n).read_bytes()) for n in references},
        actual_Notebook_id=141014201,actual_CPU_versions=[1,2],CPU_status='BOTH_ERROR',
        current_runtime_changes_from_tested_V2=runtime_changes,
        new_unvalidated_runtime_file=dict(path='egrd/v031/device_runtime.py',sha256=sha((HERE/'device_runtime.py').read_bytes())),
        current_runtime_Kaggle_validated=False,raw_evidence_root=str(PRIVATE),
        private_task_input_diff_sha256=sha((PRIVATE/'TASK_INPUT_DIFF.txt').read_bytes()),
        original_task_private_file_sha256=sha((PRIVATE/'original_task.json').read_bytes()),
        public_raw_task_bodies=False,manifest_self_excluded=True))
    print(json.dumps(validation,indent=2))


if __name__=='__main__':run()
