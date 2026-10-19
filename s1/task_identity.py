"""Hash public task inputs without exposing reference/test patches to the Agent."""
import json
from pathlib import Path
from .util import sha,sha_file


def identify(data,selection):
    from swegemma.deduplication import resolve_task_snapshot_paths
    data=Path(data)
    rows={r['instance_id']:r for r in map(json.loads,(data/'tasks.jsonl').read_text().splitlines())}
    result={}
    for ident in selection:
        row=rows[ident]
        snapshot,base,patch=resolve_task_snapshot_paths(data/'snapshots',ident,row['repo'])
        assert snapshot.is_file(),ident
        paths={p.relative_to(data).as_posix():sha_file(p) for p in (snapshot,base,patch) if p is not None}
        result[ident]=dict(instance_id=ident,repo=row['repo'],base_commit=row['base_commit'],
            issue_sha256=sha(row['problem_statement'].encode()),input_files=paths,
            task_record_sha256=sha(json.dumps(row,sort_keys=True).encode()),
            test_patch_sha256=sha((row.get('test_patch') or '').encode()))
    return result


def find_data():
    paths=[p.parent for p in Path('/kaggle/input').rglob('tasks.jsonl') if (p.parent/'snapshots').is_dir()]
    assert len(paths)==1,paths
    return paths[0]
