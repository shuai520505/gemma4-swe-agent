"""Verify the original private CPU archive; export allowlisted derived results."""
import json
import zipfile

from .cli import HERE, ROOT, PRIVATE, NOTEBOOK, DATASET, sha, write


def collect():
    build=json.loads((HERE/'CPU_BUILD_V1.json').read_bytes())
    frozen=json.loads((HERE/'DATASET_BUILD_V1.json').read_bytes())
    archive=PRIVATE/'output-v1/egrd-v03-cpu-v1.zip'
    remote=json.loads((PRIVATE/'remote-notebook-v1/kernel-metadata.json').read_bytes())
    assert remote['id']==NOTEBOOK and remote['is_private'] is True
    assert remote['enable_gpu'] is False and remote['enable_tpu'] is False
    assert remote['enable_internet'] is False and not remote['model_sources']
    assert remote['dataset_sources']==[DATASET]
    assert 'KernelWorkerStatus.COMPLETE' in (PRIVATE/'cli/status-v1/stdout.txt').read_text()
    assert 'Kernel version 1 successfully pushed' in (PRIVATE/'cli/notebook-dispatch-v1/stdout.txt').read_text()
    assert sha((PRIVATE/'notebook-v1/study.ipynb').read_bytes())==build['Notebook_sha256']
    with zipfile.ZipFile(PRIVATE/'dataset-v1/data_bundle.zip') as inputs:
        assert inputs.testzip() is None
        assert sha((PRIVATE/'dataset-v1/data_bundle.zip').read_bytes())==frozen['bundle_sha256']
        for name,digest in frozen['member_hashes'].items():
            assert sha(inputs.read(name))==digest,name
        registry=json.loads(inputs.read('metadata/task_registry.json'))
        assert inputs.read('metadata/external_source_lock.json')==(ROOT/'egrd/v023/EXTERNAL_SOURCE_LOCK.json').read_bytes()
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        identity=json.loads(z.read('INPUT_IDENTITY.json'))
        assert identity['dataset_manifest_sha256']==frozen['manifest_sha256']
        assert identity['runtime_sha256']==build['runtime_sha256']==sha(z.read('runtime.py'))
        assert z.read('runtime.py')==(HERE/'runtime.py').read_bytes()
        summary=json.loads(z.read('results/TASK_REPRODUCTIONS.json'))
        assert [r['instance_id'] for r in summary['records']]==registry['execution_order']
        records=[]
        for task,raw in zip(registry['tasks'],summary['records']):
            ident=raw['instance_id'];prefix=f'results/tasks/{ident}/'
            assert json.loads(z.read(prefix+'RESULT.json'))==raw
            for key in ('base_commit','issue_sha256','snapshot_sha256','repo'):
                assert raw[key]==task[key]
            assert raw['probe_sha256']==task['diagnostic_sha256']
            assert raw['requirements_sha256']==frozen['member_hashes'][task['requirements_path']]
            assert raw['source_unchanged'] and raw['source_tree_before']==raw['source_tree_after']
            assert raw['cleanup'] and raw['official_native_resolved'] is None and raw['swebench_resolved'] is None
            commands={}
            for key,folder in (('venv_creation','venv'),('installation','install'),('pip_check','pip-check'),
                               ('import_smoke','import'),('diagnostic_execution','diagnostic')):
                actual=json.loads(z.read(prefix+folder+'/COMMAND.json'))
                assert actual==raw[key] and actual['owned_process_reaped']
                for stream in ('stdout','stderr'):
                    body=z.read(prefix+folder+'/'+stream+'.log')
                    assert sha(body)==actual[stream+'_sha256']
                    assert len(body)==actual[stream+'_bytes']
                commands[key]=actual
            assert json.loads(z.read(prefix+'probe.json'))==raw['probe']
            assert raw['probe']['controls_passed'] and raw['environment_verified']
            assert raw['classification']=='TARGET_BEHAVIOR_FAILURE'
            assert raw['probe']['phase']=='TARGET' and commands['diagnostic_execution']['returncode']==1
            receipt=raw['probe']
            records.append({**{k:raw[k] for k in ('instance_id','repo','base_commit','issue_sha256','snapshot_sha256',
                'split','exposure','status','classification','environment_verified','genuine_issue_failure',
                'source_tree_before','source_tree_after','source_unchanged','cleanup','probe_sha256',
                'requirements_sha256','wall_seconds','termination_reason','official_native_resolved','swebench_resolved',
                'model_requests','prompt_tokens','completion_tokens','tool_requests')},
                'evaluation_kind':'ISSUE_GROUNDED_DEVELOPMENT_PROBE',
                'canonical_SWEbench_evaluation':False,'independent_confirmation_eligible':False,
                'commands':commands,'positive_controls_passed':True,
                'executed_check_count':len(receipt['checks']),
                'passed_control_count':sum(c['control'] and c['passed'] for c in receipt['checks']),
                'failed_target_assertions':sum(not c['control'] and not c['passed'] for c in receipt['checks']),
                'target_exception_type':receipt['exception_type'],
                'runtime':{k:raw['runtime'][k] for k in ('python','module_version','packages','installed_RECORD_sha256')},
                'source_import_verified':raw['source_import_verified'],
                'raw_result_sha256':sha(z.read(prefix+'RESULT.json')),
                'probe_receipt_sha256':sha(z.read(prefix+'probe.json')),
                'environment_warning':'Nonfatal sitecustomize startup reports missing wrapt; probe controls and import succeed. Isolation is venv-level, not a hardened sandbox.'})
        cleanup=json.loads(z.read('NOTEBOOK_CLEANUP.json'))
        assert cleanup['input_copy_removed'] and not cleanup['GPU']
        environment=json.loads(z.read('results/ENVIRONMENT.json'))
        log=json.loads((PRIVATE/'output-v1/egrd-v03-repair-development-cpu.log').read_bytes())
        execution=dict(Notebook=NOTEBOOK,Notebook_id=remote['id_no'],version=1,status='COMPLETE',
            private=True,CPU_only=True,enable_gpu=False,enable_tpu=False,internet=False,
            model_sources=[],GPU_inference=0,model_requests=0,formal_submissions=0,
            Notebook_sha256=build['Notebook_sha256'],runtime_sha256=build['runtime_sha256'],
            dataset_input_version=1,input_bundle_sha256=frozen['bundle_sha256'],
            input_manifest_sha256=frozen['manifest_sha256'],input_layout=identity['input_layout'],
            observed_original_bundle_sha256=identity['observed_bundle_sha256'],
            mounted_member_hashes_checked=True,docker_image=remote['docker_image'],
            runtime=environment,task_wall_seconds=sum(r['wall_seconds'] for r in records),
            notebook_body_wall_seconds=cleanup['wall_seconds'],
            platform_log_last_timestamp_seconds=max(e['time'] for e in log),
            billed_CPU_seconds=None,account_GPU_quota_delta=None,
            budget='3600 second requested CPU window; driver 2100; commands 60/120/180 as source-bound',
            all_cleanup=True,Compiler_retested=False,actual_CPU_versions=1,authorized_max_CPU_versions=2)
        output=dict(schema='EGRD_DEV_RESULTS_PUBLIC_V1',records=records,
            environment_verified=sum(r['environment_verified'] for r in records),
            genuine_issue_failures=sum(r['genuine_issue_failure'] for r in records),
            model_requests=0,official_native_resolved=None,swebench_resolved=None,
            all_cleanup=True,GPU=False,formal_submission=False,
            raw_archive_sha256=sha(archive.read_bytes()),Notebook_id=remote['id_no'],Notebook_version=1)
        raw_record=dict(path=str(archive),sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,
            CRC='ALL_MEMBERS_PASS',members={i.filename:dict(crc32=f'{i.CRC:08x}',bytes=i.file_size,
                sha256=sha(z.read(i))) for i in z.infolist()})
        write(PRIVATE/'VERIFIED_RAW_ARCHIVE.json',raw_record)
        write(HERE/'RAW_ARCHIVES.json',dict(private_evidence_root=str(PRIVATE),archives=[
            {k:raw_record[k] for k in ('path','sha256','bytes','CRC')}
        ],member_manifest_sha256=sha((PRIVATE/'VERIFIED_RAW_ARCHIVE.json').read_bytes()),
            raw_trajectory_or_probe_content_public=False))
    write(HERE/'CPU_EXECUTION_RECORD.json',execution)
    write(HERE/'TASK_REPRODUCTIONS.json',output)
    print(json.dumps(dict(Notebook_id=execution['Notebook_id'],environment_verified=output['environment_verified'],
        genuine_issue_failures=output['genuine_issue_failures'],archive_sha256=output['raw_archive_sha256'])))


if __name__=='__main__':collect()
