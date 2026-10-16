"""Freeze a V0-derived first-score candidate and a packaging-only Notebook."""
import base64
import hashlib
import json
from pathlib import Path
import zipfile

from experiments.prepare import ROOT, MEMBERS, archive_bytes, write_new
from harness_v2.integrity import verify_baseline

EVALUATION = dict(timeout_seconds=120, max_tool_calls=60, max_time_minutes=5.0)


def check(directory):
    import yaml
    directory = Path(directory)
    files = {p.relative_to(directory).as_posix(): p.read_bytes()
             for p in directory.rglob('*') if p.is_file()}
    assert set(files) == set(MEMBERS)
    assert not any(p.is_symlink() for p in directory.rglob('*'))
    for name in ('agent.yaml', 'prompts/system.md'):
        assert files[name] == (ROOT/'candidates/v0/submission'/name).read_bytes()
    assert yaml.safe_load(files['eval_config.yaml']) == {'evaluation': EVALUATION}
    return files


def compile_official(directory):
    from adk_submission import ModelRegistry, compile_submission, validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    from scripts.agent_config import MODEL, TOOLS
    check(directory)
    limits, constraints = build_submission_limits()
    validate_directory(directory, limits=limits)
    models = ModelRegistry()
    models.register(MODEL, LiteLlm(model='openai/'+MODEL,
        api_base='http://127.0.0.1:8000/v1', api_key='EMPTY'))
    agent = compile_submission(directory, SwegemmaContext().create_tools(), models,
        limits=limits, generation_constraints=constraints)
    assert agent.model.model == 'openai/'+MODEL
    assert not agent.sub_agents and [t.__name__ for t in agent.tools] == TOOLS
    assert agent.generate_content_config.max_output_tokens == 16384
    return agent


def build():
    verify_baseline()
    target = ROOT/'candidates/s0/submission'
    for name in ('agent.yaml', 'prompts/system.md'):
        write_new(target/name, (ROOT/'candidates/v0/submission'/name).read_bytes())
    write_new(target/'eval_config.yaml', b'evaluation:\n  timeout_seconds: 120\n  max_tool_calls: 60\n  max_time_minutes: 5.0\n')
    files = check(target)
    data = archive_bytes(files)
    write_new(ROOT/'candidates/s0/submission.zip', data)
    digest = hashlib.sha256(data).hexdigest()
    manifest = dict(candidate='s0', parent='v0', prompt_changed=False,
        evaluation=EVALUATION, source_hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},
        zip_sha256=digest, zip_bytes=len(data), official_score=None,
        budget_status='initial_candidate_not_an_optimum', harness_controller_in_submission=False)
    write_new(ROOT/'candidates/s0/manifest.json', (json.dumps(manifest,indent=2)+'\n').encode())
    code=f'''import base64,hashlib,io,zipfile
from pathlib import Path
data=base64.b64decode({base64.b64encode(data).decode()!r},validate=True)
assert hashlib.sha256(data).hexdigest()=={digest!r}
with zipfile.ZipFile(io.BytesIO(data)) as z:
    assert z.testzip() is None
    assert set(z.namelist())=={{'agent.yaml','eval_config.yaml','prompts/system.md'}}
    assert 'agent.yaml' in z.namelist()
output=Path('/kaggle/working/submission.zip')
with output.open('xb') as f: f.write(data)
print('S0 submission.zip',len(data),hashlib.sha256(data).hexdigest())
'''
    nb=dict(cells=[dict(cell_type='markdown',metadata={},source='# S0 first leaderboard probe\nPackaging only. No model inference or development evaluation.'),
        dict(cell_type='code',metadata={},source=code,outputs=[],execution_count=None)],
        metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3')),nbformat=4,nbformat_minor=5)
    for c in nb['cells']:c['id']=hashlib.sha256(c['source'].encode()).hexdigest()[:12]
    write_new(ROOT/'candidates/s0/notebook/submission.ipynb',(json.dumps(nb,indent=1)+'\n').encode())
    meta=json.loads((ROOT/'artifacts/harness-v2/r12/gpu-kernel/kernel-metadata.json').read_text())
    meta.update(id='wudangdexiaodoashi/gemma4-s0-first-submission',title='Gemma4 S0 First Submission',
        code_file='submission.ipynb',enable_gpu=False,dataset_sources=[],model_sources=[])
    meta.pop('machine_shape',None)
    write_new(ROOT/'candidates/s0/notebook/kernel-metadata.json',(json.dumps(meta,indent=2)+'\n').encode())
    return manifest


if __name__=='__main__': print(json.dumps(build(),indent=2))
