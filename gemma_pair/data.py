import json
import os
from pathlib import Path
import subprocess
import tarfile

from egrd.v03.runtime import restore,tree_identity,cleanup
from .common import ROOT,HERE,sha,write

def prepare(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    lock=json.loads((ROOT/'egrd/v03/DATASET_BUILD_V1.json').read_bytes())
    matches=[p for p in Path('/kaggle/input').rglob('MANIFEST.json')
             if 'egrd-repair-development' in str(p) and sha(p.read_bytes())==lock['manifest_sha256']]
    assert len(matches)==1,'Expected immutable public development bundle not mounted'
    data=matches[0].parent;manifest=json.loads(matches[0].read_bytes())
    for n,h in manifest['files'].items():assert sha((data/n).read_bytes())==h,n
    registry=json.loads((data/'metadata/task_registry.json').read_bytes())
    issues=json.loads((HERE/'ISSUES.json').read_bytes())
    deps=json.loads((data/'environments/dependency_lock.json').read_bytes())
    results={}
    for task in registry['tasks']:
        ident=task['instance_id'];folder=out/ident;folder.mkdir()
        issue=issues[ident]
        assert sha(issue['problem_statement'].encode())==task['issue_sha256']
        assert issue['base_commit']==task['base_commit'] and issue['repo']==task['repo']
        assert set(issue)=={'instance_id','repo','base_commit','problem_statement'}
        wheels=folder/'wheels';wheels.mkdir()
        for name in deps['groups'][task['environment_group']]:
            record=deps['packages'][name];path=data/'wheels'/record['filename']
            assert sha(path.read_bytes())==record['sha256'];(wheels/path.name).symlink_to(path)
        source=restore(data/task['snapshot_path'],folder/'restored',task['archive_root'])
        identity=tree_identity(source)
        env=dict(os.environ,GIT_AUTHOR_NAME='Research snapshot',GIT_AUTHOR_EMAIL='research@example.invalid',
            GIT_COMMITTER_NAME='Research snapshot',GIT_COMMITTER_EMAIL='research@example.invalid',
            GIT_AUTHOR_DATE='2026-10-30T00:00:00+00:00',GIT_COMMITTER_DATE='2026-10-30T00:00:00+00:00')
        # A large source commit otherwise launches asynchronous git gc, which
        # can remove loose objects while the baseline archive is being written.
        commands=(['init','-q'],['config','gc.auto','0'],['config','maintenance.auto','false'],
                  ['add','.'],['commit','-qm','Unmodified base snapshot'])
        for command in commands:
            subprocess.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*command],
                           cwd=source,env=env,check=True,capture_output=True)
        snapshot=folder/'base-flat.tgz'
        with tarfile.open(snapshot,'w:gz') as archive:
            for p in sorted(source.iterdir()):archive.add(p,arcname=p.name)
        cleanup(folder/'restored',folder)
        taskfile=folder/'task.json';write(taskfile,issue)
        record=dict(task=task,issue=issue,taskfile=str(taskfile),data=str(data),snapshot=str(snapshot),
                    wheels=str(wheels),base_source_identity=identity)
        write(folder/'DATA_BINDING.json',record);results[ident]=record
    write(out/'DATA_RESULTS.json',results)
    return results
