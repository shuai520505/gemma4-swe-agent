import io,json,tarfile,tempfile,unittest,zipfile
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

if __name__=='__main__':unittest.main()
