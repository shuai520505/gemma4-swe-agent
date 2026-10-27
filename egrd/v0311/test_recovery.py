"""Offline simulated OS/HTTP fixtures. None establishes Kaggle device capability."""
import copy
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.request
import zipfile

from egrd.v031 import device_runtime
from .device_gate import verify_node
from .lifecycle import release_owned, finish_session
from .prepare import verify_history, HERE, ROOT, OLD, PRIVATE, sha
from .boundary_audit import compare
from .scripted_boundary import ScriptedBoundary


class Recovery(unittest.TestCase):
    def install_case(self, case):
        class Node:
            present=True
            def is_symlink(self):return case=='symlink'
            def exists(self):return self.present
            def unlink(self):self.present=False
            def chmod(self,mode):pass
        node=Node()
        node.stat=lambda:SimpleNamespace(st_mode=stat.S_IFREG if case=='regular' else stat.S_IFCHR,
                                         st_rdev=258 if case=='wrong_device' else 259)
        class Root:
            def __truediv__(self,key):self.key=key;return node
        def create(*args):
            if case=='denied':raise PermissionError('SIMULATED_CAP_MKNOD_DENIED')
            if case=='missing_parent':raise FileNotFoundError('SIMULATED_MISSING_DEV_DIRECTORY')
            node.present=True
        with patch.object(device_runtime.os,'mknod',side_effect=create,create=True) as create_mock, \
             patch.object(device_runtime.os,'makedev',return_value=259,create=True):
            error={'denied':PermissionError,'missing_parent':FileNotFoundError,
                   'symlink':AssertionError,'regular':AssertionError,'wrong_device':AssertionError}.get(case)
            if error:
                with self.assertRaises(error):device_runtime.install_null_device(Root())
            else:self.assertFalse(device_runtime.install_null_device(Root())['regular_file_fallback'])
            self.assertEqual(create_mock.call_count,0 if case=='symlink' else 1)
            if case in ('denied','missing_parent'):self.assertFalse(node.present)

    def test_simulated_character_device_success(self):self.install_case('success')
    def test_simulated_mknod_denied(self):self.install_case('denied')
    def test_simulated_unexpected_regular_result(self):self.install_case('regular')
    def test_simulated_existing_symlink(self):self.install_case('symlink')
    def test_simulated_device_number_mismatch(self):self.install_case('wrong_device')
    def test_simulated_missing_parent(self):self.install_case('missing_parent')

    def test_lstat_symlink_regular_wrong_device_rejected(self):
        for mode,rdev in ((stat.S_IFLNK,259),(stat.S_IFREG,0),(stat.S_IFCHR,258)):
            with self.subTest(mode=mode,rdev=rdev),patch.object(os,'makedev',return_value=259,create=True):
                node=SimpleNamespace(lstat=lambda:SimpleNamespace(st_mode=mode,st_rdev=rdev))
                with self.assertRaises(AssertionError):verify_node(node)

    def test_partial_initialization_and_lease_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root=base/'owned';root.mkdir();(root/'partial').write_text('fixture')
            lease=base/'lease.json';entry=dict(root=str(root),lease=str(lease),token='fixture',uid=23456,sid='owned')
            lease.write_text(json.dumps(entry));killed=[]
            result=release_owned(entry,base,lambda e:killed.append(e['uid']) or [])
            self.assertEqual(killed,[23456]);self.assertTrue(result['root_removed'] and result['lease_removed'])

    def test_cleanup_rejects_wrong_owner_and_escaping_root(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);lease=base/'lease';lease.write_text(json.dumps(dict(token='other',uid=23456)))
            entry=dict(root=str(base/'owned'),lease=str(lease),token='fixture',uid=23456,sid='owned')
            with self.assertRaises(AssertionError):release_owned(entry,base,lambda e:self.fail('must not kill'))
            entry['root']=str(base.parent/'outside')
            with self.assertRaises(AssertionError):release_owned(entry,base,lambda e:self.fail('must not kill'))
            self.assertTrue(lease.exists())

    def test_failed_cleanup_does_not_falsely_remove_lease(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root=base/'owned';root.mkdir();lease=base/'lease'
            entry=dict(root=str(root),lease=str(lease),token='fixture',uid=23456,sid='owned')
            lease.write_text(json.dumps(entry))
            def fail(entry):raise RuntimeError('SIMULATED_PROCESS_STILL_ALIVE')
            with self.assertRaises(RuntimeError):release_owned(entry,base,fail)
            self.assertTrue(lease.exists() and root.exists())

    def test_real_local_git_rejects_contaminated_regular_config(self):
        with tempfile.TemporaryDirectory() as temp:
            config=Path(temp)/'synthetic-config';config.write_text('not valid git configuration\n')
            env=dict(os.environ,GIT_CONFIG_GLOBAL=str(config),GIT_CONFIG_NOSYSTEM='1')
            bad=subprocess.run(['git','config','--global','--list'],env=env,capture_output=True)
            self.assertNotEqual(bad.returncode,0);self.assertIn(b'bad config',bad.stderr)
            config.write_bytes(b'')
            good=subprocess.run(['git','config','--global','--list'],env=env,capture_output=True)
            self.assertEqual(good.returncode,0)
        # An ordinary empty config is a local negative-test control only. No
        # fallback implementation or changed child Git environment is deployed.

    def test_requests_persist_before_consumer_exception(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);transport=ScriptedBoundary(['fixture'],root/'requests').start()
            raw=b'{"model":"SCRIPTED_ONLY","messages":[{"role":"user","content":"public fixture"}]}'
            try:
                response=urllib.request.urlopen(urllib.request.Request(transport.base_url+'/chat/completions',
                    data=raw,headers={'Content-Type':'application/json'}),timeout=5)
                self.assertEqual(response.status,200);response.read()
                try:raise RuntimeError('SIMULATED_RUNNER_EXCEPTION')
                except RuntimeError:pass
                self.assertEqual((root/'requests/request_001.json').read_bytes(),raw)
                self.assertEqual(len(json.loads((root/'SCRIPTED_HTTP_REQUESTS.json').read_bytes())),1)
            finally:transport.stop()
            self.assertTrue(transport.cleaned)

    def test_boundary_detects_supplement_and_unexpected_parameters(self):
        a=dict(model='fixture',messages=[dict(role='system',content='same'),dict(role='user',content='ISSUE')],tools=[],max_tokens=16384)
        b=copy.deepcopy(a);b['messages'][1]['content']+=' RECEIPT'
        audit,_=compare(json.dumps(a).encode(),json.dumps(b).encode(),'ISSUE',' RECEIPT')
        self.assertTrue(audit['only_supplement_differs']);self.assertIsNone(audit['token_overhead'])
        b['max_tokens']=8192
        audit,_=compare(json.dumps(a).encode(),json.dumps(b).encode(),'ISSUE',' RECEIPT')
        self.assertFalse(audit['parameters_equal'] or audit['only_supplement_differs'])

    def test_transport_cleanup_survives_manager_cleanup_exception(self):
        with tempfile.TemporaryDirectory() as temp:
            transport=SimpleNamespace(calls=[{'fixture':True}],cleaned=False)
            def stop():transport.cleaned=True
            transport.stop=stop
            def fail():raise RuntimeError('SIMULATED_MANAGER_CLEANUP_FAILURE')
            manager=SimpleNamespace(cleanup_all=fail)
            with self.assertRaises(RuntimeError):finish_session(transport,manager,Path(temp))
            self.assertTrue(transport.cleaned)
            self.assertTrue(json.loads((Path(temp)/'TRANSPORT_CLEANUP.json').read_bytes())['complete'])
            self.assertEqual(len(json.loads((Path(temp)/'SCRIPTED_HTTP_REQUESTS.json').read_bytes())),1)

    def test_unchanged_history_and_scope(self):verify_history()

    def test_sealed_cpu_payload_metadata_and_entry_order(self):
        build=json.loads((HERE/'CPU_BUILD.json').read_bytes())
        folder=PRIVATE/'notebook-v1'
        with zipfile.ZipFile(folder/'payload.zip') as archive:
            self.assertIsNone(archive.testzip())
            for name,digest in build['members'].items():
                self.assertEqual(sha(archive.read(name)),digest,name)
                if name.startswith('egrd/v0311/'):
                    self.assertEqual(archive.read(name),(ROOT/name).read_bytes())
        meta=json.loads((folder/'kernel-metadata.json').read_bytes())
        self.assertTrue(meta['is_private'])
        self.assertFalse(any(meta[k] for k in ('enable_gpu','enable_tpu','enable_internet','machine_shape','model_sources','competition_sources')))
        nb=json.loads((folder/'study.ipynb').read_bytes())
        body=nb['cells'][1]['source']
        self.assertLess(body.index('check_device(RUN_DIR)'),body.index("'pip','install'"))
        for cell in nb['cells']:compile(cell['source'],'<sealed-cpu-notebook>','exec')
        self.assertEqual(sha((folder/'study.ipynb').read_bytes()),build['Notebook_sha256'])

    def test_actual_archive_crc_all_manifest_files_and_runtime_sources(self):
        public=json.loads((HERE/'RAW_ARCHIVES.json').read_bytes())
        path=Path(public['path'])
        self.assertEqual(sha(path.read_bytes()),public['sha256'])
        build=json.loads((HERE/'CPU_BUILD.json').read_bytes())
        with zipfile.ZipFile(path) as archive:
            self.assertIsNone(archive.testzip())
            evidence=json.loads(archive.read('evidence_manifest.json'))
            for name,identity in evidence.items():
                self.assertEqual(sha(archive.read(name)),identity['sha256'],name)
            for name,digest in build['members'].items():
                self.assertEqual(sha(archive.read('source/'+name)),digest,name)

    def test_ready_schema_rejects_failed_gate_and_invented_native_outcome(self):
        from jsonschema import Draft202012Validator,ValidationError
        schema=json.loads((HERE/'CPU_RUNNER_RESULTS.schema.json').read_bytes())
        Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema)
        result=json.loads((HERE/'CPU_RUNNER_RESULTS.json').read_bytes())
        validator.validate(result)
        changed=copy.deepcopy(result);changed['gates']['native_submit']=False
        with self.assertRaises(ValidationError):validator.validate(changed)
        changed=copy.deepcopy(result);changed['records'][0]['official_native_resolved']=True
        with self.assertRaises(ValidationError):validator.validate(changed)


if __name__=='__main__':unittest.main()
