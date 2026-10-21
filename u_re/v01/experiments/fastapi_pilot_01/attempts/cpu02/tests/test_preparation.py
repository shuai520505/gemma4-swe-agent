import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile

from u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02.prepare import HERE,PILOT,ROOT
from u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02.launch import validate_local,request_for_build


class PreparationTests(unittest.TestCase):
    def test_payload_and_screening_protocol_are_identical(self):
        spec=validate_local();nb=json.loads((HERE/'notebook/study.ipynb').read_bytes())
        line=next(l for l in nb['cells'][0]['source'].splitlines() if l.startswith("payload=__import__('base64').b64decode("))
        payload=base64.b64decode(ast.literal_eval(line[len("payload=__import__('base64').b64decode("):-1]))
        self.assertEqual(hashlib.sha256(payload).hexdigest(),spec['payload_sha256'])
        old=json.loads((PILOT/'registrations/cpu01_build.json').read_bytes())
        self.assertEqual(spec['payload_sha256'],old['payload_sha256'])
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            self.assertIsNone(z.testzip())
            for n in ('screen.py','SELECTION_PROTOCOL.json','RANKED_POOL.json','EXCLUSION_LEDGER_V02.json'):
                self.assertEqual(z.read((PILOT/n).relative_to(ROOT).as_posix()),(PILOT/n).read_bytes())
        self.assertIn("/'cpu02'/",nb['cells'][0]['source'])
        self.assertNotIn("/'cpu01'/",nb['cells'][0]['source'])

    def test_real_SDK_request_is_CPU_only_and_wire_bound(self):
        req=request_for_build();body=type(req).to_dict(req);spec=validate_local()
        self.assertEqual(body['slug'],spec['slug'])
        self.assertIs(body['enableGpu'],False);self.assertIs(body['enableTpu'],False);self.assertIs(body['enableInternet'],False)
        self.assertFalse(body.get('modelDataSources'));self.assertFalse(body.get('machineShape'))
        self.assertEqual(hashlib.sha256(body['text'].encode()).hexdigest(),spec['wire_sha256'])
        self.assertEqual(body['sessionTimeoutSeconds'],7200)

    def test_live_launcher_without_authorization_stops_without_network(self):
        code='''
import requests
requests.Session.send=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('NETWORK_FORBIDDEN'))
from u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02.launch import launch
try:launch()
except PermissionError:print('MISSING_AUTHORIZATION_BLOCKED_BEFORE_NETWORK')
else:raise AssertionError('Unexpected launch')
'''
        r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn('MISSING_AUTHORIZATION_BLOCKED_BEFORE_NETWORK',r.stdout)
        self.assertFalse((HERE/'execution').exists());self.assertFalse((HERE/'HTTP_RECEIPT.json').exists())

    def test_collector_refuses_when_no_accepted_version(self):
        code='''
import requests
requests.Session.send=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('NETWORK_FORBIDDEN'))
from u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02.collect import collect
try:collect()
except AssertionError as e:
 assert 'No accepted existing version' in str(e)
 print('NO_VERSION_NO_OUTPUT_QUERY')
else:raise AssertionError('Unexpected collection')
'''
        r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn('NO_VERSION_NO_OUTPUT_QUERY',r.stdout)


if __name__=='__main__':unittest.main()
