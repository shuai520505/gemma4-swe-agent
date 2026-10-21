"""Audit the already downloaded, owned synthetic CPU evidence. No execution."""
import hashlib
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()

def expected_cancel(result,cleanup):
    rows=result['HTTP_audit']['rows']
    cancelled=[r for r in rows if r['terminal_status']=='cancelled']
    return (result.get('external_cancellation_propagated') is True and result.get('HTTP_cancelled') is True
        and result['HTTP_audit']['reasons']==['unexplained_cancellation']
        and len(cancelled)==1 and cancelled[0]['usage'] is None and not cancelled[0]['usage_complete']
        and cleanup.get('complete') is True and cleanup.get('leftover_sandboxes')==0)

def audit(path):
    path=Path(path);summary={};members={};seen=set();feedback=False
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        original_manifest=json.loads(z.read('evidence_manifest.json'))
        for n,entry in original_manifest.items():
            raw=z.read(n)
            assert sha(raw)==entry['sha256'] and len(raw)==entry['bytes']
        registration=json.loads(z.read('source/cpu_registration.json'))
        for n,h in registration['files'].items():assert sha(z.read('source/'+n))==h
        assert sha(z.read('source/u_re/v01/submission_noegv.zip'))=='2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608'
        for n in z.namelist():
            raw=z.read(n);members[n]=dict(bytes=len(raw),sha256=sha(raw))
        for case in ('basic','closed_loop','wrong_test','exact_tools','external_cancel'):
            prefix=f'validation/cases/{case}/'
            raw=json.loads(z.read(prefix+'case_result.json'));cleanup=json.loads(z.read(prefix+'cleanup.json'))
            boundary=json.loads(z.read(prefix+'boundary.json'))
            assert boundary['budget_seconds']==300 and boundary['tools_limit']==60 and boundary['command_seconds']==120
            assert cleanup['complete'] and cleanup['leftover_sandboxes']==0
            wire=raw['wire_configuration']
            assert all((r['output'],r['thinking'],r['seed'],r['sampling'])==(16384,4096,17,{}) for r in wire)
            events=[json.loads(s) for s in z.read(prefix+'adk_events.jsonl').decode().splitlines()]
            for e in events:
                for part in e.get('event',{}).get('content',{}).get('parts',[]):
                    if part.get('function_response'):seen.add(part['function_response']['name'])
            requests=[json.loads(s) for s in z.read(prefix+'request_snapshots.jsonl').decode().splitlines()]
            feedback|=any(m.get('role')=='tool' for r in requests for m in r['body']['messages'])
            summary[case]=dict(counted_tools=raw['counted_tools'],successful_submits=raw['successful_submits'],
                native_HTTP_audit_passed=raw['HTTP_audit']['passed'],cleanup_complete=True,
                counterexample_revision_retest=raw['counterexample_revision_retest'],
                expected_synthetic_cancellation=expected_cancel(raw,cleanup) if case=='external_cancel' else None,
                outcome='SCRIPT_ASSERTION_FAILED' if case=='external_cancel' else 'PASS',
                evidence={n:members[n] for n in (prefix+'case_result.json',prefix+'cleanup.json',prefix+'boundary.json')})
        assert len(seen)==6 and feedback
        summary.update(post_submit_negative=dict(outcome='NOT_RUN'),native_toy_verifier=dict(outcome='NOT_RUN'))
        gate_present='validation/CPU_INTERFACE_GATE.json' in z.namelist()
        assert not gate_present
        result=dict(Notebook_id=140042899,version=1,platform_status='ERROR',archive=dict(filename=path.name,
            bytes=path.stat().st_size,sha256=sha(path.read_bytes()),CRC_valid=True,members=len(members),
            original_manifest_entries_verified=len(original_manifest),registered_sources_verified=len(registration['files'])),
            official_compiler_loaded_noegv=True,tools_with_real_responses=sorted(seen),tool_feedback_in_next_request=feedback,
            checks=summary,full_CPU_gate_passed=False,native_TaskResult='NOT_RUN',native_JUnit='NOT_RUN',
            root_cause='New wrapper wrongly required the production deadline cancellation audit to pass for a deliberately externally-cancelled mock fixture. Original tools/Runner propagated cancellation and cleaned sandboxes; this is not a Gemma failure.',
            correction_status='OFFLINE_CONFIRMED_FIXTURE_PREDICATE; corrected future script NOT_REEXECUTED',
            GPU=False,Gemma_inference=False,competition_task_executed=False)
    (HERE/'cpu01/ARCHIVE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (HERE/'cpu01/OUTPUT_MEMBER_HASHES.json').write_text(json.dumps(members,indent=2)+'\n',encoding='utf-8')
    # Keep originals private; only this owned log, which contains no competition data, is copied for the failure record.
    with zipfile.ZipFile(path) as z:
        (HERE/'cpu01/OFFICIAL_CPU_FAILURE.log').write_bytes(z.read('cpu.log'))
    print(json.dumps({k:result[k] for k in ('Notebook_id','platform_status','tools_with_real_responses','full_CPU_gate_passed')}))

if __name__=='__main__':
    import sys
    audit(sys.argv[1])
