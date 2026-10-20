"""Seal new diagnostic evidence and link immutable originals; no historical writes."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def record(p):
    raw=p.read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def main():
    previous=json.loads((HERE/'evidence/INITIAL_HISTORY.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in previous['files'].items())
    original_names=['u_re/v01/INTEGRITY_MANIFEST.json','u_re/v01/CANDIDATES.json',
                    'u_re/v01/GPU_EXPERIMENT_PROTOCOL_DRAFT.json','u_re/v01/results/cpu02/raw.zip',
                    'u_re/v01/results/cpu03/raw.zip','u_re/v01/results/cpu03/validation/task_identities.json',
                    'u_re/v01/results/cpu03/validation/requests_7433/phase2.junit.xml',
                    'u_re/v01/results/cpu03/validation/requests_7433/phase2_command.json',
                    'u_re/v01/submission_noegv.zip','u_re/v01/submission_full.zip']
    members={}
    for arm in ('noegv','full'):
        with zipfile.ZipFile(ROOT/f'u_re/v01/submission_{arm}.zip') as z:
            assert z.testzip() is None
            members[arm]={n:dict(bytes=len(z.read(n)),sha256=hashlib.sha256(z.read(n)).hexdigest()) for n in z.namelist()}
    files={}
    for p in sorted(HERE.rglob('*')):
        rel=p.relative_to(HERE)
        if not p.is_file() or p.name=='INTEGRITY_MANIFEST.json' or {'__pycache__','.pytest_cache','download','_local'}.intersection(rel.parts):continue
        files[rel.as_posix()]=record(p)
    result=dict(experiment='requests_7433_fixture_01',base=previous['base'],outcome='ENVIRONMENT_BLOCKED',
                files=files,linked_frozen_files={n:record(ROOT/n) for n in original_names},
                task_identity=json.loads((HERE/'expected_task.json').read_text()),
                frozen_zip_members=members,history_files_checked=len(previous['files']),
                CPU_only=True,Agent_runs=0,model_calls=0,GPU_started=False,formal_submission=False,
                exclusions=['This manifest itself','__pycache__','.pytest_cache','download','_local'],
                raw_archive_completeness='results/cpu01/raw.zip has its own complete verified312-file manifest; no excluded cache hides a changed original')
    with (HERE/'INTEGRITY_MANIFEST.json').open('x') as out:json.dump(result,out,indent=2)
    print(json.dumps(dict(new_files=len(files),history_files_checked=len(previous['files']),outcome=result['outcome'])))


if __name__=='__main__':main()
