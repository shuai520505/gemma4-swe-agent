"""Freeze a prompt-only comparison without mounting audit/reference material."""
import ast
import hashlib
import json
from pathlib import Path
import random
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MEMBERS = ('agent.yaml', 'eval_config.yaml', 'prompts/system.md')
TASKS = (
    ('fastapi_15589', 'request validation'),
    ('requests_7315', 'URL normalization'),
    ('rich_3777', 'terminal environment configuration'),
    ('rich_4006', 'Unicode termination/algorithm'),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise FileExistsError(f'Refusing to replace frozen artifact: {path}')
        return
    with path.open('xb') as f:
        f.write(data)


def archive_bytes(files):
    import io
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    return stream.getvalue()


def verify_frozen(root=ROOT):
    p = root / 'experiments/v0_frozen.json'
    manifest = json.loads(p.read_text(encoding='utf-8'))
    for name, digest in manifest['files'].items():
        if sha((root / name).read_bytes()) != digest:
            raise ValueError(f'V0 evidence changed: {name}')
    return len(manifest['files'])


def prepare():
    source = ROOT / 'artifacts/kaggle-single/output-v2/v0_runs/20261014T161032_870715Z'
    protected = [ROOT / 'submission.zip', source.with_suffix('.zip')]
    protected += [p for p in source.rglob('*') if p.is_file()]
    protected += [p for p in (ROOT / 'submission').rglob('*') if p.is_file()]
    protected += [p for p in (ROOT / 'candidates/v0').rglob('*') if p.is_file()]
    manifest = {'base_commit': 'b056420', 'files': {
        p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(protected)}}
    write_new(ROOT / 'experiments/v0_frozen.json',
              (json.dumps(manifest, indent=2) + '\n').encode())
    verify_frozen()
    for name in MEMBERS:
        assert (ROOT / 'candidates/v0/submission' / name).read_bytes() == (ROOT / 'submission' / name).read_bytes()
    for name in ('agent.yaml', 'eval_config.yaml'):
        assert (ROOT / 'candidates/v0/submission' / name).read_bytes() == (ROOT / 'candidates/v1/submission' / name).read_bytes()
    prompt = (ROOT / 'candidates/v1/submission/prompts/system.md').read_text(encoding='utf-8')
    for forbidden in ('fastapi', '15661', 'prepare_release', 'PREPARE_RELEASE', 'release.py', 'asyncer'):
        assert forbidden not in prompt, f'Task-specific prompt content: {forbidden}'
    rows = {t['instance_id']: t for t in map(json.loads, (ROOT.parent / 'official-inputs/tasks.jsonl').read_text(encoding='utf-8').splitlines())}
    # Only public metadata and the original problem statement are inspected for selection.
    # Never copy patch/test_patch/hints or reference solutions into the payload.
    selected = [dict(instance_id=i, category=c, repo=rows[i]['repo'], base_commit=rows[i]['base_commit'],
                     problem_sha256=sha(rows[i]['problem_statement'].encode())) for i, c in TASKS]
    rng = random.Random(20261015)
    rng.shuffle(selected)
    schedule = []
    for n, task in enumerate(selected):
        arms = ['v0', 'v1'] if n % 2 == 0 else ['v1', 'v0']
        first_index = len(schedule) + 1
        schedule.extend(dict(index=first_index + j, arm=arm, **task) for j, arm in enumerate(arms))
    payload = {}
    for arm in ('v0', 'v1'):
        directory = ROOT / 'candidates' / arm / 'submission'
        files = {name: (directory / name).read_bytes() for name in MEMBERS}
        if arm == 'v1':
            write_new(ROOT / 'candidates/v1/submission.zip', archive_bytes(files))
        payload.update({f'{arm}/{name}': data for name, data in files.items()})
    plan = dict(schema_version=1, experiment='v1-prompt-pilot-01', seed=20261015,
                historical_task_excluded='fastapi_15661', repeats=1,
                model='gemma-4-31b-it-qat-w4a16-ct', model_version=2,
                profile=dict(max_time_minutes=8.0, max_tool_calls=60, timeout_seconds=120,
                             verification_timeout_seconds=300, max_tasks=8, task_wall_minutes=12.0),
                schedule=schedule, source_hashes={k: sha(v) for k, v in payload.items()},
                inference_status='not_executed_at_registration', competition_score=None)
    plan_data = (json.dumps(plan, indent=2) + '\n').encode()
    write_new(ROOT / 'experiments/preregistered.json', plan_data)
    payload['experiment.json'] = plan_data
    write_new(ROOT / 'artifacts/v1-pilot/input/submission.bundle', archive_bytes(payload))
    print(json.dumps({'frozen_files': verify_frozen(), 'runs': len(schedule),
                      'payload_sha256': sha((ROOT / 'artifacts/v1-pilot/input/submission.bundle').read_bytes())}, indent=2))


if __name__ == '__main__':
    prepare()
