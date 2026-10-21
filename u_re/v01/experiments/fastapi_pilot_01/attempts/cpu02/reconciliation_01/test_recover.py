import json
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import zipfile
from unittest.mock import patch

import requests
from . import recover as r


def resource():
    meta = dict(id=r.ID,ref=r.REF,author=r.OWNER,slug=r.SLUG,is_private=True,
                current_version_number=1,language='python',kernel_type='notebook',
                enable_gpu=False,enable_tpu=False,enable_internet=False,model_data_sources=[])
    return SimpleNamespace(metadata=SimpleNamespace(**{'_'+k:v for k,v in meta.items()}),
        blob=SimpleNamespace(source=(r.CPU02/'notebook/study.ipynb').read_text()))


class ReadonlyRecoveryTests(unittest.TestCase):
    def test_mutations_and_unknown_operations_denied_before_transport(self):
        for op in ('SaveKernel','CreateKernelSession','RunKernel','RestartKernel','DeleteKernel','SubmitKernel','Unknown'):
            with self.subTest(op=op),tempfile.TemporaryDirectory() as folder:
                with patch.object(requests.Session,'send',side_effect=AssertionError('TRANSPORT_FORBIDDEN')) as transport:
                    with r.ReadGuard(Path(folder)):
                        with self.assertRaises(PermissionError):
                            requests.post('https://api.kaggle.com/v1/kernels.KernelsApiService/'+op,json={})
                    transport.assert_not_called()

    def test_wrong_owner_slug_version_host_and_service_denied(self):
        base='https://api.kaggle.com/v1/kernels.KernelsApiService/GetKernel'
        body=dict(userName=r.OWNER,kernelSlug=r.SLUG,versionLabel='1')
        self.assertTrue(r.allowed_api('POST',base,body))
        for key,value in [('userName','other'),('kernelSlug','cpu03'),('versionLabel','2')]:
            self.assertFalse(r.allowed_api('POST',base,dict(body,**{key:value})))
        self.assertFalse(r.allowed_api('GET',base,body))
        self.assertFalse(r.allowed_api('POST',base.replace('api.kaggle.com','example.com'),body))
        self.assertFalse(r.allowed_api('POST',base.replace('KernelsApiService','OtherService'),body))

    def test_metadata_survives_non_JSON_403_without_body_or_secret(self):
        with tempfile.TemporaryDirectory() as folder:
            response=requests.Response();response.status_code=403;response._content=b'SECRET_NOT_JSON'
            with patch.object(requests.Session,'send',return_value=response) as transport:
                with r.ReadGuard(Path(folder)):
                    result=requests.post('https://api.kaggle.com/v1/kernels.KernelsApiService/GetKernel',
                        json=dict(userName=r.OWNER,kernelSlug=r.SLUG,versionLabel='1'))
                    self.assertEqual(result.status_code,403)
                self.assertEqual(transport.call_count,1)
            raw=(Path(folder)/'HTTP/001.json').read_text()
            self.assertNotIn('SECRET',raw);self.assertEqual(json.loads(raw)['HTTP_status'],403)

    def test_exact_and_semantic_source_identity(self):
        v=resource();a=r.identity(v)
        self.assertEqual(a['state'],'IDENTITY_CONFIRMED')
        self.assertTrue(a['source']['payload_match'])
        v.blob.source=json.dumps(json.loads(v.blob.source),sort_keys=True)
        a=r.identity(v);self.assertEqual(a['state'],'IDENTITY_CONFIRMED')
        self.assertFalse(a['source']['exact_file_match']);self.assertFalse(a['source']['exact_wire_match'])
        self.assertTrue(a['source']['semantic_JSON_match'])

    def test_short_ref_preserved_and_cross_checked_with_owner_ID_source(self):
        v=resource();v.metadata._ref=r.SLUG
        a=r.identity(v);self.assertEqual(a['state'],'IDENTITY_CONFIRMED')
        self.assertEqual(a['metadata']['ref'],r.SLUG)
        self.assertEqual(a['canonical_ref_for_comparison'],r.REF)
        v.metadata._author='other';self.assertNotEqual(r.identity(v)['state'],'IDENTITY_CONFIRMED')

    def test_wrong_ID_or_resource_stops(self):
        v=resource();v.metadata._id=123
        self.assertEqual(r.identity(v)['state'],'IDENTITY_MISMATCH')
        v=resource();v.metadata._ref='other/Notebook'
        self.assertEqual(r.identity(v)['state'],'IDENTITY_MISMATCH')

    def test_missing_fields_or_changed_content_not_confirmed(self):
        v=resource();v.metadata._enable_gpu=None
        self.assertEqual(r.identity(v)['state'],'RESOURCE_FOUND_IDENTITY_PARTIAL')

    def test_display_name_does_not_override_exact_resource_owner(self):
        v=resource();v.metadata._author='The 13th Seat of The Genius Club'
        a=r.identity(v)
        self.assertEqual(a['state'],'IDENTITY_CONFIRMED')
        self.assertEqual(a['owner_from_full_ref'],r.OWNER)
        self.assertEqual(a['metadata']['author'],'The 13th Seat of The Genius Club')
        v.metadata._ref='someoneelse/'+r.SLUG
        self.assertEqual(r.identity(v)['state'],'IDENTITY_MISMATCH')
        v=resource();v.blob.source='{}'
        self.assertEqual(r.identity(v)['state'],'RESOURCE_FOUND_IDENTITY_PARTIAL')

    def test_unknown_download_and_disabled_download_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(requests.Session,'send',side_effect=AssertionError('TRANSPORT_FORBIDDEN')) as transport:
                with r.ReadGuard(Path(folder)) as guard:
                    guard.urls.add('https://storage.googleapis.com/example')
                    with self.assertRaises(PermissionError):requests.get('https://storage.googleapis.com/example')
                transport.assert_not_called()

    def test_newer_latest_does_not_satisfy_version_gate(self):
        v=resource();v.metadata._current_version_number=2
        self.assertEqual(r.identity(v)['state'],'RESOURCE_FOUND_IDENTITY_PARTIAL')

    def test_request_cap_blocks_before_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(requests.Session,'send',side_effect=AssertionError('TRANSPORT_FORBIDDEN')) as transport:
                with r.ReadGuard(Path(folder),maximum=0):
                    with self.assertRaisesRegex(RuntimeError,'cap reached'):
                        requests.post('https://api.kaggle.com/v1/kernels.KernelsApiService/GetKernel',
                            json=dict(userName=r.OWNER,kernelSlug=r.SLUG,versionLabel='1'))
                transport.assert_not_called()

    def test_real_evidence_directory_prevents_reentrant_live_queries(self):
        self.assertTrue((r.HERE/'evidence').is_dir())
        with patch.object(requests.Session,'send',side_effect=AssertionError('TRANSPORT_FORBIDDEN')) as transport:
            with self.assertRaises(FileExistsError):r.run()
            transport.assert_not_called()

    def test_archive_manifest_tampering_rejected(self):
        from .audit import validate_archive
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z:
            z.writestr('cpu.log',b'actual')
            z.writestr('evidence_manifest.json',json.dumps({'cpu.log':dict(bytes=6,sha256='0'*64)}))
        with zipfile.ZipFile(raw) as z:
            with self.assertRaises(AssertionError):validate_archive(z)

    def test_archive_unsafe_paths_rejected(self):
        from .audit import validate_archive
        for name in ('../escape','/absolute','C:/escape','folder\\escape'):
            with self.subTest(path=name):
                raw=io.BytesIO()
                with zipfile.ZipFile(raw,'w') as z:
                    z.writestr(name,b'bad');z.writestr('evidence_manifest.json','{}')
                with zipfile.ZipFile(raw) as z:
                    with self.assertRaises(AssertionError):validate_archive(z)


if __name__=='__main__':unittest.main()
