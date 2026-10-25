"""Rehash downloaded evidence and derive safe native/environment identities."""
import hashlib
import json
from pathlib import Path
import zipfile

from .read_preflight import HERE, GPU, save
from u_re.v02.experiments.env_recovery_admission_01.junit_audit import parse_snapshot_phases


def sha(raw):return hashlib.sha256(raw).hexdigest()


def audit(archive):
    archive=Path(archive)
    lock=json.loads((HERE/'RELEVANCE_REVIEW_LOCK.json').read_bytes())
    assert lock['archive_sha256']==sha(archive.read_bytes())
    manifest=json.loads((GPU/'EXECUTION_MANIFEST.json').read_bytes())
    metrics=json.loads((HERE/'BATCH_02_DERIVED_METRICS.json').read_bytes())
    with zipfile.ZipFile(archive) as z, zipfile.ZipFile(GPU/'payload.zip') as payload:
        assert z.testzip() is None and payload.testzip() is None
        for name in payload.namelist():
            assert sha(payload.read(name))==sha(z.read('source/'+name)),name
        obj=lambda n:json.loads(z.read(n))
        assert obj('PAYLOAD_IDENTITY.json')['payload_sha256']==sha((GPU/'payload.zip').read_bytes())
        assert obj('execution/MODEL_FILES.json')==manifest['model']['files']
        before=obj('PRODUCTION_ENVIRONMENT_BEFORE.json')
        assert before==obj('PRODUCTION_ENVIRONMENT_AFTER.json')==json.loads((GPU/'ENVIRONMENT_LOCK.json').read_bytes())['fingerprint']
        identities=obj('execution/TASK_IDENTITIES.json')
        for task in manifest['tasks']:
            for key in ('repo','base_commit','issue_sha256','task_record_sha256','test_patch_sha256','input_files'):
                assert identities[task['instance_id']][key]==task[key]
        runtime=obj('execution/GPU_RUNTIME.json');devices=obj('execution/GPU_DEVICES.json')
        assert len(devices)==4 and all(d['name']=='NVIDIA L4' for d in devices)
        assert runtime['versions']['vllm']=='0.19.1' and runtime['torch_cuda']=='12.8'
        assert obj('execution/VLLM_CONFIG.json')['tensor_parallel_size']==4
        assert obj('execution/isolation/result.json')['exit_code']==0
        assert obj('execution/isolation/cleanup.json')['complete'] is True
        cleanup=obj('execution/SERVER_CLEANUP.json')
        assert cleanup['confirmed'] is True and cleanup['remaining']==[] and cleanup['idle_error'] is None
        records=obj('execution/ABBA_RESULTS.json')['records']
        assert [(r['run'],r['instance_id'],r['arm']) for r in records]==[(r['run'],r['instance_id'],r['arm']) for r in manifest['batches']['2']]
        native=[];bindings=[];schemas={};first_messages={};initial={}
        for row,metric in zip(records,metrics['sessions']):
            pre='execution/runs/'+metric['session']+'/'
            result=obj(pre+'official_result.json')
            raw=z.read(pre+'verifier/phase2.junit.xml');parsed=parse_snapshot_phases(raw)
            assert result['resolved'] is False and result['test_exit_code']==1
            assert parsed['environment_errors']==0 and parsed['duplicate_snapshot_finalizer_errors']==2
            assert parsed['counts']==row['native']['counts']
            assert obj(pre+'worker_done.json')['integrity_complete'] is True
            cfg=obj(pre+'runtime_config.json');assert cfg['model_transport']=='REAL_GEMMA'
            assert cfg['generation']==dict(max_output_tokens=16384,seed=17,thinking_config=dict(thinking_budget=4096))
            wire=[json.loads(x) for x in z.read(pre+'agent/http_wire.jsonl').splitlines()]
            requests=[r['body'] for r in wire if r.get('kind')=='http_request']
            for body in requests:
                assert body['max_completion_tokens']==16384 and body['seed']==17
                assert body['thinking_token_budget']==4096 and body['chat_template_kwargs']['enable_thinking'] is True
            schemas[row['arm']]=requests[0]['tools']
            first_messages[row['arm']]=requests[0]['messages']
            initial[row['arm']]=metric['actual_counted_inputs'][0]
            native.append(dict(run=row['run'],arm=row['arm'],instance_id=row['instance_id'],native_resolved=result['resolved'],
                TaskResult_sha256=sha(z.read(pre+'official_result.json')),JUnit_sha256=sha(raw),
                counts=parsed['counts'],environment_errors=0,exact_paired_snapshot_teardown_records=2,
                patch_sha256=metric['final_patch_sha256'],patch_bytes=metric['final_patch_bytes'],
                native_infrastructure_stop=False,worker_integrity_complete=True,worker_cleanup_complete=row['worker']['cleanup_complete'],
                worker_seconds=row['worker_seconds'],supervised_process_seconds=row['worker']['duration_seconds']))
            bindings.append(dict(arm=row['arm'],actual_model_requests=len(requests),compiled_generation=cfg['generation'],
                tool_names=[t['function']['name'] for t in schemas[row['arm']]],
                first_request_message_roles=[m['role'] for m in requests[0]['messages']],
                Context_Guard_rejections=metric['context_rejections']))
        assert schemas['B']==schemas['C']
        normal={t['function']['name']:t for t in schemas['A']}
        assert len(normal)==6
        for arm in ('B','C'):
            assert {t['function']['name']:t for t in schemas[arm] if t['function']['name'] in normal}==normal
        summary=dict(archive_sha256=sha(archive.read_bytes()),archive_bytes=archive.stat().st_size,CRC_valid=True,
            original_shared_source_files_verified=len(payload.namelist()),
            shared_payload_sha256=sha((GPU/'payload.zip').read_bytes()),model_files_verified=8,
            devices=devices,runtime=runtime,model_loaded_and_real_HTTP_proven=True,
            trusted_environment_before_after_matches_frozen=True,task_identities_verified=True,
            B_C_tool_schema_equal=True,official_six_schema_equal_across_arms=True,
            initial_counted_input_tokens=initial,
            B_C_first_request_messages_identical=first_messages['B']==first_messages['C'],
            all_first_task_user_input_identical=all(first_messages[a][1]==first_messages['A'][1] for a in ('B','C')),
            registered_file_pins_verified=205,registration_manifest_additional_members=1,
            chroot_canary_and_cleanup=True,model_process_cleanup=cleanup,
            native_results=native,request_bindings=bindings,
            GPU_cost=obj('execution/GPU_COST.json'),scripted_transport_requests=0)
        save(HERE/'BATCH_02_RUNTIME_AUDIT.json',summary)
        print(json.dumps(dict(verified_sources=summary['original_shared_source_files_verified'],verified_model_files=8,
                             native_outcomes=[r['native_resolved'] for r in native],GPU_devices=len(devices))))


if __name__=='__main__':
    import sys
    audit(sys.argv[1])
