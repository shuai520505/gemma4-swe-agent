from pathlib import Path
import tempfile
import unittest
from s1.infrastructure_recovery.build_dependencies import select


class OfflineAdmissionTests(unittest.TestCase):
    def test_version_constraint_is_preserved_when_newer_wheel_is_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('provider-1.4-py3-none-any.whl','provider-2.0-py3-none-any.whl'):(Path(tmp)/name).touch()
            self.assertEqual(select('provider>=1,<2',tmp).name,'provider-1.4-py3-none-any.whl')

    def test_missing_provider_fails_instead_of_falling_back_to_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):select('missing_provider==2.1',tmp)

    def test_direct_url_is_not_a_cache_requirement(self):
        with self.assertRaises(ValueError):select('provider @ https://example.invalid/provider.whl',Path('.'))
