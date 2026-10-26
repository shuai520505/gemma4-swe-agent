"""CPU-only Dataset consumer, no Docker, SDK research or model inference."""
import base64
import json
from pathlib import Path

from .cli import HERE,PRIVATE,DATASET,NOTEBOOK,sha,write


def build(version=1):
    assert version in (1,2)
    base=json.loads((HERE/'DATASET_BUILD_V1.json').read_bytes())
    driver=(HERE/'runtime.py').read_bytes();compile(driver,'<development-driver>','exec')
    folder=PRIVATE/f'notebook-v{version}';folder.mkdir(parents=True,exist_ok=False)
    code=f'''import base64,json,hashlib,os,sys,subprocess,zipfile,shutil,time
from pathlib import Path
RUN_DIR=Path('/kaggle/working/egrd-v03-cpu-v{version}')
RUN_DIR.mkdir(parents=True,exist_ok=False)
INPUT_TEMP=Path('/kaggle/working/.egrd-v03-input-v{version}')
started=time.monotonic()
try:
    assert not list(Path('/dev').glob('nvidia[0-9]*')),'CPU-only authorization'
    driver=base64.b64decode({base64.b64encode(driver).decode()!r})
    assert hashlib.sha256(driver).hexdigest()=={sha(driver)!r}
    (RUN_DIR/'runtime.py').write_bytes(driver)
    bundles=list(Path('/kaggle/input').rglob('data_bundle.zip'))
    observed_bundle_sha256=None
    if bundles:
        assert len(bundles)==1,'Exactly one private development bundle'
        raw=bundles[0].read_bytes();observed_bundle_sha256=hashlib.sha256(raw).hexdigest()
        assert observed_bundle_sha256=={base['bundle_sha256']!r},'Immutable input bundle changed'
        INPUT_TEMP.mkdir(parents=True,exist_ok=False)
        with zipfile.ZipFile(bundles[0]) as archive:
            assert archive.testzip() is None
            assert all(not n.startswith('/') and '..' not in Path(n).parts for n in archive.namelist())
            archive.extractall(INPUT_TEMP)
        DATA_ROOT=INPUT_TEMP
        layout='ORIGINAL_ZIP'
    else:
        # Kaggle expands uploaded .zip files during Dataset ingestion. Bind
        # every mounted member through the exact original manifest instead.
        candidates=[p for p in Path('/kaggle/input').rglob('MANIFEST.json')
            if hashlib.sha256(p.read_bytes()).hexdigest()=={base['manifest_sha256']!r}]
        assert len(candidates)==1,'Unique matching immutable Dataset manifest required'
        DATA_ROOT=candidates[0].parent;layout='KAGGLE_UNPACKED_ARCHIVE'
    manifest=json.loads((DATA_ROOT/'MANIFEST.json').read_bytes())
    assert hashlib.sha256((DATA_ROOT/'MANIFEST.json').read_bytes()).hexdigest()=={base['manifest_sha256']!r}
    for name,digest in manifest['files'].items():
        assert hashlib.sha256((DATA_ROOT/name).read_bytes()).hexdigest()==digest,name
    identity=dict(dataset={DATASET!r},dataset_input_revision=manifest['revision'],CPU_only=True,
        input_mount=str(DATA_ROOT),input_layout=layout,uploaded_bundle_sha256={base['bundle_sha256']!r},
        observed_bundle_sha256=observed_bundle_sha256,
        dataset_manifest_sha256={base['manifest_sha256']!r},runtime_sha256={sha(driver)!r},
        GPU_device_nodes=[],model_requests=0,formal_submission=False)
    (RUN_DIR/'INPUT_IDENTITY.json').write_text(json.dumps(identity,indent=2))
    env=dict(os.environ,PYTHONIOENCODING='utf-8',PIP_DISABLE_PIP_VERSION_CHECK='1')
    with (RUN_DIR/'driver.stdout.log').open('w') as out,(RUN_DIR/'driver.stderr.log').open('w') as err:
        result=subprocess.run([sys.executable,str(RUN_DIR/'runtime.py'),str(DATA_ROOT),str(RUN_DIR/'results')],
            stdout=out,stderr=err,env=env,timeout=2100)
    assert result.returncode==0,'Development driver failed; original error preserved'
finally:
    cleanup=not INPUT_TEMP.exists()
    if INPUT_TEMP.exists():
        assert INPUT_TEMP.parent==Path('/kaggle/working') and INPUT_TEMP.name=='.egrd-v03-input-v{version}'
        shutil.rmtree(INPUT_TEMP);cleanup=not INPUT_TEMP.exists()
    (RUN_DIR/'NOTEBOOK_CLEANUP.json').write_text(json.dumps(dict(input_copy_removed=cleanup,
        wall_seconds=time.monotonic()-started,model_requests=0,GPU=False)))
    archive=Path('/kaggle/working/egrd-v03-cpu-v{version}.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as out:
        for path in sorted(RUN_DIR.rglob('*')):
            if path.is_file() and not path.is_symlink():out.write(path,path.relative_to(RUN_DIR))
    print('EGRD_V03_CPU_EVIDENCE',str(archive),flush=True)
'''
    compile(code,'<dataset-cpu-notebook>','exec')
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),
        cells=[dict(cell_type='code',source=code,id=sha(code.encode())[:12],metadata={},outputs=[],execution_count=None)])
    raw=(json.dumps(nb,indent=1)+'\n').encode();(folder/'study.ipynb').write_bytes(raw)
    # Reuse the verified CPU image only; no Compiler/wheelhouse experiment repeats.
    image=json.loads((HERE.parent/'v023/RECOVERED_DEPENDENCY_IDENTITIES.json').read_bytes())['pinned_Docker_image']
    meta=dict(id=NOTEBOOK,title='EGRD V03 Repair Development CPU',code_file='study.ipynb',language='python',
        kernel_type='notebook',is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,
        machine_shape='',dataset_sources=[DATASET],competition_sources=[],model_sources=[],kernel_sources=[],
        docker_image=image,docker_image_pinning_type='original')
    write(folder/'kernel-metadata.json',meta)
    write(HERE/f'CPU_BUILD_V{version}.json',dict(version=version,Notebook=NOTEBOOK,
        Notebook_sha256=sha(raw),runtime_sha256=sha(driver),dataset=DATASET,
        input_bundle_sha256=base['bundle_sha256'],input_manifest_sha256=base['manifest_sha256'],
        CPU_only=True,model_requests=0,max_task_count=3,max_CPU_versions=2))
    print('Frozen CPU Notebook',version,sha(raw),'no dispatch.')


if __name__=='__main__':
    import sys
    build(int(sys.argv[1]) if len(sys.argv)>1 else 1)
