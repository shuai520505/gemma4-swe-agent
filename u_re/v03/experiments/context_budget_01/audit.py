"""Derive CPU acceptance from version-bound downloaded bytes, never a flag."""
import json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from .common import HERE,ROOT,write,sha
def counts(raw):
    cases=list(ET.fromstring(raw).iter('testcase'))
    return dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
def audit_cpu(archive,attempt):
    archive=Path(archive).resolve();assert not archive.is_relative_to(ROOT)
    d=HERE/attempt;receipt=json.loads((d/'execution/HTTP_RECEIPT.json').read_bytes())
    output=json.loads(sorted((d/'read_observations').glob('read-*/OUTPUT_MANIFEST.json'))[-1].read_bytes())
    item=next(f for f in output['files'] if f['file']=='v03-'+attempt+'.zip')
    assert output['status']=='COMPLETE' and output['version_bound_before_after'] and item['complete']
    assert item['Notebook_id']==receipt['Notebook_id'] and item['version']==receipt['accepted_version']==1
    assert sha(archive.read_bytes())==item['sha256']
    manifest=json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes());lock=json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        load=lambda n:json.loads(z.read(n))
        assert load('PAYLOAD_IDENTITY.json')['payload_sha256']==manifest['payload_sha256']
        for n,h in manifest['files'].items():assert sha(z.read('source/'+n))==h,n
        acceptance=load('results/CPU_ACCEPTANCE.json')
        assert acceptance['status']=='V03_PAYLOAD_END_TO_END_CPU_PASS' and acceptance['CPU_MODEL']=='SCRIPTED_ONLY' and acceptance['real_Gemma_requests']==0
        assert acceptance['owned_scripted_runs']==2 and acceptance['HTTP_requests']==12 and acceptance['cleanup_complete']
        before=load('PRODUCTION_ENVIRONMENT_BEFORE.json');assert before==load('PRODUCTION_ENVIRONMENT_AFTER.json')
        assert before==json.loads((ROOT/'u_re/v02/experiments/env_recovery_admission_01/V02B_ENVIRONMENT_LOCK.json').read_bytes())['fingerprint']
        checks=load('POLICY_BOUNDARY_CHECKS.json');assert [r['rejected'] for r in checks]==[False,True,False,False,True]
        baseline=[]
        for t in lock['tasks']:
            root='results/baselines/'+t['instance_id']+'/'
            result=load(root+'official_result.json');audit=load(root+'audit.json')
            assert not result['resolved'] and result['test_exit_code']==1 and counts(z.read(root+'phase2.junit.xml'))==t['native_baseline_counts']==audit['counts']
            assert not audit['infrastructure_stop'] and audit['category']=='assertion_failure'
            assert z.read(root+'before.json')==z.read(root+'after.json') and load(root+'provenance.json')['verified'] and load(root+'cleanup.json')['complete']
            baseline.append(dict(task=t['instance_id'],TaskResult_sha256=sha(z.read(root+'official_result.json')),JUnit_sha256=sha(z.read(root+'phase2.junit.xml')),counts=audit['counts']))
        runs=[]
        for i,arm,cap in [(1,'A',16384),(2,'B',8192)]:
            root=f'results/runs/{i:02d}-ure_gpu03_owned-{arm}/'
            cfg=load(root+'runtime_config.json');native=load(root+'official_result.json');agent=load(root+'agent/agent_result.json');done=load(root+'worker_done.json')
            assert cfg['generation']['max_output_tokens']==cfg['budget']['output_tokens']==cap
            assert cfg['generation']['thinking_config']['thinking_budget']==4096 and cfg['generation']['seed']==17
            assert cfg['model_transport']=='CPU_SCRIPTED_ONLY' and not cfg['real_model']
            assert native['resolved'] and agent['patch_submitted'] and agent['patch_bytes']>0 and done['integrity_complete'] and done['cleanup_complete']
            assert load(root+'audit_result.json')['allow_next_run']
            assert counts(z.read(root+'verifier/phase2.junit.xml'))==dict(tests=1,failures=0,errors=0,skipped=0)
            wire=[json.loads(x) for x in z.read(root+'agent/http_wire.jsonl').splitlines()]
            requests=[e['body'] for e in wire if e['kind']=='http_request'];assert len(requests)==6
            assert all(b.get('max_completion_tokens',b.get('max_tokens'))==cap and b['thinking_token_budget']==4096 for b in requests)
            assert load(root+'HTTP_AUDIT.json')['passed']
            events=[json.loads(x) for x in z.read(root+'events.jsonl').splitlines()]
            guard=[e for e in events if e.get('kind')=='context_admission'];assert guard and all(e['output_reserved']==cap for e in guard)
            assert (z.read(root+'research_candidate/prompts/system.md')==z.read('source/u_re/v01/experiments/action_priority_01/candidate_action_v01/prompts/system.md'))
            runs.append(dict(policy=arm,output_cap=cap,resolved=True,TaskResult_sha256=sha(z.read(root+'official_result.json')),JUnit_sha256=sha(z.read(root+'verifier/phase2.junit.xml')),runtime_sha256=sha(z.read(root+'runtime_config.json')),HTTP_requests=6,guard_and_compiler_and_wire_equal=True,cleanup_complete=True))
        assert load('results/isolation/cleanup.json')['complete'] and load('results/CPU_TRANSPORT_PROOF.json')['both_policies_verified']
    return dict(status='V03_PAYLOAD_END_TO_END_CPU_PASS',attempt=attempt,Notebook_id=receipt['Notebook_id'],version=1,platform_status='COMPLETE',CPU_MODEL='SCRIPTED_ONLY',real_Gemma_requests=0,payload_sha256=manifest['payload_sha256'],all_production_file_hashes_match=True,raw_archive_path=str(archive),raw_archive_sha256=sha(archive.read_bytes()),raw_bytes=archive.stat().st_size,CRC_valid=True,baselines=baseline,synthetic_runs=runs,boundary_cases=checks,environment_unchanged=True,isolation_and_cleanup_passed=True)
if __name__=='__main__':
    import sys
    proof=audit_cpu(sys.argv[1],sys.argv[2]);write(HERE/'CPU_END_TO_END_ACCEPTANCE.json',proof);print(json.dumps(proof))
