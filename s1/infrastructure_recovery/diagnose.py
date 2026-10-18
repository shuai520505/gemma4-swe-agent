"""CPU evidence collection from official installed code and clean public base only."""
import importlib
import importlib.metadata as metadata
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tarfile

from harness_v2.evidence import atomic_json,atomic_bytes
from s1.util import sha_file
from s1.task_identity import find_data,identify


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    modules=['swegemma.sandbox.subprocess','swegemma.harness.container_setup',
        'swegemma.harness.verification','swegemma.harness.agent_runner','swegemma.evaluate']
    for name in modules:
        module=importlib.import_module(name)
        atomic_bytes(output/'official_sources'/(name+'.py'),Path(inspect.getfile(module)).read_bytes())
    data=find_data()
    atomic_json(output/'task_identity.json',identify(data,['requests_7328']))
    wheels={p.relative_to(data/'wheels').as_posix():dict(bytes=p.stat().st_size,sha256=sha_file(p))
        for p in sorted((data/'wheels').rglob('*.whl'))}
    atomic_json(output/'task_wheels.json',wheels)
    packages={d.metadata['Name']:d.version for d in metadata.distributions()}
    eps=[dict(name=e.name,value=e.value,distribution=d.metadata['Name'],version=d.version)
        for d in metadata.distributions() for e in d.entry_points if e.group=='pytest11']
    atomic_json(output/'host_environment.json',dict(packages=packages,pytest11=eps,
        python=sys.executable,sys_path=sys.path))
    from swegemma.sandbox.subprocess import SubprocessManager
    manager=SubprocessManager(base_dir=output/'sandboxes',timeout_seconds=120)
    sid=manager.start()
    try:
        atomic_json(output/'sandbox_layout.json',manager.sandboxes[sid])
        result=manager.exec(sid,'pwd')
        workspace=Path(result.stdout.strip())
        assert workspace.is_dir() and workspace.is_relative_to((output/'sandboxes').resolve())
        # Resolve public snapshot only: no Agent Patch or evaluation test patch.
        from swegemma.deduplication import resolve_task_snapshot_paths
        rows={r['instance_id']:r for r in map(json.loads,(data/'tasks.jsonl').read_text().splitlines())}
        snapshot,base,patch=resolve_task_snapshot_paths(data/'snapshots','requests_7328',rows['requests_7328']['repo'])
        with tarfile.open(snapshot) as tar:
            names=tar.getnames()
            atomic_json(output/'snapshot_members.json',names)
            tar.extractall(workspace,filter='data')
        roots=[p.parent for p in workspace.rglob('pyproject.toml') if (p.parent/'tests/conftest.py').exists()]
        if (workspace/'tests/conftest.py').exists():root=workspace
        else:
            assert len(roots)==1,roots
            root=roots[0]
        atomic_json(output/'clean_root.json',dict(root=str(root),base_commit=rows['requests_7328']['base_commit']))
        for name in ('tests/conftest.py','pyproject.toml','setup.cfg','setup.py','requirements-dev.txt'):
            path=root/name
            if path.exists():atomic_bytes(output/'base_configuration'/name,path.read_bytes())
        from harness_v2.isolation import prepare_pip_entrypoints
        prepare_pip_entrypoints(manager.sandboxes[sid]['venv'])
        # These are unmodified existing public tests. Their setup is the endpoint.
        commands=dict(environment="python3 -c 'import sys,requests,json,importlib.metadata as m; print(json.dumps(dict(prefix=sys.prefix,sys_path=sys.path,requests_file=requests.__file__,pytest11=[dict(name=e.name,value=e.value) for e in m.entry_points(group=\"pytest11\")])))'",
            traceconfig='python3 -m pytest --trace-config --collect-only -q tests/test_requests.py',
            fixture_setup='python3 -m pytest -vv --setup-show --full-trace tests/test_requests.py -k test_no_content_length --maxfail=1')
        import shlex
        for label,command in commands.items():
            r=manager.exec(sid,'cd '+shlex.quote(str(root))+' && '+command,timeout=180)
            atomic_json(output/(label+'.json'),dict(command=command,exit_code=r.exit_code,stdout=r.stdout,stderr=r.stderr))
    finally:
        manager.cleanup_all()
        atomic_json(output/'cleanup.json',dict(cleanup_complete=not manager.sandboxes))


if __name__=='__main__':main(sys.argv[1])
