import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import requests
from .admission import normalize,run as reconcile,PRIOR,HERE,ROOT,sha
from .GPU_NOTEBOOK import controller_module,SLUG


class Admission(unittest.TestCase):
    def setUp(self):
        self.ledger=json.loads((PRIOR/'TASK_ADMISSION_LEDGER.json').read_bytes())
        self.selected=json.loads((PRIOR/'SELECTED_TASKS.json').read_bytes())
        self.archive=ROOT.parent/'private-evidence/u_re_integrated_screen01/read-02/evidence_confirmed/output/u_re_integrated_screen01.zip'
    def test_native_bytes_accept_exact_two(self):
        with zipfile.ZipFile(self.archive) as z:r=normalize(self.ledger,self.selected,z.read)
        self.assertEqual([r['admission'] for r in r['tasks']],['BASELINE_ELIGIBLE']*2)
        self.assertTrue(all(r['baseline']=='EXECUTED' for r in r['tasks']))
    def test_manual_eligible_flag_does_not_bypass_identity(self):
        self.selected['tasks'][0]['base_commit']='tampered'
        with zipfile.ZipFile(self.archive) as z,self.assertRaises(AssertionError):normalize(self.ledger,self.selected,z.read)
    def test_tampered_native_output_rejected(self):
        with zipfile.ZipFile(self.archive) as z,self.assertRaises(AssertionError):
            normalize(self.ledger,self.selected,lambda n:z.read(n)+b' ' if n.endswith('official_result.json') else z.read(n))


class Dispatch(unittest.TestCase):
    def case(self,*,grant=True,body_change=None,reply=None):
        m=controller_module();spec=json.loads((HERE/'BUILD.json').read_bytes())
        value=json.loads((HERE/'GPU_AUTHORIZATION.json').read_bytes())
        value.update({k:spec[k] for k in ('Notebook_sha256','wire_sha256','payload_sha256')})
        if not grant:value=None
        nb=json.loads((HERE/'notebook/study.ipynb').read_bytes())
        body=dict(slug=SLUG,enableGpu=True,enableTpu=False,enableInternet=False,modelDataSources=[m.MODEL_SOURCE],machineShape='NvidiaL4',sessionTimeoutSeconds=10000,text=json.dumps(nb))
        if body_change:body.update(body_change)
        self.calls=0
        def send(session,request,**kw):
            self.calls+=1
            self.assertEqual(kw['allow_redirects'],False)
            retry=session.get_adapter(request.url).max_retries
            self.assertEqual(retry.total,0)
            r=requests.Response();r.status_code=200;r.headers['Content-Type']='application/json';r._content=json.dumps(reply or dict(kernelId=123,versionNumber=1,ref=SLUG)).encode();return r
        root=tempfile.TemporaryDirectory();self.addCleanup(root.cleanup)
        controller=m.Controller(Path(root.name),spec)
        gates=dict(identity_confirmed=True,slug_conflict=False,current_readonly_GO=True,payload_integrity=True,source_commit='test')
        def sdk():
            requests.Session().post('https://api.kaggle.com/v1/kernels.KernelsApiService/SaveKernel',json=body)
            return SimpleNamespace(kernel_id=123,version_number=1,ref=(reply or {}).get('ref',SLUG))
        def invoke():
            with patch('requests.Session.send',send):return controller.execute(value,gates,sdk)
        return controller,invoke
    def test_one_dispatch_no_retry_reentry(self):
        c,send=self.case();send();self.assertEqual(self.calls,1)
        with self.assertRaises(RuntimeError):send()
        self.assertEqual(self.calls,1)
    def test_ungranted_never_dispatches(self):
        c,send=self.case(grant=False)
        with self.assertRaises(AssertionError):send()
        self.assertEqual(self.calls,0)
    def test_bad_wire_stops_before_claim(self):
        c,send=self.case(body_change=dict(text='changed'))
        with self.assertRaises(AssertionError):send()
        self.assertEqual(self.calls,0)
        self.assertFalse((c.path/'dispatch.claim').exists())
    def test_wrong_device_stops_before_network(self):
        c,send=self.case(body_change=dict(machineShape='NvidiaTeslaP100'))
        with self.assertRaises(AssertionError):send()
        self.assertEqual(self.calls,0)
    def test_unknown_ref_preserved_never_resaves(self):
        c,send=self.case(reply=dict(kernelId=123,versionNumber=1,ref='https://www.kaggle.com/code/'+SLUG));send()
        self.assertIn('UNKNOWN_STOP',c.journal.states())
        with self.assertRaises(RuntimeError):send()
        self.assertEqual(self.calls,1)


class Build(unittest.TestCase):
    def test_payload_no_scripted_model_and_frozen_sources(self):
        import ast,base64
        nb=json.loads((HERE/'notebook/study.ipynb').read_bytes())
        line=next(l for l in nb['cells'][0]['source'].splitlines() if l.startswith("payload=__import__('base64').b64decode("))
        payload=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            self.assertIsNone(z.testzip())
            self.assertFalse(any(n.endswith(('taskruntime_probe.py','runner_cases.py','cpu_interfaces.py')) for n in z.namelist()))
            self.assertEqual(z.read('u_re/v01/experiments/action_priority_01/integrated_cpu_01/agent_phase.py'),(PRIOR/'agent_phase.py').read_bytes())
            for arm,name in (('A','u_re/v01/submission_noegv.zip'),('B','u_re/v01/experiments/action_priority_01/submission_action_v01.zip')):
                lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes());self.assertEqual(sha(z.read(name)),lock['arms'][arm]['ZIP_sha256'])


if __name__=='__main__':unittest.main()
