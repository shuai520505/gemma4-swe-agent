import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import requests
from kagglesdk.kaggle_client import KaggleClient
from kagglesdk.kernels.types.kernels_api_service import ApiSaveKernelRequest
from u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02 import dispatch as d


def fixtures():
    h=hashlib.sha256(b'local mock Notebook').hexdigest()
    spec=dict(execution_id=d.EXECUTION_ID,slug=d.SLUG,max_dispatches=1,
        Notebook_sha256=h,wire_sha256=h,payload_sha256=h,selection_protocol_sha256=h,
        configuration=dict(GPU=False,TPU=False,internet=False,model_sources=[],Agent_runs=0,Gemma_calls=0,formal_submission=False),
        expected_candidates_in_order=['synthetic_test_only'],sdk_versions={'kagglesdk':'local installed'})
    auth=dict(execution_id=d.EXECUTION_ID,slug=d.SLUG,allow_new_CPU_only_save_and_run=True,
        max_SaveKernel_dispatches=1,acknowledges_CPU01_may_have_been_accepted=True,evidence_source='human_user_message',
        human_message_reference='LOCAL_FAULT_INJECTION_NOT_LIVE_AUTHORIZATION',
        **{k:spec[k] for k in ('Notebook_sha256','wire_sha256','payload_sha256','selection_protocol_sha256')})
    gates=dict(identity_confirmed=True,slug_conflict=False,current_readonly_GO=True,payload_integrity=True,source_commit='LOCAL_TEST_NOT_GPU_OR_KAGGLE_AUTHORIZATION')
    return spec,auth,gates


def submit():
    # Real installed SDK request serialization and response/error parsing.
    # Only the outermost requests transport is replaced; no network request.
    request=ApiSaveKernelRequest();request.slug=d.SLUG;request.new_title=d.SLUG.split('/')[1]
    request.text='local mock Notebook';request.enable_gpu=False;request.enable_tpu=False
    request.enable_internet=False;request.model_data_sources=[];request.language='python';request.kernel_type='notebook'
    with KaggleClient(api_token='LOCAL_FAKE_NOT_A_CREDENTIAL',verbose=False) as client:
        return client.kernels.kernels_api_client.save_kernel(request)


def response(status,body):
    r=requests.Response();r.status_code=status;r._content=body;r.headers['Content-Type']='application/json' if body.startswith(b'{') else 'text/plain'
    r.headers['X-Request-Id']='not-a-safe-id-DO-NOT-LOG';return r


