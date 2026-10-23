"""Derive acceptance from actual version/source-bound raw CPU outputs."""
import json, zipfile
from pathlib import Path
from .common import HERE, ROOT, sha, write, CONTROL_SHA
from u_re.v03.experiments.context_budget_01.audit import counts

def audit_cpu(archive, attempt):
    archive=Path(archive).resolve(); assert not archive.is_relative_to(ROOT)
    directory=HERE/attempt
    receipt=json.loads((directory/'execution/HTTP_RECEIPT.json').read_bytes())
    output=json.loads(sorted((directory/'read_observations').glob('read-*/OUTPUT_MANIFEST.json'))[-1].read_bytes())
    item=next(f for f in output['files'] if f['file']=='v04-'+attempt+'.zip')
    assert output['status']=='COMPLETE' and output['version_bound_before_after'] and item['complete']
    assert item['Notebook_id']==receipt['Notebook_id'] and item['version']==receipt['accepted_version']==1
    assert sha(archive.read_bytes())==item['sha256']
    manifest=json.loads((HERE/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())
    lock=json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    prompt_lock=json.loads((HERE/'CANDIDATE_BUILD_MANIFEST.json').read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        load=lambda n:json.loads(z.read(n))
        assert load('PAYLOAD_IDENTITY.json')['payload_sha256']==manifest['payload_sha256']
        for n,h in manifest['files'].items(): assert sha(z.read('source/'+n))==h, n
        acceptance=load('results/CPU_ACCEPTANCE.json')
        assert acceptance['status']=='V04_EGR_PAYLOAD_END_TO_END_CPU_PASS'
        assert acceptance['CPU_MODEL']=='SCRIPTED_ONLY' and acceptance['real_Gemma_requests']==0
        assert acceptance['owned_scripted_runs']==2 and acceptance['HTTP_requests']==14 and acceptance['cleanup_complete']
        before=load('PRODUCTION_ENVIRONMENT_BEFORE.json')
        assert before==load('PRODUCTION_ENVIRONMENT_AFTER.json')
        assert before==json.loads((ROOT/'u_re/v02/experiments/env_recovery_admission_01/V02B_ENVIRONMENT_LOCK.json').read_bytes())['fingerprint']
        baseline=[]
        for task in lock['tasks']:
            root='results/baselines/'+task['instance_id']+'/'
            result=load(root+'official_result.json'); audit=load(root+'audit.json')
            assert not result['resolved'] and result['test_exit_code']==1
            assert counts(z.read(root+'phase2.junit.xml'))==task['native_baseline_counts']==audit['counts']
            assert not audit['infrastructure_stop'] and audit['category']=='assertion_failure'
            assert z.read(root+'before.json')==z.read(root+'after.json')
            assert load(root+'provenance.json')['verified'] and load(root+'cleanup.json')['complete']
            baseline.append(dict(task=task['instance_id'],role='DEVELOPMENT_ONLY_ENVIRONMENT_RECHECK',TaskResult_sha256=sha(z.read(root+'official_result.json')),JUnit_sha256=sha(z.read(root+'phase2.junit.xml')),counts=audit['counts']))
        runs=[]
        for number,arm in ((1,'A'),(2,'B')):
            root=f'results/runs/{number:02d}-ure_gpu03_owned-{arm}/'
            config=load(root+'runtime_config.json'); native=load(root+'official_result.json')
            agent=load(root+'agent/agent_result.json'); done=load(root+'worker_done.json')
            proof=load(root+'COMPILED_PROMPT_EVIDENCE.json')
            expected_prompt='source/'+('u_re/v01/experiments/action_priority_01/candidate_action_v01/prompts/system.md' if arm=='A' else 'u_re/v04/experiments/evidence_guided_repair_01/candidate_egr_v04/prompts/system.md')
            assert proof['instruction_sha256']==sha(z.read(expected_prompt))
            assert proof['candidate_sha256']==(CONTROL_SHA if arm=='A' else prompt_lock['treatment_ZIP_sha256'])
            assert proof['instruction_visible_in_all_actual_HTTP_requests'] and proof['actual_HTTP_requests']==7
            assert proof['compiled'] and all(c['agent_class']=='LlmAgent' for c in proof['compiled'])
            generation=dict(max_output_tokens=16384,seed=17,thinking_config=dict(thinking_budget=4096))
            assert all(c['generation']==generation for c in proof['compiled'])
            assert config['generation']['max_output_tokens']==config['budget']['output_tokens']==16384
            assert {k:config['budget'][k] for k in ('agent_seconds','tool_budget','command_seconds','thinking_budget','seed')}==dict(agent_seconds=300,tool_budget=60,command_seconds=120,thinking_budget=4096,seed=17)
            assert config['model_transport']=='CPU_SCRIPTED_ONLY' and not config['real_model']
            assert native['resolved'] and agent['patch_submitted'] and agent['patch_bytes']>0
            assert done['integrity_complete'] and done['cleanup_complete'] and load(root+'audit_result.json')['allow_next_run']
            assert counts(z.read(root+'verifier/phase2.junit.xml'))==dict(tests=1,failures=0,errors=0,skipped=0)
            wire=[json.loads(x) for x in z.read(root+'agent/http_wire.jsonl').splitlines()]
            requests=[e['body'] for e in wire if e['kind']=='http_request']
            assert len(requests)==7 and all(b.get('max_completion_tokens',b.get('max_tokens'))==16384 and b['thinking_token_budget']==4096 and b['seed']==17 for b in requests)
            assert load(root+'HTTP_AUDIT.json')['passed']
            events=[json.loads(x) for x in z.read(root+'events.jsonl').splitlines()]
            guards=[e for e in events if e.get('kind')=='context_admission']
            assert guards and all(e['output_reserved']==16384 for e in guards)
            adk=[json.loads(x) for x in z.read(root+'agent/adk_events.jsonl').splitlines()]
            tools={p['function_response']['name'] for e in adk for p in e.get('event',{}).get('content',{}).get('parts',[]) if p.get('function_response')}
            assert tools=={'get_status','run_command','read_file','edit_file','write_file','submit_patch'}
            assert b'owned-scratch.txt' not in z.read(root+'final.patch')
            runs.append(dict(candidate=arm,instruction_sha256=proof['instruction_sha256'],tools_schema_sha256=proof['tools_schema_sha256'],generation=generation,budget=config['budget'],CPU_MODEL='SCRIPTED_ONLY',resolved=True,patch_bytes=agent['patch_bytes'],TaskResult_sha256=sha(z.read(root+'official_result.json')),JUnit_sha256=sha(z.read(root+'verifier/phase2.junit.xml')),HTTP_requests=7,six_tools_executed=True,cleanup_complete=True))
        assert runs[0]['instruction_sha256']!=runs[1]['instruction_sha256']
        assert runs[0]['tools_schema_sha256']==runs[1]['tools_schema_sha256'] and runs[0]['generation']==runs[1]['generation']
        assert load('results/isolation/cleanup.json')['complete']
        isolation=load('results/isolation/result.json')
        assert isolation['exit_code']==0 and 'INTEGRATED_CANARY_AND_DEPENDENCIES_OK' in isolation['stdout']
        assert load('results/CPU_TRANSPORT_PROOF.json')['both_candidates_verified']
    return dict(status='V04_EGR_CPU_READY',attempt=attempt,Notebook_id=receipt['Notebook_id'],version=1,platform_status='COMPLETE',CPU_MODEL='SCRIPTED_ONLY',real_Gemma_requests=0,payload_sha256=manifest['payload_sha256'],all_production_file_hashes_match=True,raw_archive_path=str(archive),raw_archive_sha256=sha(archive.read_bytes()),raw_bytes=archive.stat().st_size,CRC_valid=True,baselines=baseline,synthetic_runs=runs,environment_unchanged=True,isolation_and_cleanup_passed=True,GPU_authorized=False,algorithmic_effect='NOT_EVALUATED')

if __name__=='__main__':
    import sys
    proof=audit_cpu(sys.argv[1],sys.argv[2]); write(HERE/'CPU_END_TO_END_ACCEPTANCE.json',proof); print(json.dumps(proof))
