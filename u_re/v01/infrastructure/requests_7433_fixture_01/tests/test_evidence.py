"""Read-only regression of actual saved Linux diagnostic evidence, not mock tests."""
import hashlib
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
import zipfile
from u_re.v01.infrastructure.requests_7433_fixture_01.assess import assess

HERE=Path(__file__).resolve().parents[1]
RUN=HERE/'results/cpu01/validation'


class EvidenceTests(unittest.TestCase):
    def test_raw_archive_complete_and_no_silent_corruption(self):
        raw=HERE/'results/cpu01/raw.zip'
        receipt=json.loads((raw.parent/'COLLECTION.json').read_text())
        self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(),receipt['raw_archive_sha256'])
        with zipfile.ZipFile(raw) as z:
            self.assertIsNone(z.testzip())
            manifest=json.loads(z.read('evidence_manifest.json'))
            self.assertEqual(len(manifest),receipt['manifest_verified_files'])
            for name,v in manifest.items():
                data=z.read(name)
                self.assertEqual((len(data),hashlib.sha256(data).hexdigest()),(v['bytes'],v['sha256']),name)

    def test_all_native_errors_are_real_setup_events_not_stdout_matches(self):
        cases=list(ET.parse(RUN/'native_baseline/phase2.junit.xml').getroot().iter('testcase'))
        errors=[c.find('error') for c in cases if c.find('error') is not None]
        self.assertEqual((len(cases),len(errors)),(339,195))
        self.assertTrue(all(c.find('failure') is None for c in cases))
        self.assertEqual(sum("fixture 'httpbin'" in (e.text or '') for e in errors),191)
        self.assertEqual(sum("fixture 'httpbin_secure'" in (e.text or '') for e in errors),4)
        result=json.loads((RUN/'native_baseline/official_result.json').read_text())
        self.assertIs(result['resolved'],False)
        self.assertEqual(result['test_exit_code'],1)

    def test_native_command_retained_and_observer_not_in_scoring_command(self):
        current=json.loads((RUN/'native_baseline/phase2_command.json').read_text())['command']
        previous=json.loads((HERE.parents[1]/'results/cpu03/validation/requests_7433/phase2_command.json').read_text())['command']
        normalize=lambda s:re.sub(r'/tmp/_swegemma_junit_[a-f0-9]+\.xml','<RANDOM>',s)
        self.assertEqual(normalize(current),normalize(previous))
        self.assertNotIn('toy_provider',current)
        self.assertNotIn('_ure_fixture_observer',current)

    def test_absent_provider_is_independently_supported(self):
        d=RUN/'diagnostics'
        env=json.loads(json.loads((d/'environment.json').read_text())['stdout'])
        self.assertIsNone(env['versions']['pytest-httpbin'])
        self.assertIsNone(env['modules']['pytest_httpbin'])
        self.assertIsNone(env['environment']['PYTEST_DISABLE_PLUGIN_AUTOLOAD'])
        error=json.loads((d/'explicit_provider_import.json').read_text())
        self.assertIn("No module named 'pytest_httpbin'",error['stderr'])
        self.assertNotEqual(error['exit_code'],0)
        offline=json.loads((d/'offline_provider_resolution.json').read_text())
        self.assertIn('No matching distribution found for pytest-httpbin==2.1.0',offline['stderr'])
        self.assertNotEqual(offline['exit_code'],0)

    def test_native_junit_captured_before_cleanup_and_no_source_side_effects(self):
        capture=json.loads((RUN/'native_baseline/phase2_junit_capture.json').read_text())
        self.assertTrue(capture['sandbox_exists_at_capture'])
        self.assertEqual(capture['status'],'captured')
        self.assertEqual(hashlib.sha256((RUN/'native_baseline/phase2.junit.xml').read_bytes()).hexdigest(),capture['sha256'])
        self.assertEqual(json.loads((RUN/'cleanup.json').read_text()),dict(complete=True,remaining_directories=[]))
        records=[json.loads((RUN/p).read_text()) for p in ('before_native_files.json','after_native_files.json','after_diagnostics_files.json')]
        self.assertEqual(records[0],records[1]);self.assertEqual(records[1],records[2])

    def test_actual_linux_semantics_and_conservative_admission(self):
        result=assess(RUN)
        self.assertEqual(result['outcome'],'ENVIRONMENT_BLOCKED')
        self.assertTrue(result['root_cause_proven_in_research_environment'])
        self.assertFalse(result['official_fix_applied'])
        self.assertEqual(result['protocol_status'],'DRAFT_BASELINE_BLOCKED')
        for r in result['synthetic_cases']['cases']:
            self.assertEqual(r['pytest'],'8.4.2')
            self.assertTrue(r['expected_observed'])
            self.assertEqual(r['counts']['tests'],2)


if __name__=='__main__':unittest.main()
