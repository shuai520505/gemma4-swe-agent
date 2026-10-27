"""Offline regression/privacy/source audit; never dispatch a Notebook."""
import io
import json
import re
import subprocess
import unittest

from .prepare import HERE, OLD, ROOT, PRIVATE, PRIOR, sha, write, verify_history
from egrd.v031.prepare import PRIOR_PRIVATE


def run():
    verify_history()
    PRIVATE.mkdir(parents=True,exist_ok=True)
    suite=unittest.TestSuite()
    excluded={'egrd.v031.test_preparation.Preparation.test_namespace_and_frozen_history_unchanged',
              'egrd.v03.test_platform.Platform.test_frozen_candidates_and_history_unchanged'}
    def add(node):
        if isinstance(node,unittest.TestSuite):
            for child in node:add(child)
        elif node.id() not in excluded:suite.addTest(node)
    for name in ('egrd.v0311.test_recovery','egrd.v031.test_preparation','egrd.v03.test_platform','egrd.v023.test_recovery'):
        add(unittest.defaultTestLoader.loadTestsFromName(name))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (PRIVATE/'OFFLINE_TEST_LOG.txt').write_text(stream.getvalue(),encoding='utf8',newline='\n')
    assert result.wasSuccessful(),stream.getvalue()
    issue=json.loads((PRIOR/'original_task.json').read_bytes())['problem_statement'].encode()
    regression=(PRIOR/'regression.py').read_bytes()
    probe=(PRIOR_PRIVATE/'probes/django__django-16333.py').read_bytes()
    patterns=[rb'-----BEGIN [A-Z ]*PRIVATE KEY-----',rb'gh[pousr]_[A-Za-z0-9]{25,}',
              rb'github_pat_[A-Za-z0-9_]{25,}',rb'(?i)X-(?:Goog|Amz)-Signature=',
              rb'(?i)"(?:api_key|access_token|refresh_token)"\s*:\s*"[^"\s]{8,}"']
    files={p.relative_to(HERE).as_posix():p.read_bytes() for p in HERE.rglob('*')
           if p.is_file() and '__pycache__' not in p.parts and p.name not in ('INTEGRITY_MANIFEST.json','OFFLINE_VALIDATION.json')}
    for name,raw in files.items():
        assert not name.endswith(('.zip','.tgz','.whl','.ipynb','.log'))
        assert issue not in raw and regression not in raw and probe not in raw and b'\r\n' not in raw,name
        for pattern in patterns:assert not re.search(pattern,raw),name
        if name.endswith('.py'):compile(raw,name,'exec')
        if name.endswith('.json'):json.loads(raw)
    for args in (['git','diff','--check'],['git','diff','--cached','--check']):
        subprocess.run(args,cwd=ROOT,check=True)
    report=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
                scope_assertions_replaced=sorted(excluded),replacement='Recovery.test_unchanged_history_and_scope',
                device_tests='SIMULATED_OS_CASES_ONLY',local_git='ACTUAL_LOCAL_GIT_SYNTHETIC_CONFIG',
                local_HTTP='ACTUAL_LOCAL_SCRIPTED_HTTP_WITH_DURABLE_CAPTURE',
                JSON_parse='PASS',Python_syntax='PASS',privacy_scan='PASS_PLUS_MANUAL_REVIEW',git_diff_check='PASS',
                result_schema_and_negative_cases='PASS',
                initial_pre_dispatch_audit='Stopped on CRLF in two new Git policy files; normalized before dispatch',
                initial_post_run_collector='Stopped on frozen prompt CRLF versus compiled LF hash; accounted for native text loading without runtime change',
                test_log_sha256=sha((PRIVATE/'OFFLINE_TEST_LOG.txt').read_bytes()))
    write(HERE/'OFFLINE_VALIDATION.json',report)
    files['OFFLINE_VALIDATION.json']=(HERE/'OFFLINE_VALIDATION.json').read_bytes()
    write(HERE/'INTEGRITY_MANIFEST.json',dict(base_commit='017bb9039c666ae50dcb3447cc8dcdc1f72d8149',
        public_files={n:sha(b) for n,b in sorted(files.items())},
        original_v031_manifest_sha256=sha((OLD/'INTEGRITY_MANIFEST.json').read_bytes()),
        S0_zip_sha256=sha((ROOT/'candidates/s0/submission.zip').read_bytes()),
        preserved_receipt_sha256=sha((OLD/'EVIDENCE_RECEIPT.json').read_bytes()),
        historical_results_modified=False,manifest_self_excluded=True))
    print(json.dumps(report,indent=2))


if __name__=='__main__':run()
