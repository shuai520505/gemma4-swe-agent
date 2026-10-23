"""Derive CPU gate from downloaded,version-bound raw execution evidence."""
import json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from .notebook import HERE,ROOT,PRIOR,sha,write

def counts(raw):
    cases=list(ET.fromstring(raw).iter('testcase'))
    return dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))

def audit(archive,attempt='cpu-e2e01'):
    archive=Path(archive).resolve();assert not archive.is_relative_to(ROOT)
    cpu=HERE/attempt;receipt=json.loads((cpu/'execution/HTTP_RECEIPT.json').read_bytes())
    m=json.loads(sorted((cpu/'read_observations').glob('read-*/OUTPUT_MANIFEST.json'))[-1].read_bytes())
    assert m['status']=='COMPLETE' and m['version_bound_before_after']
    item=next(f for f in m['files'] if f['file']==attempt+'.zip')
    assert item['Notebook_id']==receipt['Notebook_id'] and item['version']==receipt['accepted_version']==1 and item['complete']
    assert sha(archive.read_bytes())==item['sha256']
    manifest=json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes());lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        load=lambda n:json.loads(z.read(n))
        payload=load('PAYLOAD_IDENTITY.json');assert payload['payload_sha256']==manifest['payload_sha256'] and payload['mode']=='CPU_DRY_RUN'
        for name,h in manifest['files'].items():assert sha(z.read('source/'+name))==h,name
        acceptance=load('results/CPU_ACCEPTANCE.json')
        assert acceptance['status']=='GPU03_PAYLOAD_END_TO_END_CPU_PASS' and acceptance['CPU_MODEL']=='SCRIPTED_ONLY'
        assert acceptance['cleanup_complete'] and acceptance['real_Gemma_requests']==0
        assert acceptance['production_entry']==manifest['production_entry']
        identities=load('results/TASK_IDENTITIES.json');baselines=[]
        for task in lock['tasks']:
            ident=task['instance_id'];root='results/baselines/'+ident+'/'
            for key in ('repo','base_commit','issue_sha256','task_record_sha256','test_patch_sha256','input_files'):assert identities[ident][key]==task[key]
            result=load(root+'official_result.json');audit=load(root+'audit.json');junit=z.read(root+'phase2.junit.xml')
            assert not result['resolved'] and result['test_exit_code']==1
            assert audit['category']=='assertion_failure' and not audit['infrastructure_stop']
            assert audit['counts']==counts(junit)==task['native_baseline_counts']
            assert load(root+'cleanup.json')['complete'] and load(root+'provenance.json')['verified']
            assert z.read(root+'before.json')==z.read(root+'after.json')
            baselines.append(dict(instance_id=ident,counts=counts(junit),TaskResult_sha256=sha(z.read(root+'official_result.json')),JUnit_sha256=sha(junit),source_provenance=True,cleanup=True))
        root='results/runs/01-ure_gpu03_owned-A/'
        worker=load(root+'audit_result.json');done=load(root+'worker_done.json');native=load(root+'official_result.json')
        assert worker['allow_next_run'] and worker['process_tree_stopped'] and worker['cleanup_complete']
        assert done['cleanup_complete'] and done['integrity_complete'] and native['resolved'] and native['test_exit_code']==0
        assert counts(z.read(root+'verifier/phase2.junit.xml'))==dict(tests=1,failures=0,errors=0,skipped=0)
        agent=load(root+'agent/agent_result.json');http=load(root+'HTTP_AUDIT.json');runtime=load(root+'runtime_config.json')
        assert agent['patch_submitted'] and agent['patch_bytes']>0 and http['passed'] and http['requests']==6
        assert runtime['real_model'] is False and runtime['model_transport']=='CPU_SCRIPTED_ONLY'
        assert runtime['budget']['agent_seconds']==300 and runtime['budget']['tool_budget']==60 and runtime['budget']['command_seconds']==120
        events=[json.loads(line) for line in z.read(root+'agent/events.jsonl').splitlines()]
        assert any(e.get('production_changed') for e in events)
        assert load('results/CPU_TRANSPORT_PROOF.json')['tool_results_returned_to_model']
        assert load('results/isolation/cleanup.json')['complete'] is True
        proof=dict(status=acceptance['status'],CPU_MODEL='SCRIPTED_ONLY',Notebook_id=receipt['Notebook_id'],version=1,platform_status='COMPLETE',
            payload_sha256=manifest['payload_sha256'],production_entry=manifest['production_entry'],all_production_file_hashes_match=True,
            raw_archive_path=str(archive),raw_archive_sha256=sha(archive.read_bytes()),raw_bytes=archive.stat().st_size,CRC_valid=True,
            baseline_checks=baselines,synthetic_agent_result=agent,synthetic_JUnit=counts(z.read(root+'verifier/phase2.junit.xml')),
            worker_cleanup=True,HTTP_terminal_integrity=True,scripted_HTTP_requests=http['requests'],real_Gemma_requests=0,
            GPU01_CPU_GATE_PIN_verified=True,GPU02_lazy_import_executed=True,observer_directory_collision_absent=True,
            scope='Exact sealed GPU production ZIP executed via shared Session and actual supervised Worker;only external CPU model transport and owned synthetic Agent input differ')
    return proof

def seal(archive,attempt='cpu-e2e01'):write(HERE/'CPU_END_TO_END_ACCEPTANCE.json',audit(archive,attempt))

def verify():
    expected=json.loads((HERE/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
    actual=audit(expected['raw_archive_path'])
    assert actual==expected,'CPU gate must be re-derived from exact raw archive,not a manually changed flag'
    return actual

if __name__=='__main__':
    import sys
    seal(sys.argv[1])
