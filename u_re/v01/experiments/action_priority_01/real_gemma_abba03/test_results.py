"""Independent offline checks against real raw evidence;no new model or task runs."""
import json,os,re,unittest,zipfile
from pathlib import Path
from .notebook import HERE,PRIOR,sha
from .cpu_acceptance import counts,verify

@unittest.skipUnless(os.environ.get('GPU03_PRIVATE_ARCHIVE'),'Private raw archive required for actual-output audit')
class ActualResults(unittest.TestCase):
    def setUp(self):
        self.z=zipfile.ZipFile(os.environ['GPU03_PRIVATE_ARCHIVE']);self.addCleanup(self.z.close)
        self.metrics=json.loads((HERE/'AGENT_BEHAVIOR_METRICS.json').read_bytes())['runs']
    def load(self,name):return json.loads(self.z.read(name))
    def test_cpu_and_gpu_used_identical_registered_source_bytes(self):
        proof=verify();manifest=json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())
        self.assertEqual(proof['payload_sha256'],self.load('PAYLOAD_IDENTITY.json')['payload_sha256'])
        for n,h in manifest['files'].items():self.assertEqual(sha(self.z.read('source/'+n)),h)
    def test_native_results_junit_patches_cleanup_and_metrics(self):
        expected=[False,True,True,True]
        for row,resolved in zip(self.metrics,expected):
            root=f"results/runs/{row['run']:02d}-{row['instance_id']}-{row['arm']}/"
            native=self.load(root+'official_result.json');self.assertIs(native['resolved'],resolved)
            j=counts(self.z.read(root+'verifier/phase2.junit.xml'));self.assertEqual(j['errors'],0);self.assertEqual(j['failures'],0 if resolved else 1)
            self.assertTrue(self.load(root+'worker_done.json')['cleanup_complete']);self.assertTrue(self.load(root+'audit_result.json')['process_tree_stopped'])
            self.assertEqual(self.load(root+'agent/agent_result.json')['charged_tools'],row['charged_tools'])
            patch=self.z.read(root+'final.patch');self.assertTrue(patch.strip())
            identity=json.loads((HERE/'ABBA_RESULTS.json').read_bytes())['runs'][row['run']-1]
            self.assertEqual(len(patch),identity['patch_bytes']);self.assertEqual(sha(patch),identity['patch_sha256'])
    def test_all_real_http_responses_usage_and_route(self):
        total=0;tokens=dict(prompt_tokens=0,completion_tokens=0,total_tokens=0)
        for row in self.metrics:
            root=f"results/runs/{row['run']:02d}-{row['instance_id']}-{row['arm']}/"
            wire=[json.loads(l) for l in self.z.read(root+'agent/http_wire.jsonl').splitlines()]
            requests=[r for r in wire if r['kind']=='http_request'];responses=[r for r in wire if r['kind']=='http_response']
            self.assertEqual(len(requests),len(responses));self.assertEqual(len(requests),row['model_requests']);total+=len(requests)
            subtotal=dict.fromkeys(tokens,0)
            for r in responses:
                self.assertEqual(r['status'],200);self.assertNotIn('CPU_SCRIPTED',str(r['body']))
                for k in tokens:subtotal[k]+=r['body']['usage'][k]
            self.assertEqual(subtotal,row['received_usage'])
            for k in tokens:tokens[k]+=subtotal[k]
            self.assertEqual(self.load(root+'runtime_config.json')['model_transport'],'REAL_GEMMA')
        self.assertEqual(total,106);self.assertEqual(tokens,dict(prompt_tokens=840263,completion_tokens=20704,total_tokens=860967))
        self.assertEqual(self.load('results/GPU_COST.json')['scripted_HTTP_requests'],0)
    def test_submit_metrics_match_native_callback_state_and_tool_responses(self):
        for row in self.metrics:
            root=f"results/runs/{row['run']:02d}-{row['instance_id']}-{row['arm']}/agent/"
            events=[json.loads(l) for l in self.z.read(root+'events.jsonl').splitlines()]
            # Activity text is optional:run4 has successful native responses and
            # a persistent context flag but no "Patch submitted" activity line.
            counters=[e for e in events if e.get('kind')=='counters']
            self.assertEqual(counters[-1]['patch_submitted'],row['successful_submit'])
            adk=[json.loads(l) for l in self.z.read(root+'adk_events.jsonl').splitlines()]
            submits=[r['function_response'] for event in adk for r in event.get('event',{}).get('content',{}).get('parts',[]) if r.get('function_response',{}).get('name')=='submit_patch' and r['function_response']['response'].get('status')=='ok']
            self.assertEqual(len(submits),row['successful_submit_count'])
            if submits:self.assertGreater(submits[0]['response']['patch_size'],0)
    def test_first_edits_are_filesystem_events_and_pair_not_uniformly_earlier(self):
        for row in self.metrics:
            root=f"results/runs/{row['run']:02d}-{row['instance_id']}-{row['arm']}/agent/"
            events=[json.loads(l) for l in self.z.read(root+'events.jsonl').splitlines()]
            start=next(e['recorded_monotonic'] for e in events if e.get('agent_started'))
            changes=[e for e in events if e.get('production_changed') and e['start_monotonic']>=start]
            self.assertEqual(row['first_source_edit_seconds'],changes[0]['end_monotonic']-start if changes else None)
        self.assertIsNone(self.metrics[0]['first_source_edit_seconds'])
        self.assertGreater(self.metrics[2]['first_source_edit_seconds'],self.metrics[3]['first_source_edit_seconds'])
    def test_hardware_weights_server_and_all_sandboxes_clean(self):
        devices=self.load('results/GPU_DEVICES.json');self.assertEqual(len(devices),4)
        self.assertTrue(all(d['name']=='NVIDIA L4' for d in devices))
        lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes());self.assertEqual(self.load('results/MODEL_FILES.json'),lock['model']['files'])
        cleanup=self.load('results/SERVER_CLEANUP.json');self.assertTrue(cleanup['confirmed']);self.assertEqual(cleanup['remaining'],[]);self.assertIsNone(cleanup['idle_error'])
        self.assertEqual(self.load('results/EXECUTION_STATUS.json')['status'],'GPU03_REAL_GEMMA_ABBA_COMPLETE')

if __name__=='__main__':unittest.main()
