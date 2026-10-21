import unittest
from pathlib import Path
from types import SimpleNamespace
from u_re.v01.experiments.fastapi_pilot_01.reconciliation_01.query import allowed_request,metadata


class GuardTests(unittest.TestCase):
    def test_resource_mutations_rejected(self):
        for name in ('SaveKernel','CreateKernelSession','CancelKernelSession','DeleteKernel','GenerateAccessToken','ExpireApiToken'):
            self.assertFalse(allowed_request('POST','https://api.kaggle.com/v1/'+name))

    def test_only_reviewed_read_endpoints_allowed(self):
        for name in ('IntrospectToken','ListKernels','GetKernel','GetKernelSessionStatus','ListKernelSessionOutput'):
            self.assertTrue(allowed_request('POST','https://api.kaggle.com/v1/'+name))
        self.assertFalse(allowed_request('GET','https://api.kaggle.com/v1/GetKernel'))
        self.assertFalse(allowed_request('POST','https://other.example/v1/GetKernel'))

    def test_unknown_fields_do_not_default_to_false_or_zero(self):
        d=metadata(SimpleNamespace(_ref='owner/slug',_is_private=None,_current_version_number=None))
        self.assertIsNone(d['is_private']);self.assertIsNone(d['current_version_number'])
        self.assertNotIn('source',d)


if __name__=='__main__':unittest.main()
