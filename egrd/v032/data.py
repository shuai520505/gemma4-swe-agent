"""Reuse exact PR40 data/environment construction; no task selection or solutions."""
import json
import os
from pathlib import Path
import subprocess
import tarfile

from egrd.v03.runtime import restore,tree_identity,cleanup
from egrd.v031.prepare import ROOT,HERE as FROZEN,sha,write


def prepare(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    digest=json.loads((ROOT/'egrd/v03/DATASET_BUILD_V1.json').read_bytes())['manifest_sha256']
    paths=[p for p in Path('/kaggle/input').rglob('MANIFEST.json')
           if 'egrd-repair-development' in str(p) and sha(p.read_bytes())==digest]
    assert len(paths)==1
    data=paths[0].parent;manifest=json.loads(paths[0].read_bytes())
    for name,value in manifest['files'].items():assert sha((data/name).read_bytes())==value,name
    task=next(t for t in json.loads((data/'metadata/task_registry.json').read_bytes())['tasks'] if t['instance_id']=='django__django-16333')
    lock=json.loads((FROZEN/'TASK_IDENTITY_LOCK.json').read_bytes())
    assert task['base_commit']==lock['base_commit'] and task['issue_sha256']==lock['issue_sha256']
    assert sha((data/task['snapshot_path']).read_bytes())==lock['snapshot_sha256']
    assert sha((data/task['diagnostic_path']).read_bytes())==lock['probe_sha256']
    deps=json.loads((data/'environments/dependency_lock.json').read_bytes())
    wheels=out/'task-wheels';wheels.mkdir()
    for name in deps['groups']['django']:
        record=deps['packages'][name];path=data/'wheels'/record['filename']
        assert sha(path.read_bytes())==record['sha256'];(wheels/path.name).symlink_to(path)
    source=restore(data/task['snapshot_path'],out/'restored',task['archive_root'])
    assert tree_identity(source)==lock['source_tree_before']
    from .source_observer import scan
    production=scan(source)
    write(out/'PRODUCTION_BASELINE.json',production)
    env=dict(os.environ,GIT_AUTHOR_NAME='Synthetic snapshot metadata',GIT_AUTHOR_EMAIL='cpu@example.invalid',
        GIT_COMMITTER_NAME='Synthetic snapshot metadata',GIT_COMMITTER_EMAIL='cpu@example.invalid',
        GIT_AUTHOR_DATE='2026-10-26T00:00:00+00:00',GIT_COMMITTER_DATE='2026-10-26T00:00:00+00:00')
    for command in (['init','-q'],['add','.'],['commit','-qm','Unmodified base content; synthetic research Git metadata']):
        subprocess.run(['git',*command],cwd=source,env=env,check=True,capture_output=True)
    snapshot=out/'django-base-flat.tgz'
    with tarfile.open(snapshot,'w:gz') as archive:
        for p in sorted(source.iterdir()):archive.add(p,arcname=p.name)
    cleanup(out/'restored',out)
    result=dict(data=str(data),task=task,wheels=str(wheels),snapshot=str(snapshot),
                regression=str(FROZEN/'private/regression.py'),production_baseline=str(out/'PRODUCTION_BASELINE.json'))
    write(out/'DATA_BINDING.json',dict(task_id=task['instance_id'],base_commit=task['base_commit'],
          source_tree_sha256=lock['source_tree_before'],snapshot_sha256=lock['snapshot_sha256'],
          issue_sha256=lock['issue_sha256'],diagnostic_sha256=lock['probe_sha256'],
          flattened_snapshot_sha256=sha(snapshot.read_bytes()),manifest_sha256=digest,
          original_source_unchanged=True,reference_columns_read=False))
    return result
