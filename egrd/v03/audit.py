"""Offline provenance/privacy gate. Does not call Kaggle or execute task probes."""
import io
import json
import re
import subprocess
import unittest

from .cli import HERE,ROOT,PRIVATE,sha,write


def run():
    receipt=PRIVATE/'remote-v2-receipt'
    for name in ('RESULTS_MANIFEST.json','TASK_REPRODUCTIONS.json','CPU_EXECUTION_RECORD.json'):
        expected=(PRIVATE/'dataset-v2'/name).read_bytes()
        assert (receipt/name).read_bytes()==expected,('Remote V2 sidecar mismatch',name)
    files={p.relative_to(HERE).as_posix():p.read_bytes() for p in HERE.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.name not in ('INTEGRITY_MANIFEST.json','OFFLINE_VALIDATION.json')}
    forbidden=[rb'-----BEGIN [A-Z ]*PRIVATE KEY-----',rb'gh[pousr]_[A-Za-z0-9]{25,}',
        rb'github_pat_[A-Za-z0-9_]{25,}',rb'(?i)"(?:api_key|access_token|refresh_token)"\s*:\s*"[^"\s]{8,}"',
        rb'(?i)X-(?:Goog|Amz)-Signature=',rb'(?i)"(?:patch|test_patch|problem_statement|model_reasoning)"\s*:']
    for name,body in files.items():
        assert len(body)<200000,name
        assert not name.endswith(('.zip','.tgz','.whl','.log','.ipynb'))
        assert b'\r\n' not in body,('LF required',name)
        for pattern in forbidden:assert not re.search(pattern,body),(name,pattern)
        if name.endswith('.json'):json.loads(body)
        if name.endswith('.py'):compile(body,name,'exec')
    suite=unittest.defaultTestLoader.loadTestsFromNames(['egrd.v03.test_platform','egrd.v023.test_recovery'])
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (PRIVATE/'OFFLINE_TEST_LOG.txt').write_text(stream.getvalue(),encoding='utf8',newline='\n')
    assert result.wasSuccessful(),stream.getvalue()
    difference=subprocess.check_output(['git','diff','--name-only','c8c92a45688a4a7005dea852e7927baefe980402'],cwd=ROOT,text=True).splitlines()
    assert all(p.startswith('egrd/v03/') for p in difference),difference
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    validation=dict(offline_tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        skipped=len(result.skipped),public_JSON_parse='PASS',Python_compile='PASS',
        privacy_pattern_scan='PASS_WITH_MANUAL_REVIEW_REQUIRED',
        remote_V2_sidecars_byte_identity='PASS',historical_tracked_diff='UNCHANGED',
        git_diff_check='PASS',test_log_sha256=sha((PRIVATE/'OFFLINE_TEST_LOG.txt').read_bytes()),
        Gemma_requests=0,GPU_inference=False,formal_submission=False)
    write(HERE/'OFFLINE_VALIDATION.json',validation)
    files['OFFLINE_VALIDATION.json']=(HERE/'OFFLINE_VALIDATION.json').read_bytes()
    references=['egrd/v023/EXTERNAL_SOURCE_LOCK.json','egrd/v023/EXTERNAL_SNAPSHOT_CHECKS.json',
        'egrd/v022/TASK_POOL_LOCK.json','egrd/v022/submission_N.zip','egrd/v022/submission_D.zip',
        'meer/v01/CANDIDATE_MANIFEST.json']
    manifest=dict(schema='EGRD_V03_INTEGRITY_V1',base_commit='c8c92a45688a4a7005dea852e7927baefe980402',
        historical_references={p:sha((ROOT/p).read_bytes()) for p in references},
        public_files={n:sha(b) for n,b in sorted(files.items())},
        private_evidence_root=str(PRIVATE),raw_archive_sha256=json.loads((HERE/'RAW_ARCHIVES.json').read_bytes())['archives'][0]['sha256'],
        dataset_id=12872403,dataset_version=2,Notebook_id=141004018,Notebook_version=1,
        raw_tests_probes_snapshots_logs_public=False,manifest_self_excluded=True)
    write(HERE/'INTEGRITY_MANIFEST.json',manifest)
    print(json.dumps(validation,indent=2))


if __name__=='__main__':run()
