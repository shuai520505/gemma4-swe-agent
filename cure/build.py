"""Allowlisted Agent ZIPs and a separate embedded CPU research validation Notebook."""
import argparse
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile
from harness_v2.integrity import verify_baseline
from .runtime_config import ResearchConfig
from . import VERSION

ROOT = Path(__file__).resolve().parents[1]
AGENT_FILES = ('agent.yaml', 'eval_config.yaml', 'sampling.yaml', 'prompts/system.md')


def archive(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    return out.getvalue()


def write_new(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() == data: return
        raise FileExistsError(path)
    with path.open('xb') as f: f.write(data)


def build(revision):
    verify_baseline()
    if not revision.replace('-', '').isalnum(): raise ValueError('Invalid revision')
    registration = ROOT / 'cure/registrations' / f'{revision}.json'
    if registration.exists(): raise FileExistsError(registration)
    candidates = {}
    for arm in ('checklist', 'cure_v01'):
        path = ROOT / 'cure/candidates' / arm
        files = {n: (path / n).read_bytes() for n in AGENT_FILES}
        data = archive(files); write_new(ROOT / 'cure/packages' / arm / 'submission.zip', data)
        candidates[arm] = dict(zip_sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
            members={n: hashlib.sha256(b).hexdigest() for n, b in files.items()})
    files = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in (ROOT / 'harness_v2').glob('*.py')}
    files.update({p.relative_to(ROOT).as_posix(): p.read_bytes() for p in (ROOT / 'cure').glob('*.py')})
    files.update({p.relative_to(ROOT).as_posix(): p.read_bytes() for p in (ROOT / 'cure/tests').glob('*.py')})
    for name in ('install_official.py', 'cpu-metadata-template.json'):
        rel = 'cure/notebooks/' + name; files[rel] = (ROOT / rel).read_bytes()
    for name in ('test_harness_v2.py', 'test_harness_v2_official.py', 'test_harness_v2_isolation.py', 'harness_v2_fixture.py', 'test_official_tools.py'):
        files['tests/' + name] = (ROOT / 'tests' / name).read_bytes()
    for arm in ('v0', 'v1'):
        for name in ('agent.yaml', 'eval_config.yaml', 'prompts/system.md'):
            rel = f'candidates/{arm}/submission/{name}'; files[rel] = (ROOT / rel).read_bytes()
    for arm in candidates:
        for name in AGENT_FILES:
            rel = f'cure/candidates/{arm}/{name}'; files[rel] = (ROOT / rel).read_bytes()
        rel = f'cure/packages/{arm}/submission.zip'; files[rel] = (ROOT / rel).read_bytes()
    plan = dict(version=VERSION, revision=revision, purpose='CPU mechanism and official API validation only',
        origin_commit='972d1dd940db3910dd78685d6e37152e96ab514b', config=ResearchConfig().snapshot(), candidates=candidates,
        source_hashes={n: hashlib.sha256(b).hexdigest() for n, b in files.items()})
    raw = (json.dumps(plan, indent=2) + '\n').encode(); write_new(registration, raw)
    files[f'cure/registrations/{revision}.json'] = raw
    payload = archive(files); digest = hashlib.sha256(payload).hexdigest()
    base = ROOT / 'artifacts/cure-v01' / revision
    write_new(base / 'research.bundle', payload)
    setup = f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil
from pathlib import Path
from datetime import datetime,timezone
RUN_DIR=Path('/kaggle/working/cure_cpu')/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode('{base64.b64encode(payload).decode()}')
assert hashlib.sha256(payload).hexdigest()=='{digest}'
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
'''
    install = (ROOT / 'cure/notebooks/install_official.py').read_text(encoding='utf-8')
    run = f'''try:
    p=subprocess.run([sys.executable,'-m','cure.cpu_validation','{revision}',str(RUN_DIR/'validation')],cwd=SOURCE,capture_output=True,text=True,timeout=1200)
    (RUN_DIR/'runner.stdout.log').write_text(p.stdout)
    (RUN_DIR/'runner.stderr.log').write_text(p.stderr)
    print(p.stdout,flush=True)
    assert p.returncode==0,'CPU validation failed; no GPU launch authorized'
finally:
    print('CURE_CPU_EVIDENCE',shutil.make_archive(str(RUN_DIR),'zip',root_dir=RUN_DIR),flush=True)
'''
    cells = []
    for code in (setup, install, run):
        compile(code, '<cpu-cell>', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code', metadata={}, source=code, outputs=[], execution_count=None))
    nb = dict(cells=cells, metadata=dict(kernelspec=dict(display_name='Python 3', language='python', name='python3')), nbformat=4, nbformat_minor=5)
    write_new(base / 'kernel/cpu.ipynb', json.dumps(nb, indent=1).encode())
    meta = json.loads((ROOT / 'cure/notebooks/cpu-metadata-template.json').read_text())
    meta.update(id=f'wudangdexiaodoashi/gemma4-cure-v01-{revision}', title=f'Gemma4 CURE V01 {revision}', code_file='cpu.ipynb')
    meta['dataset_sources'] = ['metric/gemma-4-developer-agent-wheelhouse']
    meta['model_sources'] = []; meta['enable_gpu'] = False
    write_new(base / 'kernel/kernel-metadata.json', json.dumps(meta, indent=2).encode())
    write_new(ROOT / 'cure/notebooks' / f'{revision}.ipynb', json.dumps(nb, indent=1).encode())
    write_new(ROOT / 'cure/notebooks' / f'{revision}-metadata.json', json.dumps(meta, indent=2).encode())
    print(json.dumps(dict(revision=revision, candidates=candidates, cpu_payload_sha256=digest), indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('revision'); build(p.parse_args().revision)
