import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import requests

from u_re.v01.experiments.fastapi_pilot_01.register import HERE,ROOT,PREVIOUS
from u_re.v01.experiments.fastapi_pilot_01.response_observer import describe_response,capture_response


class ReadinessTests(unittest.TestCase):
    def response(self,status,body,kind):
        r=requests.Response();r.status_code=status;r._content=body;r.headers['Content-Type']=kind
        return r

    def test_non_json_and_empty_response_preserve_actual_status(self):
        for status,body in [(502,b'<html>gateway error</html>'),(204,b'')]:
            r=self.response(status,body,'text/html')
            d=describe_response(r)
            self.assertEqual(d['http_status'],status);self.assertFalse(d['json_response'])
            self.assertEqual(d['response_bytes'],len(body));self.assertNotIn('response',d)

    def test_json_receipt_does_not_copy_secret_fields(self):
        r=self.response(200,b'{"versionNumber":1,"kernelId":123,"token":"synthetic-secret","cookie":"synthetic-cookie"}','application/json')
        d=describe_response(r)
        self.assertTrue(d['json_response']);self.assertEqual(d['versionNumber'],1)
        self.assertNotIn('synthetic-secret',json.dumps(d));self.assertNotIn('synthetic-cookie',json.dumps(d))

    def test_recorder_file_error_does_not_mask_sdk_response(self):
        r=self.response(502,b'not json','text/plain')
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'receipt.json'
            self.assertTrue(capture_response(p,r));first=p.read_bytes()
            self.assertFalse(capture_response(p,r));self.assertEqual(p.read_bytes(),first)
        self.assertEqual(r.status_code,502)

    def test_existing_attempt_refuses_save_before_api_mutation(self):
        # A fake import checks only the host refusal, not official API compatibility.
        from u_re.v01.experiments.fastapi_pilot_01 import cpu_host
        with patch.dict(sys.modules,{'kaggle':SimpleNamespace(api=object())}):
            with self.assertRaisesRegex(AssertionError,'Never repeat a save'):
                cpu_host.launch()

    def test_unconfirmed_save_is_not_fabricated_native_outcome(self):
        data=json.loads((HERE/'TASK_SCREENING_LEDGER.json').read_bytes())
        self.assertEqual(data['confirmed_cpu_checks'],0);self.assertIsNone(data['actual_platform_cpu_checks'])
        self.assertEqual(data['SaveKernel_dispatches'],1);self.assertEqual(data['SaveKernel_retries'],0)
        self.assertIsNone(data['accepted_Notebook_version']);self.assertEqual(data['selected'],[])
        self.assertEqual(len(data['rows']),50)
        for r in data['rows']:
            self.assertEqual(r['status'],'NOT_RUN');self.assertIsNone(r['cpu_entered'])
            for k in ('passed','failed','errors','native_exit_code','baseline_resolved','environment_admitted','seconds','JUnit_sha256'):
                self.assertIsNone(r[k])

    def test_auth_success_does_not_promote_cpu_or_gpu(self):
        auth=json.loads((HERE/'AUTH_STATUS.json').read_bytes())
        self.assertEqual(auth['status'],'AUTH_READONLY_GO');self.assertTrue(auth['identity_confirmed'])
        self.assertFalse(auth['credential_files_changed']);self.assertEqual(auth['SaveKernel_requests'],0)
        draft=json.loads((HERE/'GPU_EXECUTION_DRAFT.json').read_bytes())
        for n in ('execute','gpu_authorized','formal_submission','gpu_algorithm_validated','resource_admission','GPU_Notebook_generated','GPU_Notebook_saved'):
            self.assertIs(draft[n],False)
        self.assertEqual(draft['selected_tasks'],[])

    def test_precommitted_selection_and_historical_bytes_unchanged(self):
        commit='77ad02301c5c3b490d8f28fc3c397a5531854618'
        for n in ('screen.py','SELECTION_PROTOCOL.json','EXCLUSION_LEDGER_V02.json','RANKED_POOL.json','TASK_POOL_METADATA.json'):
            raw=subprocess.check_output(['git','show',commit+':'+(HERE/n).relative_to(ROOT).as_posix()],cwd=ROOT)
            self.assertEqual(raw,(HERE/n).read_bytes())
        before=json.loads((HERE/'evidence/INITIAL_HISTORY.json').read_bytes())
        self.assertEqual(len(before),5747)
        for n,h in before.items():self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),h,n)
        self.assertEqual(json.loads((PREVIOUS/'TASK_SCREENING_LEDGER.json').read_bytes())['status'],'TASK_ADMISSION_BLOCKED')

    def test_frozen_notebook_and_actual_serialized_request_match(self):
        build=json.loads((HERE/'registrations/cpu01_build.json').read_bytes())
        raw=(HERE/'notebooks/cpu01/study.ipynb').read_bytes();nb=json.loads(raw)
        request=json.loads((HERE/'results/cpu01/SAVE_REQUEST.json').read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(),build['notebook_sha256'])
        self.assertEqual(hashlib.sha256(json.dumps(nb).encode()).hexdigest(),request['notebook_text_sha256'])
        self.assertIs(request['metadata']['enableGpu'],False);self.assertIs(request['metadata']['enableTpu'],False)
        self.assertNotIn('modelDataSources',request['metadata'])


if __name__=='__main__':unittest.main()
