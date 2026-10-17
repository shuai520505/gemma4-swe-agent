"""Verify original archives and freeze the stopped study's eight-slot accounting."""
import hashlib
import json
from pathlib import Path
import zipfile
from cure.build import write_new
from cure.runner import require_gate
from harness_v2.integrity import verify_baseline


def finalize():
    repo=Path(__file__).resolve().parents[2]; base=repo/'cure/gpu-study-01'
    sha=lambda b:hashlib.sha256(b).hexdigest()
    plan=json.loads((base/'protocol.json').read_text())
    gate=require_gate(repo/'cure/results/cpu-r03/cpu_gate.json',repo)
    assert sha((base/'protocol.json').read_bytes())=='5a4c237f3ec7c5f7dd9927769b283831a024317192f47efe8bf9a5144c8bbbb5'
    original=json.loads((repo/'cure/results/delivery-manifest.json').read_text())
    for name,digest in original.items(): assert sha((repo/name).read_bytes())==digest,name
    for name,digest in plan['runtime_source_hashes'].items(): assert sha((repo/name).read_bytes())==digest,name
    archive_reports=[]
    for kind in ('cpu','cpu-r02','smoke'):
        d=base/'results'/kind
        collection=json.loads((d/'collection.json').read_text())
        archive=d/'evidence.zip'
        assert sha(archive.read_bytes())==collection['archive_sha256']
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            inventory=json.loads((d/'archive-members.json').read_text())
            for name,meta in inventory.items():
                content=z.read(name)
                assert len(content)==meta['bytes'] and sha(content)==meta['sha256'],name
                if (d/name).is_file(): assert (d/name).read_bytes()==content,name
            manifest=json.loads(z.read('evidence_manifest.json'))
            for name,meta in manifest.items():
                raw=z.read(name)
                assert len(raw)==meta['bytes'] and sha(raw)==meta['sha256'],name
            if kind=='smoke':
                for arm,candidate in plan['candidates'].items():
                    raw=z.read('source/cure/packages/'+arm+'/submission.zip')
                    assert sha(raw)==candidate['zip_sha256']
                assert sha(z.read('source/study/protocol.json'))==sha((base/'protocol.json').read_bytes())
                for name in z.namelist():
                    if name.startswith('runs/') and name.endswith('.zip'):
                        import io
                        with zipfile.ZipFile(io.BytesIO(z.read(name))) as nested:
                            assert nested.testzip() is None
                            nested_manifest=json.loads(nested.read('evidence_manifest.json'))
                            for member,meta in nested_manifest.items():
                                raw=nested.read(member)
                                assert len(raw)==meta['bytes'] and sha(raw)==meta['sha256']
        archive_reports.append(collection)
    smoke=base/'results/smoke'
    batch=json.loads((smoke/'batch_gate.json').read_text()); assert batch['infrastructure_passed'] is False
    all_rows=[r for rows in plan['batches'].values() for r in rows]
    slots=[]
    for row in all_rows:
        path=smoke/'runs'/f"{row['index']:02d}-{row['task_id']}-{row['arm']}"
        if not path.exists():
            slots.append(dict(index=row['index'],task_id=row['task_id'],arm=row['arm'],status='not_run',reason='Global stop after slot 2 instruction rendering error'))
            continue
        audit=json.loads((path/'mechanism_audit.json').read_text())
        official=audit['official']; controller=audit['controller']
        events=[json.loads(x) for x in (path/'events.jsonl').read_text().splitlines()]
        agent_time=next(e['agent_elapsed_seconds'] for e in events if 'agent_elapsed_seconds' in e)
        slots.append(dict(index=row['index'],task_id=row['task_id'],arm=row['arm'],
            status=controller['status'],official_resolved=official['resolved'],official_error=official['error_message'],
            official_test_exit_code=official['test_exit_code'],official_llm_calls=official['total_llm_calls'],
            official_tool_calls=official['tool_calls'],official_total_tokens=official['total_tokens'],
            http_llm_calls=audit['model_requests'],observed_tool_calls_including_submit=audit['tool_calls'],
            actual_server_usage=audit['usage'],agent_seconds=agent_time,official_seconds=official['duration_seconds'],
            worker_seconds=controller['duration_seconds'],infrastructure_passed=audit['infrastructure_passed'],
            phase2_ran=(path/'phase2_execution.json').is_file(),patch_bytes=(path/'latest.patch').stat().st_size,
            process_tree_stopped=controller['process_tree_stopped'],cleanup_complete=controller['cleanup_complete'],
            audited_failure_stage='agent_instruction_preprocess' if row['index']==2 else None))
    b=smoke/'runs/01-lumen_interface_01-checklist'
    wire=[json.loads(x) for x in (b/'http_wire.jsonl').read_text().splitlines()]
    requests=[x['body'] for x in wire if x['kind']=='http_request']
    responses=[x['body'] for x in wire if x['kind']=='http_response']
    task=json.loads((base/'data/tasks.jsonl').read_text().splitlines()[0])
    issue=task['problem_statement']
    assert all(any(issue in m.get('content','') for m in r['messages'] if m['role']=='user' and isinstance(m.get('content'),str)) for r in requests)
    def strings(value):
        if isinstance(value,str): yield value
        elif isinstance(value,dict):
            for child in value.values(): yield from strings(child)
        elif isinstance(value,list):
            for child in value: yield from strings(child)
    model_strings=[s for r in requests for s in strings(r)]
    assert not any(task['test_patch'] in s for s in model_strings)
    assert not any(marker in s for s in model_strings for marker in ('def test_new_entry','def test_preserved_entry'))
    # Native responses use reasoning; LiteLLM normalizes it to reasoning_content in outbound history.
    history_reasoning=sum(any(m.get('reasoning_content') for m in r['messages'] if m['role']=='assistant') for r in requests)
    response_reasoning=sum(bool(r['choices'][0]['message'].get('reasoning')) for r in responses)
    for r in requests:
        for m in r['messages']:
            if m['role']=='tool': assert isinstance(json.loads(m['content']),dict)
    identity=json.loads((smoke/'model_identity.json').read_text())
    assert identity['manifest_sha256']==sha(json.dumps(identity['files'],sort_keys=True).encode())
    assert json.loads((smoke/'wheel_hashes.json').read_text())==plan['wheel_hashes']
    report=dict(experiment_id=plan['experiment_id'],globally_stopped=True,
        reason='CURE frozen literal {JSON} fails ADK instruction state substitution before first LLM request',
        slots=slots,complete_evaluable_pairs=0,mechanism_effect='not_evaluable',kaggle_resolution_rate=None,
        official_public_submission_created=False,frozen_baseline_files_verified=verify_baseline(),
        original_cure_manifest_files_verified=len(original),registered_cpu_sources_verified=len(gate['source_hashes']),
        protocol_sha256=sha((base/'protocol.json').read_bytes()),archives=archive_reports,
        b_request_semantics=dict(all_issue_bodies_preserved=True,hidden_test_patch_absent=True,
            response_reasoning_messages=response_reasoning,outbound_requests_with_retained_reasoning=history_reasoning,
            tools_single_json_encoding_verified=True,output_cap=8192,thinking_budget=4096,seed=17,
            model_manifest_sha256=identity['manifest_sha256']),
        limits='No C model inference. No estimate of C decision ability, repair gain or extra investigation cost. Native official fields preserved; zero official B tokens is a placeholder, use actual HTTP usage.')
    write_new(base/'summary.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(report,indent=2))


if __name__=='__main__':finalize()
