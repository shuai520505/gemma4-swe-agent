"""Restore a CPU-validated research tool surface without changing frozen trials."""
import email,hashlib,importlib.metadata as md,json,os,re,shutil,subprocess
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

PINNED_HOST={'pytest':'8.4.2','pip':'24.1.2','packaging':'26.1','pluggy':'1.6.0','iniconfig':'2.3.0','pygments':'2.20.0'}
def sha(raw):return hashlib.sha256(raw).hexdigest()

def repair(root):
    root=Path(root).absolute();approved=root/'opt/approved'
    assert root.parent.name=='roots' and approved.is_dir() and not approved.is_symlink()
    assert {n:md.version(n) for n in PINNED_HOST}==PINNED_HOST,'Pinned-image distribution drift'
    files={};distributions={}
    def record_file(relative,raw,mode=0o644):
        relative=Path(relative)
        assert not relative.is_absolute() and '..' not in relative.parts
        target=root/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        assert not target.is_symlink()
        if target.exists():assert target.read_bytes()==raw,'Never replace a locked runtime file'
        else:target.write_bytes(raw);target.chmod(mode)
        files[relative.as_posix()]=sha(raw)
    def existing(name):
        found=[]
        for folder in approved.glob('*.dist-info'):
            path=folder/'METADATA'
            if not path.is_file():continue
            meta=email.message_from_bytes(path.read_bytes())
            if canonicalize_name(meta['Name'])==name:found.append((meta,path))
        assert len(found)<=1,'Conflicting task distribution metadata'
        return found[0] if found else None
    def ensure(requirement):
        name=canonicalize_name(requirement.name)
        if name in distributions:
            assert not requirement.specifier or distributions[name]['version'] in requirement.specifier
            return
        reused=existing(name)
        if reused:
            meta,path=reused;version=meta['Version']
            dependencies=meta.get_all('Requires-Dist',[])
            distributions[name]=dict(version=version,source='Unmodified locked task wheel',metadata_sha256=sha(path.read_bytes()))
        else:
            dist=md.distribution(name);version=dist.version;dependencies=dist.requires or []
            assert name in PINNED_HOST and version==PINNED_HOST[name],'Only explicit pinned host distributions may be added'
            origin=Path(dist.locate_file('')).resolve()
            copied=0
            for member in dist.files or []:
                relative=Path(str(member))
                if relative.is_absolute() or '..' in relative.parts or relative.suffix in ('.pyc','.pth') or '__pycache__' in relative.parts:continue
                source=Path(dist.locate_file(member)).resolve()
                assert source.is_relative_to(origin)
                if not source.is_file():continue
                record_file(Path('opt/approved')/relative,source.read_bytes());copied+=1
            assert copied>0
            distributions[name]=dict(version=version,source='Pinned image installed distribution; no .pth or external entrypoints',files=copied)
        assert not requirement.specifier or version in requirement.specifier
        for text in dependencies:
            dependency=Requirement(text)
            if dependency.marker and not dependency.marker.evaluate({'extra':''}):continue
            ensure(dependency)
    ensure(Requirement('pytest==8.4.2'));ensure(Requirement('pip==24.1.2'))
    alias=root/'usr/bin/python'
    assert not alias.exists() and not alias.is_symlink()
    alias.symlink_to('python3')
    for name,program in {
        'pytest':'from pytest import console_main\nraise SystemExit(console_main())\n',
        'pip':'from pip._internal.cli.main import main\nraise SystemExit(main())\n',
    }.items():record_file(Path('usr/local/bin')/name,('#!/usr/bin/python3\n'+program).encode(),0o755)
    for command in ('touch','which'):
        executable=shutil.which(command);assert executable
        raw=Path(executable).resolve().read_bytes()
        record_file(Path(executable).relative_to('/'),raw,0o755)
        if raw.startswith(b'\x7fELF'):
            linked=subprocess.run(['ldd',executable],capture_output=True,text=True,check=True,timeout=20)
            assert 'not found' not in linked.stdout
            for name in re.findall(r'(?:=>\s*)?(/[^\s()]+)',linked.stdout):
                record_file(Path(name).relative_to('/'),Path(name).resolve().read_bytes(),0o755)
    manifest=dict(schema='RESEARCH_RUNTIME_SURFACE_V1',distributions=distributions,files=files,
                  aliases={'/usr/bin/python':'python3'},network_policy_unchanged=True,
                  readonly_packages=True,root_UID_policy_unchanged=True)
    raw=json.dumps(manifest,sort_keys=True,indent=2).encode()
    (root.parent.parent/('RUNTIME_REPAIR_'+root.name+'.json')).write_bytes(raw)
    return dict(distributions=distributions,files_hashed=len(files),manifest_sha256=sha(raw),
                python_alias=True,pytest_entrypoint=True,pip_entrypoint=True,touch=True,which=True,
                network_policy_unchanged=True,readonly_packages=True)
