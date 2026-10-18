"""Actual file/manager/audit path; historical replay is byte-pinned and read-only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from harness_v2.evidence import Journal,atomic_json
from .audit import audit_verifier as production_audit
from .environment import SubprocessManager


def audit_verifier(directory,**kwargs):
    source=Path(directory);counter=len(list((source/'evaluated_inputs').glob('*')))
    evidence=source/'evaluated_inputs'/str(counter);evidence.mkdir(parents=True)
    for name in ('phase2_execution.json','phase2.junit.xml','phase2_junit_capture.json'):
        if (source/name).exists():shutil.copyfile(source/name,evidence/name)
    result=production_audit(directory,**kwargs)
    atomic_json(evidence/'result.json',result)
    atomic_json(Path(directory)/'structured_test_result.json',result)
    return result


class HistoricalTests(unittest.TestCase):
    def replay(self,name,baseline=None):
        fixtures=Path(__file__).with_name('fixtures')
        pins=json.loads((fixtures/'manifest.json').read_text());raw=(fixtures/name).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),pins[name]['sha256'])
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);(p/'phase2_execution.json').write_bytes(raw)
            return audit_verifier(p,baseline=baseline,historical_attestation={'phase2_sha256':pins[name]['sha256']})

    def test_A_frozen_Rich_failure_is_valid_and_does_not_stop(self):
        result=self.replay('rich_historical.json')
        self.assertEqual(result['category'],'assertion_failure');self.assertFalse(result['infrastructure_stop'])
        self.assertEqual(result['counts']['failures'],4);self.assertEqual(result['counts']['errors'],0)

    def test_B_frozen_Requests_missing_provider_is_environment_blocker(self):
        baseline=json.loads(Path(__file__).with_name('fixtures').joinpath('requests_baseline.json').read_text())
        self.assertFalse(baseline['requests_verifier_eligible'])
        self.assertTrue(all(not value for value in baseline['providers']['modules'].values()))
        result=self.replay('requests_historical.json',dict(environment_blocked_verified=True,
            matching_callchain_verified=True,proof='Frozen clean baseline and original fixture-callchain investigation'))
        self.assertEqual(result['category'],'setup_error');self.assertEqual(result['attribution'],'environment')
        self.assertTrue(result['infrastructure_stop']);self.assertFalse(result['confirmed_failure'])


class NativePathTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.manager=SubprocessManager(journal=Journal(self.root),base_dir=self.root/'sandbox_tmp',audit_modules=['sample_pkg'])
        self.manager.agent_id='CPU_evaluator';self.sid=self.manager.start()
        self.addCleanup(self.manager.cleanup_all)
        self.workspace=self.manager.sandboxes[self.sid]['workspace']
        (self.workspace/'tests').mkdir()

    def run_native(self,code,conftest=None):
        (self.workspace/'tests/test_case.py').write_text(code)
        if conftest is not None:(self.workspace/'tests/conftest.py').write_text(conftest)
        command='cd /workspace && PYTHONSAFEPATH=1 PYTHONNOUSERSITE=1 python3 -s -m pytest tests --junitxml=/tmp/_swegemma_junit_a11ce.xml -p no:anyio -o timeout=0 -o python_classes="Test* *Test" -q'
        result=self.manager.exec(self.sid,command,timeout=30)
        self.assertEqual(json.loads((self.root/'phase2_command.json').read_text())['command'],command)
        count=len(list((self.root/'original_native').glob('*')))
        original=self.root/'original_native'/str(count);original.mkdir(parents=True)
        for name in ('phase2_execution.json','phase2.junit.xml','phase2_junit_capture.json','phase2_command.json'):
            if (self.root/name).exists():shutil.copyfile(self.root/name,original/name)
        return result

    def tearDown(self):
        self.manager.cleanup_all()
        target=os.environ.get('S1_V3_TEST_EVIDENCE')
        if target:shutil.copytree(self.root,Path(target)/self._testMethodName,
            ignore=lambda directory,names:['sandbox_tmp'] if 'sandbox_tmp' in names else [])

    def test_C_real_pass_and_original_JUnit_survives_cleanup(self):
        self.assertEqual(self.run_native('def test_ok(): assert True\n').exit_code,0)
        before=(self.root/'phase2.junit.xml').read_bytes()
        self.manager.stop(self.sid)
        self.assertEqual((self.root/'phase2.junit.xml').read_bytes(),before)
        meta=json.loads((self.root/'phase2_junit_capture.json').read_text())
        self.assertEqual(meta['capture_phase'],'before_native_sandbox_stop')
        result=audit_verifier(self.root);self.assertEqual(result['category'],'passed');self.assertFalse(result['infrastructure_stop'])

    def test_D_mixed_assertion_and_setup_is_not_automatically_external(self):
        self.run_native('import pytest\n@pytest.fixture\ndef broken(): raise RuntimeError("fixture failure")\ndef test_a(): assert False\ndef test_b(broken): pass\n')
        result=audit_verifier(self.root,baseline={'eligible':True})
        self.assertIn('setup_error',result['categories']);self.assertIn('assertion_failure',result['categories'])
        self.assertTrue(result['infrastructure_stop']);self.assertNotEqual(result['attribution'],'environment')

    def test_E_actual_collection_error(self):
        self.assertEqual(self.run_native('import absent_cpu_validation_dependency\n').exit_code,2)
        result=audit_verifier(self.root);self.assertEqual(result['category'],'collection_error');self.assertTrue(result['infrastructure_stop'])

    def test_E_actual_internal_error(self):
        self.assertEqual(self.run_native('def test_ok(): pass\n','def pytest_collection(session): raise RuntimeError("CPU internal failure")\n').exit_code,3)
        result=audit_verifier(self.root);self.assertEqual(result['category'],'internal_error');self.assertTrue(result['infrastructure_stop'])

    def test_E_actual_executor_exception_without_Phase2(self):
        self.manager.exec(self.sid,'python3 -c "raise RuntimeError(123)"',timeout=30)
        result=audit_verifier(self.root);self.assertEqual(result['category'],'verifier_execution_error');self.assertTrue(result['infrastructure_stop'])

    def test_F_error_words_in_real_failure_data_do_not_mean_environment(self):
        self.run_native('def test_ERROR_ModuleNotFoundError(): assert False, "Found 4 errors in 2 files ModuleNotFoundError ERROR"\n')
        result=audit_verifier(self.root);self.assertEqual(result['category'],'assertion_failure');self.assertFalse(result['infrastructure_stop'])

    def test_F_error_words_in_normal_stdout_can_pass(self):
        self.run_native('def test_ERROR_ModuleNotFoundError():\n print("ERROR ModuleNotFoundError Found 4 errors")\n assert True\n')
        result=audit_verifier(self.root);self.assertEqual(result['category'],'passed');self.assertFalse(result['infrastructure_stop'])

    def test_G_missing_JUnit_fails_closed_even_after_actual_pass(self):
        self.run_native('def test_ok(): pass\n');(self.root/'phase2.junit.xml').unlink()
        result=audit_verifier(self.root);self.assertEqual(result['category'],'unknown_unparsed');self.assertTrue(result['infrastructure_stop'])

    def test_G_corrupt_JUnit_fails_closed(self):
        self.run_native('def test_ok(): pass\n');raw=b'<broken>'
        (self.root/'phase2.junit.xml').write_bytes(raw)
        meta=json.loads((self.root/'phase2_junit_capture.json').read_text());meta['sha256']=hashlib.sha256(raw).hexdigest()
        atomic_json(self.root/'phase2_junit_capture.json',meta)
        result=audit_verifier(self.root);self.assertEqual(result['category'],'unknown_unparsed');self.assertTrue(result['infrastructure_stop'])

    def test_G_summary_disagrees_with_real_JUnit(self):
        self.run_native('def test_ok(): pass\n')
        native=json.loads((self.root/'phase2_execution.json').read_text())
        native['stdout']=native['stdout'].replace('1 passed','2 passed')
        atomic_json(self.root/'phase2_execution.json',native)
        result=audit_verifier(self.root);self.assertEqual(result['category'],'unknown_unparsed');self.assertTrue(result['infrastructure_stop'])

    def test_changed_source_parser_error_can_be_attributed_to_regression(self):
        source=self.workspace/'sample_pkg.py';source.write_text('VALUE=1\n')
        self.run_native('import sample_pkg\ndef test_ok(): assert sample_pkg.VALUE==1\n')
        base_meta=json.loads((self.root/'phase2_junit_capture.json').read_text())
        self.assertFalse(audit_verifier(self.root)['infrastructure_stop'])
        source.write_text('def broken(:\n')
        self.run_native('import sample_pkg\ndef test_ok(): assert sample_pkg.VALUE==1\n')
        result=audit_verifier(self.root,baseline=dict(eligible=True,production_source_hashes=base_meta['production_source_hashes']))
        self.assertEqual(result['category'],'collection_error');self.assertEqual(result['attribution'],'agent_regression')
        self.assertFalse(result['infrastructure_stop']);self.assertTrue(result['confirmed_failure'])