class DispatchTests(unittest.TestCase):
    def perform(self,status=200,body=None,transport_error=None,write_failure=False,submit_fn=submit):
        body=body if body is not None else json.dumps(dict(ref=d.SLUG,versionNumber=1,kernelId=123)).encode()
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        path=Path(self.tmp.name)/'run';spec,auth,gates=fixtures();controller=d.Controller(path,spec);calls=[]
        real=d.exclusive
        def fail(p,data):
            if write_failure and Path(p).name=='HTTP_METADATA.json':raise OSError('local injected disk failure')
            return real(p,data)
        def transport(session,request,**kwargs):
            calls.append(1)
            self.assertFalse(kwargs['allow_redirects'])
            retry=session.get_adapter(request.url).max_retries
            self.assertTrue(all(getattr(retry,k)==0 for k in ('total','connect','read','status','redirect','other')))
            self.assertTrue((path/'dispatch.claim').is_file())
            self.assertIn('DISPATCH_STARTED',controller.journal.states())
            if transport_error:raise transport_error
            r=response(status,body)
            old=r.json
            def parse(*a,**kw):
                if not write_failure:self.assertTrue((path/'HTTP_METADATA.json').is_file())
                return old(*a,**kw)
            r.json=parse;return r
        result=None;error=None
        with patch.object(requests.Session,'send',transport),patch.object(d,'exclusive',fail):
            try:result=controller.execute(auth,gates,submit_fn)
            except BaseException as e:error=e
        self.assertEqual(len(calls),1)
        # Re-entry cannot make a second transport call or downgrade known state.
        known=list(controller.journal.states())
        with self.assertRaisesRegex(RuntimeError,'never resend'):
            controller.execute(auth,gates,lambda:self.fail('Second SDK submission'))
        if 'ACCEPTED_CONFIRMED' in known:self.assertEqual(controller.journal.states(),known)
        return path,controller,result,error

    def test_json_200_real_SDK_success_and_once_only(self):
        p,c,result,error=self.perform();self.assertIsNone(error);self.assertEqual(result.version_number,1)
        self.assertIn('ACCEPTED_CONFIRMED',c.journal.states())

    def test_non_json_502_metadata_survives(self):
        p,c,_,e=self.perform(502,b'<html>gateway</html>')
        self.assertIsInstance(e,requests.HTTPError);self.assertIn('UNKNOWN_STOP',c.journal.states())
        self.assertEqual(json.loads((p/'HTTP_METADATA.json').read_bytes())['HTTP_status'],502)
        self.assertFalse(json.loads((p/'HTTP_RECEIPT.json').read_bytes())['JSON_parsed'])

    def test_empty_204_preserves_real_SDK_error(self):
        p,c,_,e=self.perform(204,b'');self.assertIsNotNone(e)
        self.assertEqual(json.loads((p/'HTTP_METADATA.json').read_bytes())['HTTP_status'],204)
        self.assertIn('UNKNOWN_STOP',c.journal.states())

    def test_403_structured_rejection_never_retries(self):
        p,c,_,e=self.perform(403,b'{"error":{"code":403,"status":"PERMISSION_DENIED"}}')
        self.assertIsInstance(e,requests.HTTPError);self.assertIn('REJECTED_CONFIRMED',c.journal.states())

    def test_429_structured_rejection_never_retries(self):
        p,c,_,e=self.perform(429,b'{"error":{"code":429,"status":"RESOURCE_EXHAUSTED"}}')
        self.assertIsInstance(e,requests.HTTPError);self.assertIn('REJECTED_CONFIRMED',c.journal.states())

    def test_timeout_preserves_exception_identity(self):
        err=requests.Timeout('synthetic timeout');p,c,_,e=self.perform(transport_error=err)
        self.assertIs(e,err);self.assertIn('UNKNOWN_STOP',c.journal.states());self.assertFalse((p/'HTTP_RECEIPT.json').exists())

    def test_connection_interrupt_preserves_exception_identity(self):
        err=requests.ConnectionError('synthetic disconnect');p,c,_,e=self.perform(transport_error=err)
        self.assertIs(e,err);self.assertIn('UNKNOWN_STOP',c.journal.states())

    def test_observer_disk_failure_does_not_replace_SDK_success(self):
        p,c,result,e=self.perform(write_failure=True)
        self.assertIsNone(e);self.assertEqual(result.version_number,1);self.assertIn('UNKNOWN_STOP',c.journal.states())
        self.assertFalse((p/'HTTP_METADATA.json').exists())

    def test_second_SDK_send_is_blocked_before_transport(self):
        def twice():submit();return submit()
        _,c,_,e=self.perform(submit_fn=twice)
        self.assertIsInstance(e,RuntimeError);self.assertIn('Second HTTP dispatch',str(e))

    def test_secrets_and_arbitrary_headers_not_recorded(self):
        payload=json.dumps(dict(ref=d.SLUG,versionNumber=1,kernelId=123,token='NEVER_LOG_TEST_SECRET',errorDetails='NEVER_LOG_TEST_SECRET')).encode()
        p,_,_,_=self.perform(body=payload)
        all_text=''.join(x.read_text() for x in p.rglob('*') if x.is_file())
        self.assertNotIn('NEVER_LOG_TEST_SECRET',all_text);self.assertNotIn('not-a-safe-id',all_text)

    def test_unexpected_version_preserves_known_acceptance_but_not_new_resource_gate(self):
        body=json.dumps(dict(ref=d.SLUG,versionNumber=2,kernelId=123)).encode()
        p,c,result,e=self.perform(body=body)
        self.assertIsNone(e);self.assertEqual(result.version_number,2)
        accepted=[json.loads(x.read_bytes()) for x in (p/'events').glob('*ACCEPTED_CONFIRMED.json')]
        self.assertEqual(len(accepted),1);self.assertFalse(accepted[0]['expected_new_version'])

    def test_torn_dispatch_claim_never_authorizes_another_send(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'dispatch.claim').write_bytes(b'{incomplete')
            s,a,g=fixtures();c=d.Controller(p,s)
            with self.assertRaisesRegex(RuntimeError,'never resend'):c.execute(a,g,lambda:self.fail('Torn-claim replay'))
            self.assertEqual((p/'dispatch.claim').read_bytes(),b'{incomplete')

    def test_missing_authorization_prevents_even_sdk_call(self):
        with tempfile.TemporaryDirectory() as t:
            spec,_,g=fixtures();c=d.Controller(Path(t)/'run',spec)
            with self.assertRaises(PermissionError):c.execute(None,g,lambda:self.fail('Unauthorized SDK call'))
            self.assertFalse(c.path.exists())

    def test_wrong_or_existing_slug_prevents_submission(self):
        with tempfile.TemporaryDirectory() as t:
            s,a,g=fixtures();s['slug']=s['slug'].replace('cpu02','cpu01')
            with self.assertRaises(AssertionError):d.Controller(Path(t)/'run',s).execute(a,g,lambda:self.fail('Wrong slug'))
            s,a,g=fixtures();g['slug_conflict']=True
            with self.assertRaises(AssertionError):d.Controller(Path(t)/'run',s).execute(a,g,lambda:self.fail('Existing slug'))

    def test_GPU_TPU_or_model_input_prevents_submission(self):
        with tempfile.TemporaryDirectory() as t:
            for k,v in [('GPU',True),('TPU',True),('model_sources',['forbidden']),('internet',True)]:
                s,a,g=fixtures();s['configuration'][k]=v
                with self.assertRaises(AssertionError):d.Controller(Path(t)/k,s).execute(a,g,lambda:self.fail('Non-CPU request'))

    def test_crash_after_dispatch_before_receipt_and_restart(self):
        with tempfile.TemporaryDirectory() as t:
            program='''
import os,sys,requests
from pathlib import Path
from u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02.tests.test_dispatch import fixtures,submit
from u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02.dispatch import Controller
s,a,g=fixtures()
requests.Session.send=lambda *args,**kw:os._exit(73)
Controller(Path(sys.argv[1]),s).execute(a,g,submit)
'''
            path=Path(t)/'run';r=subprocess.run([sys.executable,'-c',program,str(path)],capture_output=True)
            self.assertEqual(r.returncode,73);self.assertTrue((path/'dispatch.claim').is_file())
            self.assertFalse((path/'HTTP_METADATA.json').exists())
            s,a,g=fixtures();c=d.Controller(path,s)
            with self.assertRaisesRegex(RuntimeError,'never resend'):c.execute(a,g,lambda:self.fail('Crash resend'))
            self.assertIn('UNKNOWN_STOP',c.journal.states())


if __name__=='__main__':unittest.main()
