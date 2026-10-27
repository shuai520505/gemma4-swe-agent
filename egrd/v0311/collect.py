"""Independently verify the completed CPU archive and publish safe derivatives."""
import json
from pathlib import Path
import zipfile

from jsonschema import Draft202012Validator

from .prepare import HERE, OLD, ROOT, PRIVATE, S0_SHA, REF, BASE, sha, write, arm_input, verify_history
from .boundary_audit import compare


def collect():
    verify_history()
    path=PRIVATE/'range-download/egrd-v0311-cpu-v1.zip'
    body=path.read_bytes();build=json.loads((HERE/'CPU_BUILD.json').read_bytes())
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        read=lambda name:json.loads(archive.read(name))
        for name,digest in build['members'].items():
            assert sha(archive.read('source/'+name))==digest,name
        manifest=read('evidence_manifest.json')
        for name,identity in manifest.items():
            raw=archive.read(name)
            assert len(raw)==identity['bytes'] and sha(raw)==identity['sha256'],name
        assert read('PAYLOAD_IDENTITY.json')['payload_sha256']==build['payload_sha256']
        device=read('DEVICE_ACCEPTANCE.json')
        assert device['status']=='NULL_DEVICE_PASS' and device['cleanup'] and not device['fallback_executed']
        assert device['stat']['character_device'] and (device['stat']['major'],device['stat']['minor'])==(1,3)
        assert not device['stat']['regular_file'] and not device['stat']['symlink']
        assert device['child']['returncode']==0 and device['host_read_write']
        result=read('results/CPU_TEST_RESULTS.json')
        assert result['status']=='CPU_PREFLIGHT_PASS' and result['GPU']==result['real_Gemma_requests']==0
        assert result['SDK']==json.loads((ROOT/'egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json').read_bytes())['SDK']
        original=read('source/egrd/v031/private/original_task.json')['problem_statement']
        receipt=read('source/egrd/v031/EVIDENCE_RECEIPT.json')
        suffix=arm_input(original,receipt,'B')[len(original):]
        raw_requests={arm:archive.read(f'results/{arm}/model-boundary/request_001.json') for arm in ('A','B')}
        boundary,diff=compare(raw_requests['A'],raw_requests['B'],original,suffix)
        assert boundary==read('results/INPUT_BOUNDARY_AUDIT.json') and boundary['only_supplement_differs']
        assert sha(archive.read('results/RENDERED_INPUT_DIFF.txt'))==sha(diff.encode())
        for name in ('DEVICE_ACCEPTANCE.json','CPU_TEST_RESULTS.json','INPUT_BOUNDARY_AUDIT.json'):
            direct=next((PRIVATE/'compact-output').rglob(name))
            archived=archive.read(name if name=='DEVICE_ACCEPTANCE.json' else 'results/'+name)
            assert direct.read_bytes()==archived,name
        records=[];trusted=[];sessions=[]
        for arm,summary in zip(('A','B'),result['records']):
            assert summary['arm']==arm and summary['full_compiler'] and summary['agent_cleanup']
            assert summary['package_sha256']==S0_SHA and summary['patch_submitted'] and summary['git_diff_check']
            config=read(f'results/{arm}/COMPILED_CONFIGURATION.json')
            assert config['generation']==summary['generation']
            prompt_bytes=archive.read(f'results/{arm}/candidate/prompts/system.md')
            # The frozen member has 13 CRLFs; the native loader reads text with
            # universal newline handling. Do not rewrite the historical bytes.
            assert config['instruction_sha256']==sha(prompt_bytes.replace(b'\r\n',b'\n'))
            for name,digest in json.loads((OLD/'S0_AGENT_LOCK.json').read_bytes())['members'].items():
                assert sha(archive.read(f'results/{arm}/candidate/'+name))==digest
            calls=read(f'results/{arm}/SCRIPTED_HTTP_REQUESTS.json')
            captured=[n for n in archive.namelist() if n.startswith(f'results/{arm}/model-boundary/request_') and n.endswith('.json')]
            assert len(calls)==len(captured)==summary['scripted_requests']==11
            for index,request in enumerate(calls,1):
                assert json.loads(archive.read(f'results/{arm}/model-boundary/request_{index:03d}.json'))==request
            events=[json.loads(row) for row in archive.read(f'results/{arm}/agent/adk_events.jsonl').splitlines()]
            responses=[p['function_response'] for e in events for p in e.get('event',{}).get('content',{}).get('parts',[]) if p.get('function_response')]
            assert sorted({r['name'] for r in responses})==sorted(summary['compiled_tools'])
            assert len(summary['compiled_tools'])==6
            submit=[r for r in responses if r['name']=='submit_patch']
            assert len(submit)==1 and submit[0]['response']['status']=='ok'
            assert sha(json.dumps(submit,sort_keys=True).encode())==summary['native_submit_response_sha256']
            native_patch=archive.read(f'results/{arm}/submitted.patch')
            assert sha(native_patch)==summary['patch_sha256'] and native_patch
            assert native_patch.count(b'diff --git ')==1
            assert native_patch.startswith(b'diff --git a/django/contrib/auth/forms.py b/django/contrib/auth/forms.py')
            assert b'EGRD_SCRIPTED_ONLY_TRANSPORT_MARKER' in native_patch
            assert 'AGENT_FILESYSTEM_ISOLATION_PASS' in json.dumps(responses)
            assert summary['path_read_write_attacks_denied'] and summary['no_evaluator_content_in_requests']
            evaluation=read(f'results/{arm}/trusted-postedit/DEVELOPMENT_RESULT.json')
            assert evaluation==summary['development_result']
            for key in ('patch_applicable','source_changed_from_original','Python_AST_unchanged',
                        'original_failing_probe_still_fails','positive_controls_passed','trusted_probe_write_denied',
                        'trusted_probe_unchanged','tests_did_not_change_source','cleanup'):
                assert evaluation[key] is True,(arm,key)
            assert evaluation['production_behavior_changed'] is False and evaluation['repair_success'] is False
            assert evaluation['bounded_regression']['exit_code']==0
            checks=evaluation['target_receipt']['checks']
            assert len(checks)==4 and sum(c['passed'] for c in checks)==3
            assert checks[-1]['expected']==1 and checks[-1]['actual']==0 and not checks[-1]['passed']
            assert evaluation['probe_program_sha256']==json.loads((OLD/'TASK_IDENTITY_LOCK.json').read_bytes())['probe_sha256']
            registry=read(f'results/{arm}/agent/roots/owned_uids.json')
            sessions.extend((arm,row['sid']) for row in registry['entries'])
            record={k:summary[k] for k in ('arm','package_sha256','full_compiler','compiled_tools','generation',
                'instruction_sha256','scripted_requests','charged_tools','agent_seconds','worker_seconds','patch_submitted',
                'patch_sha256','git_diff_check','agent_cleanup','actual_model_tokens','official_native_resolved','canonical_swebench_resolved')}
            record.update(status='SCRIPTED_CPU_PASS',patch_bytes=len(native_patch),isolation=True,
                          prompt_original_CRLF_count=prompt_bytes.count(b'\r\n'),
                          instruction_loading='Native text read normalizes CRLF to LF; original member unchanged',
                          initial_request_sha256=sha(raw_requests[arm]),initial_request_bytes=len(raw_requests[arm]))
            records.append(record)
            trusted.append(dict(arm=arm,patch_sha256=summary['patch_sha256'],patch_applicable=True,
                original_source_sha256=evaluation['original_source_sha256'],tested_source_sha256=evaluation['tested_source_sha256'],
                probe_program_sha256=evaluation['probe_program_sha256'],changed_production_files=evaluation['changed_production_files'],
                Python_AST_unchanged=True,production_behavior_changed=False,repair_success=False,
                target_classification=evaluation['target_receipt']['classification'],target_exit_code=evaluation['diagnostic']['exit_code'],
                expected_related_count=1,observed_related_count=0,positive_controls_passed=3,target_assertions_failed=1,
                bounded_regression_exit_code=0,probe_unchanged=True,tests_did_not_change_source=True,
                trusted_probe_write_denied=True,cleanup=True,official_native_resolved=None,canonical_swebench_resolved=None))
        assert len({sid for arm,sid in sessions})==len(sessions)
        assert records[0]['generation']==records[1]['generation']
        assert records[0]['instruction_sha256']==records[1]['instruction_sha256']
        assert records[0]['patch_sha256']==records[1]['patch_sha256']
        gates={key:True for key in ('null_device','Git','S0_identity','task_identity','A_Compiler','B_Compiler','A_tools','B_tools',
            'native_submit','patch_applicability','A_boundary','B_boundary','isolation','trusted_evaluator','cleanup','zero_GPU','zero_real_Gemma')}
        public=dict(status='EGRD_V0311_CPU_READY_GPU_NOT_AUTHORIZED',CPU_MODEL='SCRIPTED_ONLY',GPU=0,
            real_Gemma_requests=0,formal_submissions=0,Notebook_id=141087018,Notebook_version=1,
            gates=gates,records=records,SDK=result['SDK'],model_authorization=False,
            historical_serving_equivalence='HISTORICAL_SERVING_EQUIVALENCE_UNVERIFIED',
            task_input_bytes={'A':559,'B':2134},task_supplement_bytes=1575,
            token_overhead=None,total_scripted_HTTP_requests=sum(r['scripted_requests'] for r in records),
            boundary=boundary,engineering_readiness=True,algorithm_efficacy='NOT_TESTED',
            all_new_CPU_evidence=True,old_partial_results_not_reused_for_gates=True)
        Draft202012Validator(json.loads((HERE/'CPU_RUNNER_RESULTS.schema.json').read_bytes())).validate(public)
        write(HERE/'CPU_RUNNER_RESULTS.json',public)
        write(HERE/'TRUSTED_POST_EDIT_RESULTS.json',dict(CPU_MODEL='SCRIPTED_ONLY',records=trusted,
             evaluator_scope='OWNED_DEVELOPMENT_CHECKS_NOT_NATIVE_OR_CANONICAL_SWEBENCH',complete_correctness='UNKNOWN'))
        write(HERE/'DEVICE_RESULT.json',device)
        write(HERE/'BOUNDARY_COMPARISON.json',boundary)
        write(HERE/'RAW_ARCHIVES.json',dict(path=str(path),sha256=sha(body),bytes=len(body),CRC='ALL_MEMBERS_PASS',
            manifest_files_verified=len(manifest),all_uploaded_source_members_match=True,
            payload_sha256=build['payload_sha256'],raw_model_bodies_private=True,
            original_CLI_download='IncompleteRead; original zero-byte file/error preserved',
            recovery='Read-only official output-list API plus bounded HTTP byte ranges; no redispatch',
            prior_V031_failures='Unchanged; separately hash/CRC checked by verify_history'))
    metadata=json.loads((PRIVATE/'actual-ref/kernel-metadata.json').read_bytes())
    status=(PRIVATE/'cli/status-05/stdout.txt').read_text(encoding='utf8')
    assert 'KernelWorkerStatus.COMPLETE' in status
    assert metadata['id_no']==141087018 and not metadata['enable_gpu'] and not metadata['enable_tpu'] and metadata['is_private']
    assert (PRIVATE/'CPU_DISPATCH.json').is_file() and not (PRIVATE/'CPU_DISPATCH_V2.json').exists()
    write(HERE/'KAGGLE_CPU_EXECUTION_RECORD.json',dict(ref=REF,Notebook_id=141087018,version=1,status='COMPLETE',
        actual_executions=1,dispatch_attempts=1,CPU_only=True,private=True,GPU=0,TPU=0,real_Gemma_requests=0,
        model_weights_loaded=False,formal_submissions=0,base_commit=BASE,Notebook_sha256=build['Notebook_sha256'],
        payload_sha256=build['payload_sha256'],metadata_sha256=sha((PRIVATE/'actual-ref/kernel-metadata.json').read_bytes()),
        remote_cell_sources_match=True,docker_image=metadata['docker_image'],
        data_sources=metadata['dataset_sources'],model_sources=[],competition_sources=[],
        CLI_version='2.2.2',read_only_recovery=True,version_suffixed_pull='403; ordinary-ref read-only pull succeeded',
        authorization='Owner EGRD V0.3.1.1 instruction; one additional CPU execution only',
        future_GPU_authorized=False,source_dataset='Private existing development Dataset V2; no mutation'))
    print(public['status'], '; 17 observed gates PASS; 22 SCRIPTED_ONLY HTTP requests; zero real Gemma.')


if __name__=='__main__':collect()
