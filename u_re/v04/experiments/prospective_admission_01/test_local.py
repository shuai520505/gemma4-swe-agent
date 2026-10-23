import asyncio,io,json,tarfile,tempfile,unittest,zipfile
from pathlib import Path
from .common import HERE,ROOT,PRIOR,sha
from .identity import tree_digest,overlay_content_digest,conflicts

class AdmissionTests(unittest.TestCase):
    def test_frozen_candidates_and_order(self):
        p=json.loads((HERE/'GPU_REPLICATION_PROTOCOL.json').read_bytes())
        self.assertEqual((HERE/'GPU_REPLICATION_PROTOCOL.json').read_bytes(),(PRIOR/'GPU_REPLICATION_PROTOCOL.json').read_bytes())
        self.assertEqual([r['instance_id'] for r in p['ranked_candidates']],['fastapi_13713','fastapi_14297','fastapi_14459','fastapi_14306','fastapi_14455'])
        for key,path in [('A',ROOT/'u_re/v01/experiments/action_priority_01/submission_action_v01.zip'),('B',PRIOR/'submission_egr_v04.zip')]:
            self.assertEqual(sha(path.read_bytes()),p['candidates'][key]['ZIP_sha256'])
    def test_tree_content_not_archive_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths=[]
            for i in range(3):
                path=Path(tmp)/f'{i}.tgz';paths.append(path)
                with tarfile.open(path,'w:gz') as z:
                    for rel,data in [(f'root{i}/module.py',b'code' if i<2 else b'changed'),(f'root{i}/.git/random',str(i).encode())]:
                        item=tarfile.TarInfo(rel);item.size=len(data);item.mtime=i;z.addfile(item,io.BytesIO(data))
            self.assertEqual(tree_digest(paths[0]),tree_digest(paths[1]))
            self.assertNotEqual(tree_digest(paths[0]),tree_digest(paths[2]))
    def test_overlay_offsets_not_content_identity(self):
        a='diff --git a/tests/x.py b/tests/x.py\n@@ -1 +1 @@\n-old\n+new'
        self.assertEqual(overlay_content_digest(a),overlay_content_digest(a.replace('@@ -1 +1 @@','@@ -99 +99 @@')))
        self.assertNotEqual(overlay_content_digest(a),overlay_content_digest(a.replace('+new','+other')))
    def test_conflicts_stop_on_historical_alias(self):
        a=dict(repo='r',issue_sha256='1',base_commit='a',snapshot_tree_sha256='x',test_overlay_content_sha256='u',input_files={})
        b=dict(a,issue_sha256='2',base_commit='b',test_overlay_content_sha256='v')
        self.assertEqual(conflicts({'new':a,'old':b},['new'])[0]['shared'],['snapshot_tree_sha256'])
        b['snapshot_tree_sha256']='y';self.assertEqual(conflicts({'new':a,'old':b},['new']),[])
    def test_actual_screen_payload(self):
        from .notebook import validate_screen
        self.assertTrue(validate_screen('screen01'))
        b=json.loads((HERE/'screen01/BUILD.json').read_bytes())
        self.assertEqual(b['configuration']['Agent_runs'],0);self.assertFalse(b['configuration']['GPU'])
        self.assertTrue(b['entry'].endswith('prospective_admission_01.screen'))
    def test_raw_snapshot_pairing_not_blanket_error_waiver(self):
        from .audit import native_counts
        from u_re.v02.experiments.env_recovery_admission_01.junit_audit import parse_snapshot_phases
        record=json.loads((HERE/'SELECTED_TASKS.json').read_bytes())['tasks'][1]
        with zipfile.ZipFile(record['source_archive']['private_path']) as z:
            root='validation/03-fastapi_14459/'
            self.assertEqual(native_counts(z,root),dict(tests=8,failures=2,errors=2,skipped=0))
            raw=z.read(root+'phase2.junit.xml')
            with self.assertRaises(AssertionError):parse_snapshot_phases(raw.replace(b'some snapshots in this test have incorrect values.',b'independent environment failure'))
    def test_preserved_stop_and_derived_admission(self):
        original=json.loads((HERE/'TASK_ADMISSION_RESULTS.json').read_bytes())
        final=json.loads((HERE/'NORMALIZED_ADMISSION_VIEW.json').read_bytes())
        selected=json.loads((HERE/'SELECTED_TASKS.json').read_bytes())['tasks']
        self.assertEqual(original['status'],'V04_ADMISSION_BLOCKED')
        self.assertEqual(final['original_screen_status'],original['status'])
        self.assertEqual([r['instance_id'] for r in selected],['fastapi_14297','fastapi_14459'])
        self.assertEqual(selected[1]['snapshot_duplicate_teardown_count'],2)
        self.assertEqual(selected[1]['independent_environment_errors'],0)
    def test_final_production_and_CPU_only_authorization(self):
        from .production import validate
        from .session import coordinator,run
        self.assertTrue(validate('cpu-e2e02'))
        lock=json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
        f=coordinator(lock,{})
        self.assertEqual(f.__globals__['__package__'],'u_re.v04.experiments.prospective_admission_01')
        self.assertEqual([r['arm'] for r in lock['order']],list('ABBA'))
        with self.assertRaises(AssertionError):asyncio.run(run('unused',0,mode='GPU'))
        with zipfile.ZipFile(HERE/'payload.zip') as z:
            for n,h in json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())['files'].items():
                if n.startswith(HERE.relative_to(ROOT).as_posix()+'/'):self.assertEqual(sha((ROOT/n).read_bytes()),h)
            self.assertFalse(any(n.endswith('cpu_transport.py') for n in z.namelist()))

if __name__=='__main__':unittest.main()
