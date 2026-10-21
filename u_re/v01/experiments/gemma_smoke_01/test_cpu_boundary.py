"""Installed SDK serialization, mocked outer requests transport. No live API."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import requests
from kagglesdk.kaggle_client import KaggleClient
from kagglesdk.kernels.types.kernels_api_service import ApiSaveKernelRequest
from . import cpu_notebook as c

def submit():
    q=ApiSaveKernelRequest();q.slug=c.SLUG;q.new_title=c.SLUG.split('/')[1]
    q.text='synthetic notebook';q.enable_gpu=False;q.enable_tpu=False;q.enable_internet=False
    q.model_data_sources=[];q.language='python';q.kernel_type='notebook'
    with KaggleClient(api_token='LOCAL_FAKE_NOT_A_CREDENTIAL',verbose=False) as client:
        return client.kernels.kernels_api_client.save_kernel(q)

class CPUBoundaryTests(unittest.TestCase):
    def case(self,status=200,body=None,grant=True):
        d=c.controller_module();temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        h=c.sha(b'synthetic notebook')
        spec=dict(execution_id=c.EXECUTION_ID,slug=c.SLUG,max_dispatches=1,Notebook_sha256=h,wire_sha256=h,
            payload_sha256=h,selection_protocol_sha256=h,configuration=dict(GPU=False,TPU=False,internet=False,
                model_sources=[],Agent_runs=6,Gemma_calls=0,formal_submission=False),
            expected_candidates_in_order=['synthetic'],sdk_versions={})
        a=dict(execution_id=c.EXECUTION_ID,slug=c.SLUG,max_SaveKernel_dispatches=1,human_message_reference='LOCAL_TEST_ONLY',
            **{k:spec[k] for k in ('Notebook_sha256','wire_sha256','payload_sha256')}) if grant else None
        calls=[]
        def transport(session,request,**kw):
            calls.append(1);r=requests.Response();r.status_code=status
            r.headers['Content-Type']='application/json' if status==200 else 'text/html'
            r._content=body if body is not None else json.dumps(dict(ref=c.SLUG,kernelId=123,versionNumber=1)).encode()
            r.request=request;return r
        controller=d.Controller(Path(temp.name),spec)
        gates=dict(identity_confirmed=True,slug_conflict=False,current_readonly_GO=True,payload_integrity=True,source_commit='LOCAL_TEST')
        return controller,a,gates,calls,transport
    def test_accepted_sdk_one_send_and_reentry_block(self):
        x,a,g,calls,f=self.case()
        with patch('requests.Session.send',f):
            x.execute(a,g,submit)
            with self.assertRaises(RuntimeError):x.execute(a,g,submit)
        self.assertEqual(len(calls),1);self.assertIn('ACCEPTED_CONFIRMED',x.journal.states())
    def test_unauthorized_zero_send(self):
        x,a,g,calls,f=self.case(grant=False)
        with patch('requests.Session.send',f),self.assertRaises(PermissionError):x.execute(a,g,submit)
        self.assertEqual(calls,[])
    def test_non_json_failure_is_unknown_and_not_retried(self):
        x,a,g,calls,f=self.case(status=502,body=b'bad gateway')
        with patch('requests.Session.send',f):
            try:x.execute(a,g,submit)
            except Exception:pass
        self.assertEqual(len(calls),1);self.assertIn('UNKNOWN_STOP',x.journal.states())
        meta=json.loads((x.path/'HTTP_METADATA.json').read_text(encoding='utf-8'));self.assertEqual(meta['HTTP_status'],502)
    def test_receipt_slug_mismatch_unknown(self):
        x,a,g,calls,f=self.case(body=b'{"ref":"other/wrong","kernelId":123,"versionNumber":1}')
        with patch('requests.Session.send',f):x.execute(a,g,submit)
        self.assertEqual(len(calls),1);self.assertIn('UNKNOWN_STOP',x.journal.states())
    def test_gpu_configuration_refused(self):
        x,a,g,calls,f=self.case();x.spec['configuration']['GPU']=True
        with patch('requests.Session.send',f),self.assertRaises(AssertionError):x.execute(a,g,submit)
        self.assertEqual(calls,[])

if __name__=='__main__':unittest.main(verbosity=2)
