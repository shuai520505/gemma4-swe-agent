"""Actual recorded evidence checks. These are not service startup acceptance tests."""
import unittest
from pathlib import Path
from forensic import autopsy,R

class FixtureEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=autopsy()
 def test_all_183_http_errors_have_exact_provider_resolution_trace(self):
  self.assertEqual(self.r['groups']['HTTPBIN_PROVIDER_UNRESOLVED'],183)
 def test_all_four_https_errors_have_separate_provider_resolution_trace(self):
  self.assertEqual(self.r['groups']['HTTPBIN_SECURE_PROVIDER_UNRESOLVED'],4)
 def test_missing_provider_is_not_claimed_installed(self):
  self.assertFalse(self.r['wheels']['provider_in_approved_wheels']);self.assertEqual(self.r['version']['actual_installed_version'],'UNKNOWN_NOT_DIRECTLY_PROBED')
 def test_http_startup_has_not_been_misreported(self):self.assertEqual(self.r['not_executed']['HTTP_startup'],'NOT_RUN')
 def test_https_tls_startup_has_not_been_misreported(self):self.assertEqual(self.r['not_executed']['TLS_handshake'],'NOT_RUN')
 def test_fixture_teardown_unknown_but_sandbox_cleanup_confirmed(self):
  self.assertEqual(self.r['cleanup']['fixture_teardown'],'NOT_RUN');self.assertTrue(self.r['cleanup']['Agent']);self.assertTrue(self.r['cleanup']['Native'])
 def test_port_conflict_unobserved_not_invented_root_cause(self):
  self.assertEqual(self.r['not_executed']['port_conflict'],'NOT_RUN');self.assertFalse(any('Address already in use' in x['trace_excerpt'] for x in self.r['records']))
 def test_proxy_variables_are_not_inherited_from_host(self):self.assertEqual(self.r['environment']['proxy_keys'],[])
 def test_agent_native_use_same_approved_wheels_and_binding(self):
  self.assertTrue(self.r['wheels']['Agent_Native_identical']);self.assertIn('/workspace/src:/workspace:/opt/approved',self.r['source_binding']['Native_command']);self.assertIn('/workspace/src/requests/__init__.py',self.r['source_binding']['Agent']['result']['stdout'])
 def test_abnormal_fixture_process_recovery_is_not_claimed(self):self.assertEqual(self.r['not_executed']['fixture_crash_recovery'],'NOT_RUN')
 def test_all_four_ordinary_failure_tags_are_actually_network_confinement(self):self.assertEqual(self.r['groups']['NETWORK_CONFINEMENT_EACCES'],4)
 def test_native_source_state_unchanged_during_verification(self):self.assertTrue(self.r['source_binding']['guard']['unchanged'])
 def test_original_native_hash_matches_both_receipts(self):
  for name in ['native_hash_matches_receipts','session_hash_matches_done','cleanup_hash_matches_done','archive_matches_extracted_evidence']:self.assertTrue(self.r[name],name)
if __name__=='__main__':unittest.main()
