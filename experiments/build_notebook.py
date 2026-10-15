"""Build a new comparison Notebook; never rewrite the V0 Notebook."""
import ast
import hashlib
import json
from pathlib import Path

from experiments.prepare import ROOT, write_new
from scripts.build_kaggle_notebook import INSTALL, PREFLIGHT, SERVER

SETUP = '''INPUT_ROOT = Path('/kaggle/input')
WORKING_DIR = Path('/kaggle/working')
SESSION_STARTED = time.monotonic()
RUN_DIR = WORKING_DIR / 'v1_pilot' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
RUN_DIR.mkdir(parents=True, exist_ok=False)
server_instance = None
try:
    inputs = discover_inputs(INPUT_ROOT)
    ARMS_DIR = RUN_DIR / 'arms'
    PLAN = unpack_experiment(inputs['zip'], ARMS_DIR)
    profile = PLAN['profile']
    DATA_DIR, WHEELHOUSE_DIR, MODEL_PATH = inputs['data'], inputs['wheelhouse'], inputs['model']
    AGENT_DIR = ARMS_DIR / 'v0'
    TASK_INSTANCE_ID = None
    write_json(RUN_DIR / 'registered_plan.json', PLAN)
    write_json(RUN_DIR / 'manifest.json', dict(model=MODEL_NAME, inputs=inputs,
        payload_sha256=hashlib.sha256(inputs['zip'].read_bytes()).hexdigest(),
        experiment=PLAN['experiment'], profile=profile, competition_score=None))
    print('EVIDENCE DIRECTORY', RUN_DIR, flush=True)
except BaseException as exc:
    exception_record(RUN_DIR, 'comparison_inputs', exc)
    print('EVIDENCE ZIP', bundle_run(RUN_DIR), flush=True)
    raise
'''

SELECTION = '''    task_by_id = {t.instance_id: t for t in tasks}
    selected = []
    for row in PLAN['schedule']:
        task = task_by_id[row['instance_id']]
        assert task.base_commit == row['base_commit'], 'Official task base changed'
        assert hashlib.sha256(task.problem_statement.encode()).hexdigest() == row['problem_sha256'], 'Task prompt changed'
        if task not in selected:
            selected.append(task)
'''


def build():
    preflight = PREFLIGHT
    start = preflight.index('    if TASK_INSTANCE_ID is not None:')
    end = preflight.index('    for task in selected:', start)
    preflight = preflight[:start] + SELECTION + preflight[end:]
    helper = (ROOT / 'notebooks/kaggle_support.py').read_text(encoding='utf-8')
    metrics = (ROOT / 'experiments/metrics.py').read_text(encoding='utf-8')
    runtime = (ROOT / 'experiments/runtime.py').read_text(encoding='utf-8')
    sections = [('Controller and metrics', helper + '\n' + metrics + '\n' + runtime),
                ('Frozen paired experiment input', SETUP), ('Official offline installation', INSTALL),
                ('Official task and model preflight', preflight), ('Shared 31B server', SERVER),
                ('Sequential paired runs, fresh task contexts', 'await run_comparison()\n')]
    cells = [dict(cell_type='markdown', metadata={}, source='# V1 prompt-only paired pilot\n4 new public tasks, 8 runs; no audited task, reference answer, or audit notes are mounted.\nA completed execution is not a passing repair.')]
    for label, source in sections:
        compile(source, '<comparison>', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='markdown', metadata={}, source='## ' + label))
        cells.append(dict(cell_type='code', metadata={}, source=source, outputs=[], execution_count=None))
    return dict(cells=cells, metadata={'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}}, nbformat=4, nbformat_minor=5)


if __name__ == '__main__':
    data = (json.dumps(build(), indent=1) + '\n').encode()
    write_new(ROOT / 'experiments/v1_pilot.ipynb', data)
    print('Notebook SHA-256', hashlib.sha256(data).hexdigest())
