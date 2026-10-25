"""Offline controller tests. No Kaggle HTTP request or Gemma execution."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import requests
from . import cli_control as c

def authorized(batch,spec):
    d,slug,eid=c.location(batch)
    grant=json.loads((d/'RUNTIME_AUTHORIZATION.json').read_bytes())
    return dict(grant,execution_id=eid,slug=slug,model_source='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',
                **{k:spec[k] for k in ['Notebook_sha256','wire_sha256','payload_sha256']})

class CLIOperatorTests(unittest.TestCase):
    def test_frozen_batch_bindings(self):
        for batch,order in [(1,list('ABC')),(2,list('CBA'))]:
            spec=c.validate(batch);self.assertEqual(spec['expected_candidates_in_order'],order)
            c.controller(batch).checked_authorization(authorized(batch,spec),spec)
    def test_expanded_session_budget_rejected(self):
        spec=c.validate(1);g=authorized(1,spec);g['max_Agent_runs']=4
        with self.assertRaises(AssertionError):c.controller(1).checked_authorization(g,spec)
    def test_same_payload_tamper_fails_before_dispatch(self):
        spec=c.validate(1);spec['configuration']['Agent_runs']=4
        with self.assertRaises(AssertionError):c.controller(1).checked_config(spec)
    def test_inherited_single_dispatch_and_no_retry(self):
        spec=c.validate(1);grant=authorized(1,spec);module=c.controller(1)
        nb=json.loads((c.location(1)[0]/'notebook/study.ipynb').read_bytes())
        body=dict(slug=spec['slug'],enableGpu=True,enableTpu=False,enableInternet=False,
             modelDataSources=[grant['model_source']],machineShape='NvidiaL4',sessionTimeoutSeconds=10000,text=json.dumps(nb))
        request=requests.Request('POST','https://api.kaggle.com/v1/kernels.KernelsApiService/SaveKernel',data=json.dumps(body)).prepare()
        sent=[]
        def transport(session,request,**kw):
            sent.append(request);self.assertFalse(kw['allow_redirects'])
            self.assertEqual(session.get_adapter(request.url).max_retries.total,0)
            response=requests.Response();response.status_code=200;response._content=b'{}';response.headers['Content-Type']='application/json';return response
        with tempfile.TemporaryDirectory() as tmp:
            controller=module.Controller(Path(tmp),spec)
            gates=dict(identity_confirmed=True,slug_conflict=False,current_readonly_GO=True,payload_integrity=True,source_commit='OFFLINE_UNIT_TEST_ONLY')
            with patch.object(requests.Session,'send',transport):
                controller.execute(grant,gates,lambda:requests.Session().send(request))
                with self.assertRaises(RuntimeError):controller.execute(grant,gates,lambda:self.fail('Second SDK dispatch'))
            self.assertEqual(len(sent),1)
            self.assertTrue((Path(tmp)/'dispatch.claim').exists())
            self.assertTrue((Path(tmp)/'HTTP_METADATA.json').exists())

if __name__=='__main__':unittest.main(verbosity=2)
