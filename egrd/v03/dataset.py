"""One private versioned dataset; only licensed snapshots and owned probes."""
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
import zipfile

from .cli import HERE,ROOT,PRIVATE,DATASET,sha,write


def encoded(value):return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()


def pack(files):
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,body in sorted(files.items()):
            assert not name.startswith('/') and '..' not in Path(name).parts
            info=zipfile.ZipInfo(name,date_time=(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644<<16;archive.writestr(info,body)
    return buffer.getvalue()


def build(version):
    assert version in (1,2)
    directory=PRIVATE/f'dataset-v{version}';directory.mkdir(parents=True,exist_ok=False)
    if version==2:
        # Immutable input bytes are shared by a local hard link, not duplicated.
        # Results are explicit versioned sidecars; they do not rewrite v1 inputs.
        source=PRIVATE/'dataset-v1/data_bundle.zip'
        os.link(source,directory/'data_bundle.zip')
        shutil.copyfile(PRIVATE/'dataset-v1/dataset-metadata.json',directory/'dataset-metadata.json')
        for name in ('TASK_REPRODUCTIONS.json','CPU_EXECUTION_RECORD.json'):
            shutil.copyfile(HERE/name,directory/name)
        record=dict(dataset=DATASET,revision=2,input_revision=1,
            bundle_sha256=sha(source.read_bytes()),bundle_bytes=source.stat().st_size,
            sidecars={n:sha((directory/n).read_bytes()) for n in ('TASK_REPRODUCTIONS.json','CPU_EXECUTION_RECORD.json')},
            private=True,actual_remote_version=None)
        write(directory/'RESULTS_MANIFEST.json',record)
        write(HERE/'DATASET_BUILD_V2.json',record)
        print('Dataset revision 2 results frozen; v1 input bytes unchanged.')
        return record
    else:
        files={}
        historical=json.loads((ROOT/'egrd/v022/TASK_POOL_LOCK.json').read_bytes())
        external=(ROOT/'egrd/v023/EXTERNAL_SOURCE_LOCK.json').read_bytes()
        pool=json.loads(external)
        records=[dict(r,split='HISTORICAL_DEVELOPMENT_ONLY',independent_confirmation_eligible=False)
                 for r in historical['source_record_metadata']]
        files['metadata/historical_development_registry.json']=encoded(dict(source_sha256=historical['source_tasks_sha256'],
            task_count=129,tasks=records,raw_issues_tests_fixes_included=False))
        files['metadata/external_source_lock.json']=external  # preserve frozen ordering byte for byte
        exposures=[dict(instance_id=r['instance_id'],split='HISTORICAL_DEVELOPMENT_ONLY',
            exposure='PRESERVED_HISTORY_OR_RESERVATION',independent_confirmation_eligible=False) for r in records]
        exposures += [dict(instance_id=r['instance_id'],split='EXTERNAL_DEVELOPMENT_EXPOSED' if i<2 else 'EXTERNAL_PROSPECTIVE_POOL',
            exposure='V03_ISSUE_AND_PROBE_REVIEWED' if i<2 else 'METADATA_ONLY_NOT_ADMITTED',
            independent_confirmation_eligible=False if i<2 else None) for i,r in enumerate(pool['ranked_metadata'])]
        files['metadata/exposure.json']=encoded(exposures)
        dependencies=json.loads((HERE/'DEPENDENCY_LOCK.json').read_bytes())
        files['environments/dependency_lock.json']=(HERE/'DEPENDENCY_LOCK.json').read_bytes()
        for record in dependencies['packages'].values():
            body=(PRIVATE/'dependencies/wheels'/record['filename']).read_bytes()
            assert sha(body)==record['sha256'];files['wheels/'+record['filename']]=body
            extra=record['supplemental_license']
            if extra:
                body=(PRIVATE/'dependencies/supplemental-licenses'/extra['file']).read_bytes()
                assert sha(body)==extra['sha256'];files['licenses/'+extra['file']]=body
        for group,names in dependencies['groups'].items():
            text=''.join(f"{name}=={dependencies['packages'][name]['version']} --hash=sha256:{dependencies['packages'][name]['sha256']}\n" for name in names)
            files[f'environments/{group}/requirements.lock']=text.encode()
        checks=json.loads((ROOT/'egrd/v023/EXTERNAL_SNAPSHOT_CHECKS.json').read_bytes())['records']
        history=next(r for r in historical['source_record_metadata'] if r['instance_id']=='fastapi_14297')
        last=json.loads((PRIVATE/'source_downloads/fastapi-source.json').read_bytes())
        last.update({k:history[k] for k in ('repo','issue_sha256','task_record_sha256')})
        tasks=[]
        contracts={
            'django__django-16333':'A valid UserCreationForm exposing a selected ManyToMany group must persist that relation, as plain ModelForm does.',
            'pydata__xarray-3095':'Deep Dataset copy must retain the Unicode index coordinate dtype when initial and shallow copies preserve it.',
            'fastapi_14297':'Optional List[bytes] multipart upload must return HTTP 200 and two byte lengths, as the non-optional positive control does.',
        }
        for index,row in enumerate([*checks,last]):
            ident=row['instance_id'];group=('django','xarray','fastapi')[index]
            snapshot=(ROOT.parent/'private-evidence/egrd_v023/external-sources/snapshots'/f'{ident}.tgz') if index<2 else PRIVATE/'source_downloads'/f'{ident}.tgz'
            body=snapshot.read_bytes();assert sha(body)==row['snapshot_sha256']
            with tarfile.open(fileobj=io.BytesIO(body),mode='r:gz') as archive:
                root=row['archive_root'];license_body=archive.extractfile(root+'/LICENSE').read()
                if group=='django':assert b'Django Software Foundation' in license_body and b'Redistribution' in license_body
                if group=='xarray':assert license_body.startswith(b'Apache License')
                if group=='fastapi':assert b'The MIT License' in license_body
                licenses={m.name.split('/')[-1]:sha(archive.extractfile(m).read()) for m in archive.getmembers()
                    if m.isfile() and len(m.name.split('/'))==2 and m.name.split('/')[-1].upper().startswith(('LICENSE','NOTICE','COPYING'))}
            files[f'snapshots/{ident}.tgz']=body
            probe=(PRIVATE/'probes'/f'{ident}.py').read_bytes();files[f'diagnostics/{ident}.py']=probe
            task=dict(instance_id=ident,repo=row['repo'],base_commit=row['base_commit'],issue_sha256=row['issue_sha256'],
                snapshot_path=f'snapshots/{ident}.tgz',snapshot_sha256=row['snapshot_sha256'],archive_root=row['archive_root'],
                source_url=row['source_url'],license=('BSD-3-Clause','Apache-2.0','MIT')[index],license_file_hashes=licenses,
                module=group,environment_group=group,requirements_path=f'environments/{group}/requirements.lock',
                diagnostic_path=f'diagnostics/{ident}.py',diagnostic_sha256=sha(probe),
                expected_contract=contracts[ident],contract_provenance='Original Issue only; owned probe, no evaluator overlay/reference fix',
                split='EXTERNAL_DEVELOPMENT_EXPOSED' if index<2 else 'HISTORICAL_DEVELOPMENT_ONLY',
                exposure='V03_ISSUE_AND_PROBE_REVIEWED' if index<2 else 'PREVIOUSLY_USED_AND_ANALYZED',
                independent_confirmation_eligible=False,evaluation_kind='ISSUE_GROUNDED_DEVELOPMENT_PROBE',
                official_native_compatible=False,canonical_SWEbench_evaluation=False,
                environment_policy='Isolated CPython312 venv, source import by immutable base archive; exact offline wheels; no source patch')
            tasks.append(task)
        files['diagnostics/common.py']=(PRIVATE/'probes/common.py').read_bytes()
        files['metadata/task_registry.json']=encoded(dict(schema='EGRD_DEV_TASKS_V1',
            execution_order=[r['instance_id'] for r in tasks],tasks=tasks,external_order_lock_sha256=sha(external)))
        files['results/task_reproductions.json']=encoded(dict(status='NOT_RUN',records=[dict(instance_id=r['instance_id'],
            status='NOT_RUN',genuine_issue_failure=None,official_native_resolved=None,swebench_resolved=None) for r in tasks]))
        files['LICENSE_NOTICES.md']=('''# Private research aggregate: original licenses retained
This aggregate is not relicensed as CC0. Django source is BSD-3-Clause,
xarray source is Apache-2.0, FastAPI source is MIT. Each unmodified source
archive retains all original license/copyright/notice files. No patches are applied.
Whole dependency wheels retain their bundled license/notice files; the annotated-doc
0.0.2 publisher MIT license omitted from its wheel is supplied separately.
Metadata uses only source identities, hashes and our exposure labels; no hidden
evaluator, reference fix or original task-data payload is included. Own diagnostic
programs are development probes, not native competition/SWE-bench tests.
Keep this dataset private. Do not infer redistribution rights for original
Issue text, which is not copied here. Original 129 tasks remain development only.
''').encode()
    manifest=dict(schema='EGRD_PRIVATE_DATASET_V1',revision=version,
        title='EGRD Repair Development',private=True,source_base='c8c92a45688a4a7005dea852e7927baefe980402',
        files={name:sha(body) for name,body in sorted(files.items())},
        no_reference_fixes=True,no_evaluator_overlays=True,no_original_issue_bodies=True,
        model_inference=False,GPU=False,formal_submission=False)
    files['MANIFEST.json']=encoded(manifest)
    raw=pack(files);(directory/'data_bundle.zip').write_bytes(raw)
    meta=dict(title='EGRD Repair Development',id=DATASET,isPrivate=True,
        subtitle='Private CPU tasks, immutable sources and reproducible diagnostic evidence',
        description='Private versioned repair development aggregate. Mixed upstream licenses and attribution retained in source archives. Historical tasks are exposed development only. External checks are not official Native or canonical SWE-bench evaluation. No reference solutions, hidden evaluator or model inference.',
        licenses=[dict(name='other')])
    write(directory/'dataset-metadata.json',meta)
    record=dict(dataset=DATASET,revision=version,bundle_sha256=sha(raw),bundle_bytes=len(raw),
        manifest_sha256=sha(files['MANIFEST.json']),member_hashes=manifest['files'],
        task_count=3,historical_metadata_count=129,external_ranked_metadata_count=492,
        private=True,actual_remote_version=None)
    write(HERE/f'DATASET_BUILD_V{version}.json',record)
    if version==1:write(HERE/'DATASET_MANIFEST.json',record)
    print('Private Dataset bundle frozen',version,len(raw),'bytes',sha(raw))
    return record


if __name__=='__main__':
    import sys
    build(int(sys.argv[1]))
