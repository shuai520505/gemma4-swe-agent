"""Build versioned infrastructure inputs; refuse to replace any prior bundle."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

from experiments.prepare import ROOT,archive_bytes,write_new
from .integrity import verify_baseline
from .budgets import Budgets
from . import VERSION


def cell(source):
    compile(source,'<harness-v2-notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    return dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None)


def build(revision):
    verify_baseline()
    base=ROOT/'artifacts/harness-v2'/revision
    tests=['test_harness_v2.py','test_harness_v2_official.py','test_harness_v2_isolation.py','harness_v2_fixture.py','test_official_tools.py']
    files={p.relative_to(ROOT).as_posix():p.read_bytes() for p in (ROOT/'harness_v2').glob('*.py')}
    files.update({f'tests/{n}':(ROOT/'tests'/n).read_bytes() for n in tests})
    candidates={f'candidates/{a}/submission/{n}':(ROOT/'candidates'/a/'submission'/n).read_bytes()
        for a in ('v0','v1') for n in ('agent.yaml','eval_config.yaml','prompts/system.md')}
    files.update(candidates)
    hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
    plan=dict(schema_version=2,harness_version=VERSION,experiment_id='harness-v2-infra-dev-02',
        revision=revision,purpose='infrastructure development; no repair-rate inference',
        cpu_must_pass_before_gpu=True,budget=Budgets().as_dict(),model='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',
        tasks=[dict(index=1,arm='v0',instance_id='requests_7315'),dict(index=2,arm='v1',instance_id='rich_3777')],
        source_hashes=hashes,formal_comparison_status='draft_not_registered_not_executed')
    # Task identities and original issue hashes only. Never copy solutions/hints/tests.
    task_rows={r['instance_id']:r for r in map(json.loads,(ROOT.parent/'official-inputs/tasks.jsonl').read_text(encoding='utf-8').splitlines())}
    for t in plan['tasks']:
        task=task_rows[t['instance_id']]
        t.update(repo=task['repo'],base_commit=task['base_commit'],
            problem_sha256=hashlib.sha256(task['problem_statement'].encode()).hexdigest())
    files['infra_plan.json']=(json.dumps(plan,indent=2)+'\n').encode()
    payload=archive_bytes(files)
    write_new(base/'input/harness-v2.bundle',payload)
    write_new(base/'input/dataset-metadata.json',(json.dumps(dict(id='wudangdexiaodoashi/gemma4-harness-v2-private-input',
        title='Gemma4 Harness V2 Infrastructure Input',isPrivate=True,licenses=[dict(name='CC0-1.0')]),indent=2)+'\n').encode())
    write_new(ROOT/'harness_v2/registrations'/f'{revision}.json',(json.dumps(plan,indent=2)+'\n').encode())
    digest=hashlib.sha256(payload).hexdigest()
    setup=f'''import os,sys,json,hashlib,zipfile,subprocess,shutil,time
from pathlib import Path
from datetime import datetime,timezone
RUN_DIR=Path('/kaggle/working/harness_v2_cpu')/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payloads=list(Path('/kaggle/input').rglob('harness-v2.bundle'))
assert len(payloads)==1
assert hashlib.sha256(payloads[0].read_bytes()).hexdigest()=='{digest}'
with zipfile.ZipFile(payloads[0]) as z:
    assert z.testzip() is None
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
plan=json.loads((SOURCE/'infra_plan.json').read_text())
for name,digest in plan['source_hashes'].items():
    assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==digest
(RUN_DIR/'infra_plan.json').write_text(json.dumps(plan,indent=2))
print('CPU infrastructure only:',RUN_DIR,flush=True)
'''
    install='''import glob
os.environ.update(TRANSFORMERS_NO_TF='1',TRANSFORMERS_NO_FLAX='1',TRANSFORMERS_OFFLINE='1',HF_HUB_OFFLINE='1',LITELLM_LOCAL_MODEL_COST_MAP='True',LITELLM_TELEMETRY='False',OTEL_SDK_DISABLED='true',PYTHONIOENCODING='utf-8')
for pattern in ('/usr/local/lib/python*/dist-packages/*cutlass*.pth','/usr/local/lib/python*/site-packages/*cutlass*.pth'):
    for path in glob.glob(pattern): Path(path).unlink(missing_ok=True)
wheels=list(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl'))
assert len(wheels)==1
wheelhouse=wheels[0].parent
links=RUN_DIR/'wheelhouse_links'; links.mkdir()
for p in wheelhouse.glob('*.whl'):
    if 'cutlass' in p.name.lower(): continue
    name=p.name.replace('cu128','+cu128') if 'cu128' in p.name and '+' not in p.name else p.name
    (links/name).symlink_to(p)
pins=['swegemma-0.2.11-py3-none-any.whl','adk_submission-0.2.13-py3-none-any.whl','adk_eval_core-0.1.0-py3-none-any.whl','google_adk-1.36.1-py3-none-any.whl','google_genai-2.11.0-py3-none-any.whl']
try:
    with (RUN_DIR/'installation.log').open('x') as log:
        # Match official Getting Started: curated wheels, no dependency resolver.
        subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps','--force-reinstall']+
            sorted(str(p) for p in links.glob('*.whl')),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
finally:
    shutil.rmtree(links)
'''
    run='''try:
    result=subprocess.run([sys.executable,'-m','harness_v2.cpu_validation',str(RUN_DIR/'validation')],cwd=SOURCE,capture_output=True,text=True,timeout=1200)
    (RUN_DIR/'runner.stdout.log').write_text(result.stdout)
    (RUN_DIR/'runner.stderr.log').write_text(result.stderr)
    print(result.stdout,flush=True)
    assert result.returncode==0,'CPU gate failed; inspect preserved logs. GPU forbidden.'
finally:
    archive=shutil.make_archive(str(RUN_DIR),'zip',root_dir=RUN_DIR)
    print('CPU evidence',archive,flush=True)
'''
    notebook=dict(cells=[dict(cell_type='markdown',metadata={},source='# Harness V2 CPU gate\nNo GPU, model inference, or task repair score.'),
        cell(setup),cell(install),cell(run)],metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3')),nbformat=4,nbformat_minor=5)
    write_new(base/'cpu-kernel/cpu.ipynb',(json.dumps(notebook,indent=1)+'\n').encode())
    old=json.loads((ROOT/'artifacts/v1-pilot/kernel/kernel-metadata.json').read_text())
    old.update(id='wudangdexiaodoashi/gemma4-harness-v2-cpu-validation',title='Gemma4 Harness V2 CPU Validation',
        code_file='cpu.ipynb',enable_gpu=False,dataset_sources=['metric/gemma-4-developer-agent-wheelhouse',
        'wudangdexiaodoashi/gemma4-harness-v2-private-input'],model_sources=[],competition_sources=[])
    old.pop('machine_shape',None)
    write_new(base/'cpu-kernel/kernel-metadata.json',(json.dumps(old,indent=2)+'\n').encode())
    print(json.dumps(dict(revision=revision,payload_sha256=hashlib.sha256(payload).hexdigest(),
        cpu_notebook=str(base/'cpu-kernel/cpu.ipynb'),gpu_status='not_launched_cpu_gate_required'),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('revision')
    build(p.parse_args().revision)
