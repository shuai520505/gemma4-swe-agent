"""Derive safe CPU results from the original version-bound private archive."""
import json
from pathlib import Path
import zipfile

from .prepare import HERE,ROOT,PRIVATE,S0_SHA,sha,write




def collect_blocked():
    """Preserve the actual failed versions and partial gates; no success backfill."""
    remote=json.loads((PRIVATE/'remote-notebook-v2/kernel-metadata.json').read_bytes())
    assert remote['id_no']==141014201 and remote['is_private'] is True
    assert remote['enable_gpu'] is False and remote['enable_tpu'] is False and remote['enable_internet'] is False
    assert not remote['model_sources']
    assert 'KernelWorkerStatus.ERROR' in (PRIVATE/'cli/status-v2-02/stdout.txt').read_text(encoding='utf8')
    for version in (1,2):
        assert f'Kernel version {version} successfully pushed' in (PRIVATE/f'cli/dispatch-v{version}/stdout.txt').read_text(encoding='utf8')
    archives=[];baseline=None;events=[];journal=[];cleanup=[];raw2=None
    for version in (1,2):
        path=PRIVATE/f'output-v{version}-final/egrd-v031-cpu-v{version}.zip'
        build=json.loads((HERE/f'CPU_BUILD_V{version}.json').read_bytes())
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            ident=json.loads(z.read('PAYLOAD_IDENTITY.json'))
            assert ident['payload_sha256']==build['payload_sha256']
            for n,h in build['members'].items():assert sha(z.read('source/'+n))==h,n
            log=z.read('cpu.log').decode()
            if version==1:assert 'Required approved dependency unavailable: flit_core' in log
            else:
                raw2=z.read('source/egrd/v031/cpu_preflight.py')
                assert 'without calling submit_patch' in log
                baseline=json.loads(z.read('results/baseline/DEVELOPMENT_RESULT.json'))
                assert baseline['original_failing_probe_still_fails'] and baseline['positive_controls_passed']
                assert baseline['target_receipt']['checks'][-1]['actual']==0
                assert baseline['bounded_regression']['exit_code']==0
                assert baseline['trusted_probe_unchanged'] and baseline['trusted_probe_write_denied'] and baseline['cleanup']
                events=[json.loads(l) for l in z.read('results/A/agent/adk_events.jsonl').splitlines()]
                journal=[json.loads(l) for l in z.read('results/A/agent/events.jsonl').splitlines()]
                cleanup=json.loads(z.read('results/A/agent/chroot_cleanup.json'))
                assert cleanup and all(c['root_removed'] for c in cleanup)
                assert json.loads(z.read('results/A/TRANSPORT_CLEANUP.json'))['complete']
                import re
                assert not any(re.search(r'/(?:trusted-roots|roots)/[a-f0-9]{12}/',n) for n in z.namelist())
            archives.append(dict(version=version,path=str(path),sha256=sha(path.read_bytes()),bytes=path.stat().st_size,
                CRC='ALL_MEMBERS_PASS',payload_sha256=build['payload_sha256'],all_uploaded_source_hashes_match=True,
                platform_status='ERROR',cpu_log_sha256=sha(z.read('cpu.log'))))
    responses=[p['function_response'] for e in events for p in e.get('event',{}).get('content',{}).get('parts',[]) if p.get('function_response')]
    submitted=[r for r in responses if r['name']=='submit_patch']
    assert len(submitted)==1 and submitted[0]['response']['error_type']=='GitDiffError'
    assert 'bad config line 1 in file /dev/null' in submitted[0]['response']['error_message']
    assert any('AGENT_FILESYSTEM_ISOLATION_PASS' in json.dumps(r) for r in responses)
    assert any(r['name']=='edit_file' and r['response']['status']=='ok' for r in responses)
    counters=[r for r in journal if r['kind']=='counters'][-1]
    times=[r for r in journal if r.get('stage')=='save_patch' and 'agent_elapsed_seconds' in r][-1]
    record=dict(arm='A',CPU_MODEL='SCRIPTED_ONLY',full_compiler=True,package_sha256=S0_SHA,
        native_Runner_initialized=True,scripted_requests=counters['llm_calls'],charged_tools=counters['tool_calls'],
        agent_seconds=times['agent_elapsed_seconds'],real_Gemma_requests=0,actual_model_tokens=None,
        actual_tool_names=sorted({r['name'] for r in responses}),
        production_edit='OBSERVED_INERT_COMMENT_ONLY',successful_submit=False,
        submit_error=submitted[0]['response']['error_message'],exported_applicable_patch=None,
        agent_cleanup=True,host_probe_read_write_rejected=True,chroot_symlink_canary_pass=True,
        compiled_generation_capture=None,HTTP_request_capture=None,
        missing_capture='V2 wrote HTTP requests only after successful Runner return; the failed run retained ADK events but no full request bodies.',
        official_native_resolved=None,canonical_swebench_resolved=None)
    safe_baseline={k:baseline[k] for k in ('original_source_sha256','tested_source_sha256','positive_controls_passed',
        'original_failing_probe_still_fails','target_probe_passed','trusted_probe_unchanged','trusted_probe_write_denied',
        'tests_did_not_change_source','cleanup')}
    safe_baseline.update(positive_controls=3,executed_target_assertions=1,failed_target_assertions=1,
        expected_related_count=1,observed_related_count=0,bounded_regression_exit_code=0,
        module_version=baseline['target_receipt']['source_module_version'],environment_warnings=baseline['environment_warnings'])
    cpu=dict(status='CPU_PREFLIGHT_BLOCKED',CPU_MODEL='SCRIPTED_ONLY',CPU_Notebook_id=141014201,
        CPU_Notebook_ref='wudangdexiaodoashi/egrd-v031-evidence-to-patch-cpu',CPU_Notebook_version=2,
        CPU_platform_status='ERROR',versions_executed=2,baseline=safe_baseline,
        records=[record,dict(arm='B',status='NOT_RUN',full_compiler=None,scripted_requests=None,
            successful_submit=None,agent_cleanup=None,official_native_resolved=None,canonical_swebench_resolved=None)],
        input_boundary=dict(only_B_has_receipt=None,original_issue_exact=None,instructions_equal=None,tools_equal=None,
            generation_equal=None,token_overhead=None,status='MODEL_BOUNDARY_ACCEPTANCE_NOT_COMPLETED'),
        real_Gemma_requests=0,model_weights_loaded=False,GPU=0,formal_submissions=0,
        full_both_arm_compiler_gate='INCOMPLETE_A_ONLY',Task_identity_gate='PASS',
        evidence_isolation_gate='PARTIAL_A_AND_TRUSTED_BASELINE_ONLY',CPU_Runner_gate='FAIL',
        trusted_development_evaluation_gate='BASELINE_PASS_POSTEDIT_NOT_RUN',model_authorization_gate='NOT_AUTHORIZED',
        post_V2_source_fix='NOT_KAGGLE_VALIDATED',GPU_experiment_frozen=False,
        first_V2_blocking_tool_error='run_command git diff --check: fatal bad config line1 in /dev/null',
        failure_attribution='RESEARCH_RUNTIME_INFRASTRUCTURE_NOT_AGENT_ALGORITHM',
        source_supported_cause='Inherited helper creates a regular /dev/null while Git reads it as global config. The contaminating write/content was not captured.',
        scripted_request_count_source='Official context llm_calls_used from ADK event journal; raw HTTP bodies/count were not archived on failure',
        remote_CPU_metadata_sha256=sha((PRIVATE/'remote-notebook-v2/kernel-metadata.json').read_bytes()))
    write(HERE/'CPU_TEST_RESULTS.json',cpu)
    write(HERE/'RAW_ARCHIVES.json',dict(private_evidence_root=str(PRIVATE),archives=archives,
        auxiliary_log_downloads='CLI auxiliary Notebook log transfer ended IncompleteRead; both main ZIPs are complete and CRC/hash verified'))
    build=json.loads((PRIVATE/'INPUT_BUILD.json').read_bytes())
    lock=dict(execution_frozen=False,GPU_authorized=False,status='BLOCKED_BY_CPU_RUNNER',candidate_sha256=S0_SHA,
        task_lock_sha256=sha((HERE/'TASK_IDENTITY_LOCK.json').read_bytes()),
        receipt_sha256=sha((HERE/'EVIDENCE_RECEIPT.json').read_bytes()),input_build=build,
        budget=dict(agent_seconds=300,charged_tools=60,command_seconds=120),
        configuration_discrepancies=['S0 declares no seed; pinned Compiler defaults do not supply seed17.',
            'S0 contains no15360 research Guard/safety1024 setting; formal serving admission path is unavailable.'],
        configuration_capture='SOURCE_INSPECTION_ONLY; failed V2 did not archive compiled generation/full HTTP requests',
        sessions=[dict(run=i,task_id='django__django-16333',arm=arm,status='NOT_RUN',model_requests=None,
            prompt_tokens=None,completion_tokens=None,official_native_resolved=None,canonical_swebench_resolved=None)
            for i,arm in enumerate(('A','B'),1)],
        blockers=['CPU Runner submission failed','B CPU arm/input boundary/post-edit evaluation unexecuted',
            'Post-V2 runtime fix needs actual CPU reacceptance','Resolve S0 versus later research settings before final GPU freeze',
            'No owner GPU authorization'])
    write(HERE/'GPU_EXECUTION_LOCK.json',lock)
    print(json.dumps(dict(status=cpu['status'],baseline_reproduced=True,scripted_A_requests=record['scripted_requests'],
        successful_submit=False,B='NOT_RUN',real_Gemma_requests=0)))


if __name__=='__main__':
    import sys
    collect_blocked()
