"""Offline regressions only: no API, Notebook dispatch, model or source repair."""
import copy
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
import zipfile

from jsonschema import Draft202012Validator, ValidationError

from .cli import HERE,ROOT,PRIVATE,sha
from .runtime import restore,tree_identity,cleanup,command


class Platform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((HERE/'DATASET_BUILD_V1.json').read_bytes())
        cls.results=json.loads((HERE/'TASK_REPRODUCTIONS.json').read_bytes())
        cls.schema=json.loads((HERE/'REPAIR_EVIDENCE.schema.json').read_bytes())

    def test_source_bundle_member_hashes_and_licenses(self):
        p=PRIVATE/'dataset-v1/data_bundle.zip'
        self.assertEqual(sha(p.read_bytes()),self.manifest['bundle_sha256'])
        with zipfile.ZipFile(p) as z:
            self.assertIsNone(z.testzip())
            for name,digest in self.manifest['member_hashes'].items():
                self.assertEqual(sha(z.read(name)),digest,name)
            tasks=json.loads(z.read('metadata/task_registry.json'))['tasks']
            self.assertEqual([t['license'] for t in tasks],['BSD-3-Clause','Apache-2.0','MIT'])
            for t in tasks:
                with tarfile.open(fileobj=io.BytesIO(z.read(t['snapshot_path'])),mode='r:gz') as src:
                    for name,digest in t['license_file_hashes'].items():
                        self.assertEqual(sha(src.extractfile(t['archive_root']+'/'+name).read()),digest)

    def test_order_and_exposure_preserved(self):
        with zipfile.ZipFile(PRIVATE/'dataset-v1/data_bundle.zip') as z:
            original=(ROOT/'egrd/v023/EXTERNAL_SOURCE_LOCK.json').read_bytes()
            self.assertEqual(z.read('metadata/external_source_lock.json'),original)
            source=json.loads(original)
            exposures=json.loads(z.read('metadata/exposure.json'))
            self.assertEqual(len(exposures),129+492)
            self.assertTrue(all(r['independent_confirmation_eligible'] is False for r in exposures[:131]))
            self.assertEqual([r['instance_id'] for r in exposures[129:]],
                             [r['instance_id'] for r in source['ranked_metadata']])
            self.assertEqual([r['instance_id'] for r in self.results['records']],
                [source['ranked_metadata'][0]['instance_id'],source['ranked_metadata'][1]['instance_id'],'fastapi_14297'])

    def test_raw_results_hash_crc_commands_and_source_binding(self):
        raw=PRIVATE/'output-v1/egrd-v03-cpu-v1.zip'
        self.assertEqual(sha(raw.read_bytes()),self.results['raw_archive_sha256'])
        with zipfile.ZipFile(raw) as z:
            self.assertIsNone(z.testzip())
            for r in self.results['records']:
                prefix=f"results/tasks/{r['instance_id']}/"
                self.assertEqual(sha(z.read(prefix+'RESULT.json')),r['raw_result_sha256'])
                self.assertEqual(sha(z.read(prefix+'probe.json')),r['probe_receipt_sha256'])
                self.assertEqual(r['source_tree_before'],r['source_tree_after'])
                self.assertTrue(r['source_unchanged'] and r['cleanup'] and r['positive_controls_passed'])
                self.assertIsNone(r['official_native_resolved']);self.assertIsNone(r['swebench_resolved'])
                self.assertIsNone(r['prompt_tokens']);self.assertIsNone(r['completion_tokens'])
                self.assertIsNone(r['tool_requests'])
                self.assertTrue(all(c['owned_process_reaped'] and not c['timed_out'] for c in r['commands'].values()))
            self.assertEqual(self.results['genuine_issue_failures'],3)
            # FastAPI fails by the predeclared exception, not a fabricated assertion.
            self.assertEqual(self.results['records'][2]['failed_target_assertions'],0)
            self.assertEqual(self.results['records'][2]['target_exception_type'],'TypeError')

    def test_notebook_source_boundary_and_no_accelerator(self):
        meta=json.loads((PRIVATE/'notebook-v1/kernel-metadata.json').read_bytes())
        self.assertTrue(meta['is_private']);self.assertFalse(meta['enable_gpu'])
        self.assertFalse(meta['enable_tpu']);self.assertFalse(meta['enable_internet'])
        self.assertFalse(meta['model_sources']);self.assertFalse(meta['competition_sources'])
        nb=PRIVATE/'notebook-v1/study.ipynb'
        build=json.loads((HERE/'CPU_BUILD_V1.json').read_bytes())
        self.assertEqual(sha(nb.read_bytes()),build['Notebook_sha256'])
        self.assertEqual(sha((HERE/'runtime.py').read_bytes()),build['runtime_sha256'])
        self.assertFalse((PRIVATE/'notebook-dispatch-v2.json').exists())

    def test_dataset_result_version_keeps_input_bytes(self):
        self.assertEqual(sha((PRIVATE/'dataset-v2/data_bundle.zip').read_bytes()),self.manifest['bundle_sha256'])
        for name in ('CPU_EXECUTION_RECORD.json','TASK_REPRODUCTIONS.json'):
            self.assertEqual((PRIVATE/'dataset-v2'/name).read_bytes(),(HERE/name).read_bytes())
        meta=json.loads((PRIVATE/'dataset-v2/dataset-metadata.json').read_bytes())
        self.assertTrue(meta['isPrivate']);self.assertEqual(meta['licenses'],[{'name':'other'}])

    def test_frozen_candidates_and_history_unchanged(self):
        for arm,digest in dict(N='c0618f4a996883600b1353a7a7e5fe0d8588f4393613984f30f725b4cfa98e69',
                              D='253002dcea2f077945aebacee3c9ea3a6033601aedcf4b55964d99fe8b5b09d7').items():
            self.assertEqual(sha((ROOT/f'egrd/v022/submission_{arm}.zip').read_bytes()),digest)
        changed=subprocess.check_output(['git','diff','--name-only','c8c92a45688a4a7005dea852e7927baefe980402'],cwd=ROOT,text=True).splitlines()
        self.assertTrue(all(p.startswith('egrd/v03/') for p in changed),changed)

    def test_safe_archive_and_source_freshness(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);archive=root/'public.tgz'
            with tarfile.open(archive,'w:gz') as z:
                m=tarfile.TarInfo('fixture/src.py');body=b'x = 1\n';m.size=len(body);z.addfile(m,io.BytesIO(body))
            source=restore(archive,root/'work','fixture');before=tree_identity(source)
            (source/'src.py').write_bytes(b'x = 2\n')
            self.assertNotEqual(before,tree_identity(source))
            self.assertTrue(cleanup(root/'work',root))
            with self.assertRaises(AssertionError):cleanup(root,root)

    def test_archive_traversal_and_external_link_rejected(self):
        for name,link in (('../escape',None),('/absolute',None),('fixture/link','../../escape')):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);archive=root/'bad.tgz'
                with tarfile.open(archive,'w:gz') as z:
                    m=tarfile.TarInfo(name)
                    if link:m.type=tarfile.SYMTYPE;m.linkname=link
                    z.addfile(m)
                with self.assertRaises(AssertionError):restore(archive,root/'work','fixture')
                self.assertFalse((root/'escape').exists())

    def test_command_exception_and_timeout_reaped(self):
        import os,sys
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            fail=command([sys.executable,'-c','raise ValueError("synthetic")'],root,root/'error',dict(os.environ),5)
            self.assertNotEqual(fail['returncode'],0);self.assertTrue(fail['owned_process_reaped'])
            stop=command([sys.executable,'-c','import time;time.sleep(10)'],root,root/'timeout',dict(os.environ),0.2)
            self.assertTrue(stop['timed_out'] and stop['owned_process_reaped'])

    def test_observation_schema_unknown_and_claim_provenance(self):
        Draft202012Validator.check_schema(self.schema)
        item=dict(task_id='public-synthetic',source_sha256='a'*64,patch_sha256=None,
            hypothesis=dict(claim_sha256=None,classification='UNKNOWN',review_evidence_sha256=None),edit_kind='NONE',
            verification=dict(program_sha256=None,tested_source_sha256=None,receipt_sha256=None,returncode=None,
                assertions_executed=None,classification='NOT_RUN',issue_relevance='UNKNOWN',freshness='UNKNOWN',post_edit=None),
            usage=dict(model_requests=None,tool_requests=None,prompt_tokens=None,completion_tokens=None,wall_seconds=None),
            termination='NOT_RUN')
        validator=Draft202012Validator(self.schema);validator.validate(item)
        self.assertIsNone(item['usage']['prompt_tokens'])
        false_claim=copy.deepcopy(item);false_claim['hypothesis']['classification']='SUPPORTED_BY_OBSERVED_DISCRIMINATION'
        with self.assertRaises(ValidationError):validator.validate(false_claim)
        invalid=copy.deepcopy(item);invalid['usage']['prompt_tokens']=-1
        with self.assertRaises(ValidationError):validator.validate(invalid)


if __name__=='__main__':unittest.main()
