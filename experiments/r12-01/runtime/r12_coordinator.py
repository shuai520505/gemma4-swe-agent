"""R12 materialization and admission over PR43 coordinator. No GPU allocation API."""
import asyncio,hashlib,json,sys,time,zipfile
from pathlib import Path
from r12_adapter import HASHES,HERE,trusted_binding
sha=lambda b:hashlib.sha256(b).hexdigest()

def materialize(package,manifest,out):
    assert sha(Path(package).read_bytes())==manifest['CPU_dispatch_archive_sha256']
    cohort=json.loads((HERE/'COHORT_LOCK.json').read_bytes())
    assert sha((HERE/'COHORT_LOCK.json').read_bytes())==manifest['cohort_lock_sha256']
    assert cohort['order']==[[r['instance_id'],r['candidate']] for r in manifest['sessions']]
    for n,h in HASHES.items():assert sha((HERE/'candidates'/(n+'.zip')).read_bytes())==h==manifest['candidate_zip_sha256'][n]
    target=Path(out)/'inputs';target.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(package) as z:
        for info in z.infolist():
            p=Path(info.filename)
            if not p.parts or p.parts[0]!='integration':continue
            allowed=len(p.parts)>1 and p.parts[1] in ('prepared','frozen-checks') or p.name.endswith('.GPU_BINDING.json')
            if not allowed or info.is_dir():continue
            assert not p.is_absolute() and '..' not in p.parts
            dest=target/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(info))
    root=target/'integration';bindings={}
    expected={r['instance_id']:r for r in cohort['rows']}
    for p in root.glob('*.GPU_BINDING.json'):
        binding=json.loads(p.read_bytes());ident=binding['issue']['instance_id'];assert binding['issue']==expected[ident]
        original=Path(binding['snapshot']).parents[4]
        def remap(v):
            if isinstance(v,str) and v.startswith(str(original)+'/'):return str(target/Path(v).relative_to(original))
            if isinstance(v,list):return [remap(x) for x in v]
            if isinstance(v,dict):return {k:remap(x) for k,x in v.items()}
            return v
        binding=remap(binding)
        taskfile=root/(ident+'.json');taskfile.write_text(json.dumps(expected[ident]));binding['taskfile']=str(taskfile)
        # Extras come from the separately pinned, read-only task input dataset.
        inputs=next(Path('/kaggle/input').rglob('R12_INPUTS.json'));input_manifest=json.loads(inputs.read_bytes())
        assert sha(inputs.read_bytes())==manifest['task_input_manifest_sha256']
        binding['runtime_extra_wheels']=[str(inputs.parent/n) for n in binding['runtime_extra_sha256']]
        for name,h in binding['runtime_extra_sha256'].items():assert sha((inputs.parent/name).read_bytes())==h==input_manifest['files'][name]
        binding=trusted_binding(binding,root/'frozen-checks');bindings[ident]=binding
    assert set(bindings)==set(expected)
    return bindings

async def run(manifest_path,package,out,authorization_path,first_cell_started):
    manifest=json.loads(Path(manifest_path).read_bytes())
    authorization=json.loads(Path(authorization_path).read_bytes())
    assert manifest['gate']=='R12_GPU_READY','Resource/integration gate must be freshly cleared before dispatch'
    assert authorization['explicit_user_GPU_authorization'] is True and authorization['study']=='gemma-r12-01'
    # A JSON flag is an accident guard, not a substitute for human authorization.
    import gemma_pair.coordinator as prior
    plan=dict(bindings=materialize(package,manifest,out),order=[(r['instance_id'],r['candidate']) for r in manifest['sessions']],window_seconds=18000,new_explicit_GPU_authorization=True)
    await prior.run(out,float(first_cell_started),plan)

if __name__=='__main__':asyncio.run(run(*sys.argv[1:]))
