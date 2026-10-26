"""Independently inspect private raw CPU evidence; export safe derived results."""
from collections import Counter
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from .cli_recovery import HERE, ROOT, PRIVATE, REF, REQUESTED_REF, sha
from .cpu_acceptance import HASHES


def write(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf8',newline='\n')


def collect():
    path=PRIVATE/'v1-output/egrd-v023-cpu-v1.zip'
    raw=path.read_bytes()
    build=json.loads((HERE/'cpu-v1/BUILD.json').read_bytes())
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert archive.testzip() is None
        identity=json.loads(archive.read('PAYLOAD_IDENTITY.json'))
        assert identity['payload_sha256']==build['payload_sha256']
        assert identity['files']==build['payload_members']
        for name,digest in build['payload_members'].items():
            assert sha(archive.read('source/'+name))==digest,name
        results=json.loads(archive.read('validation/CPU_TEST_RESULTS.json'))
        assert results['status']=='COMPILER_FULL_PASS' and results['GPU_count']==0
        environment=json.loads(archive.read('validation/ENVIRONMENT.json'))
        assert environment['sdk']==dict(swegemma='0.2.11',**{'adk-submission':'0.2.13',
            'google-adk':'1.36.1','adk-eval-core':'0.1.0'})
        wheels=json.loads(archive.read('WHEEL_HASHES.json'))
        assert wheels==build['wheel_hashes']
        sdk_pins=json.loads((ROOT/'meer/v01/OFFICIAL_SOURCE_PINS.json').read_bytes())
        for name,pin in sdk_pins.items():
            if name.endswith('.whl'):assert wheels[name]==pin['sha256']
        members=json.loads(archive.read('validation/INSTALLED_OFFICIAL_MEMBER_HASHES.json'))
        records=[]
        for row in results['records']:
            arm=row['arm']
            assert arm in HASHES and row['package_sha256']==HASHES[arm]
            assert sha((ROOT/f'egrd/v022/submission_{arm}.zip').read_bytes())==HASHES[arm]
            with zipfile.ZipFile(io.BytesIO(archive.read(f'source/egrd/v022/submission_{arm}.zip'))) as candidate:
                assert sha(candidate.read('skills/meer-evidence/scripts/verify.py'))=='dae959c8068e6d320c7fc5c37f719ccd928f56dd19f4335af0d33193ea3f499c'
            assert sha(archive.read(f'validation/{arm}/TaskResult.json'))==row['TaskResult_sha256']
            assert sha(archive.read(f'validation/{arm}/verifier/phase2.junit.xml'))==row['JUnit_sha256']
            native=json.loads(archive.read(f'validation/{arm}/TaskResult.json'))
            junit=ET.fromstring(archive.read(f'validation/{arm}/verifier/phase2.junit.xml'))
            assert native['resolved'] and not list(junit.iter('failure')) and not list(junit.iter('error'))
            assert len(list(junit.iter('testcase')))==1
            assert sha(archive.read(f'validation/{arm}/final.patch'))==row['patch_sha256']
            assert json.loads(archive.read(f'validation/{arm}/TRANSPORT_CLEANUP.json'))['complete']
            events=[json.loads(line) for line in archive.read(f'validation/{arm}/agent/adk_events.jsonl').splitlines()]
            calls=[p['function_call'] for e in events for p in e.get('event',{}).get('content',{}).get('parts',[]) if p.get('function_call')]
            names=[x['name'] for x in calls]
            assert Counter(names)['run_skill_script']==14 and not set(names)&{'list_skills','load_skill','load_skill_resource'}
            responses=[p['function_response']['response'] for e in events
                for p in e.get('event',{}).get('content',{}).get('parts',[])
                if p.get('function_response',{}).get('name')=='run_skill_script']
            assert responses[0]['error_code']=='INVALID_ARGUMENTS'
            assert responses[1]['error_code']=='SCRIPT_NOT_FOUND'
            assert responses[2]['status']=='error' and '--check' in responses[2]['stderr']
            assert row['cleanup']['complete'] and row['explicit_submit']
            records.append(row)
        assert [r['arm'] for r in records]==['N','D']
        assert records[0]['generation']==records[1]['generation']
        log=archive.read('cpu.log').decode(errors='replace')
    meta=json.loads((PRIVATE/'actual-v1-pull/kernel-metadata.json').read_bytes())
    assert meta['id']==REF and meta['id_no']==140992640
    assert meta['is_private'] and not meta['enable_gpu'] and not meta['enable_tpu'] and not meta['enable_internet']
    assert meta['model_sources']==[] and meta['machine_shape']=='None'
    final=(PRIVATE/'cli/actual-v1-status-02/stdout.txt').read_text(encoding='utf8')
    assert 'KernelWorkerStatus.COMPLETE' in final
    assert not (PRIVATE/'dispatch-v2.json').exists()
    result=dict(status='COMPILER_FULL_PASS',CPU_MODEL='SCRIPTED_ONLY',
        source='Kaggle CPU 140992640/v1 original output archive',Notebook_ref=REF,
        records=records,actual_Gemma_requests=0,GPU_devices_observed=0,
        scripted_HTTP_requests=sum(r['scripted_HTTP_requests'] for r in records),
        real_model_token_usage=None,SDK=environment['sdk'],Python=environment['Python'],
        pinned_wheel_count_verified=len(wheels),installed_source_members_verified=len(members),
        archive_sha256=sha(raw),archive_bytes=len(raw),archive_CRC_valid=True,
        payload_sha256=build['payload_sha256'],source_members_verified=len(build['payload_members']),
        new_independent_tasks_admitted=0,real_Gemma_adoption='NOT_MEASURED',
        warnings=dict(ensurepip_unavailable='ensurepip unavailable' in log,
            warning_resolution='Inherited native SubprocessSandbox fallback without pip; both synthetic verifier results executed successfully'))
    write('CPU_TEST_RESULTS.json',result)
    write('KAGGLE_EXECUTION_RECORD.json',dict(Notebook_id=140992640,version=1,ref=REF,
        requested_ref=REQUESTED_REF,actual_ref_source='CLI push returned title-derived canonical slug, followed by read-only metadata/status',
        status='COMPLETE',versions_pushed=1,versions_executed=1,maximum_authorized_CPU_versions=2,
        retry_used=False,private=True,CPU_only=True,internet=False,model_sources=[],
        requested_machine_shape='',actual_machine_shape='None',GPU_devices_observed=0,
        GPU_inference=0,formal_submissions=0,actual_Gemma_requests=0,
        platform_log_last_timestamp_seconds=218.891741598,
        platform_log_time_scope='Last observed conversion log timestamp, not a CPU billing measure',
        worker_seconds=sum(r['worker_seconds'] for r in records),
        CPU_billing=None,GPU_account_quota_delta=None,
        Notebook_sha256=build['Notebook_sha256'],payload_sha256=build['payload_sha256'],
        raw_archive=dict(path_relative_to_workspace=path.relative_to(ROOT.parent).as_posix(),
            sha256=sha(raw),bytes=len(raw),CRC_valid=True),
        SDK=environment['sdk'],Python=environment['Python'],
        source_start='e11b28c99bec91049aec68119fead5e13fa68373',
        source_parent='765530b39a7666a78ece099756fac925a932c617',
        raw_CLI_records=[dict(label=p.parent.name,**json.loads(p.read_bytes()))
                         for p in sorted((PRIVATE/'cli').glob('*/record.json'))]))
    write('RECOVERED_DEPENDENCY_IDENTITIES.json',dict(wheelhouse=wheels,SDK=environment['sdk'],
        installed_official_source_hashes=members,pinned_Docker_image=meta['docker_image'],
        installation='Historical trusted 41-wheel set, no-index/no-deps force-reinstall in ephemeral CPU container; no package upgrade or local install'))
    print('Verified CPU full Compiler/Runner result, frozen candidates, 202 source members and native synthetic outputs.')
    return result


if __name__=='__main__':collect()
