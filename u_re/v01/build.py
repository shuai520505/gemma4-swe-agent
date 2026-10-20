"""Deterministic paired packages; no evaluator/control code in either ZIP."""
import difflib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S1 = 'b80565a71395c4d1c012a9bfea3e561ddab255db'
S0 = '972d1dd940db3910dd78685d6e37152e96ab514b'
MEMBERS = ('agent.yaml', 'eval_config.yaml', 'prompts/system.md')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise FileExistsError(f'Version rather than overwrite frozen artifact: {path}')
    path.write_bytes(data)


def archive(files):
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 20, 0, 0, 0))
            # Explicitly preserve the initially frozen Windows-created header.
            # ZipInfo otherwise chooses0 on Windows and3 on Linux.
            info.create_system = 0
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    return result.getvalue()


def git_bytes(revision, path):
    return subprocess.check_output(['git', 'show', f'{revision}:{path}'], cwd=ROOT)


def package():
    prefix, egv, suffix = [(HERE/'prompts'/name).read_text(encoding='utf-8').strip()
                           for name in ('common_prefix.md', 'egv.md', 'common_suffix.md')]
    shared = {n: git_bytes(S1, 's1/egv_v01/candidate/'+n) for n in MEMBERS[:2]}
    result = {}
    for arm, middle in (('noegv', []), ('full', [egv])):
        prompt = '\n\n'.join([prefix, *middle, suffix])+'\n'
        assert '{' not in prompt and '}' not in prompt
        files = {**shared, MEMBERS[2]: prompt.encode()}
        target = HERE/('candidate_'+arm)
        for name, data in files.items():
            write(target/name, data)
        raw = archive(files)
        write(HERE/('submission_'+arm+'.zip'), raw)
        result[arm] = dict(zip_sha256=sha(raw), members={n:sha(b) for n,b in files.items()},
                           prompt_words=len(prompt.split()), agent_count=1, GPU_status='GPU_NOT_TESTED')
    no, full = [(HERE/('candidate_'+a)/MEMBERS[2]).read_text() for a in ('noegv','full')]
    assert full.replace(egv+'\n\n','',1) == no
    diff = ''.join(difflib.unified_diff(no.splitlines(True), full.splitlines(True),
                                      fromfile='U-RE-NoEGV', tofile='U-RE-Full'))
    write(HERE/'CANDIDATE_EXACT.diff', diff.encode())
    audit = dict(source_commit=S1, source_paths=['s1/egv_v01/candidate/'+n for n in MEMBERS],
        candidates=result, changed_members=['prompts/system.md'], only_treatment='EGV block inserted between identical common sections',
        common_prefix_sha256=sha(prefix.encode()), common_suffix_sha256=sha(suffix.encode()),
        egv_block_sha256=sha(egv.encode()), model='gemma-4-31b-it-qat-w4a16-ct',
        budget=dict(agent_seconds=300, counted_tools=60, command_seconds=120),
        generation=dict(max_output_tokens=16384, thinking_budget=4096, seed=17,
                        include_thoughts='omitted', sampling='omitted'),
        executable_submission_members=0, external_controller=False)
    write(HERE/'CANDIDATES.json', (json.dumps(audit,indent=2)+'\n').encode())
    baselines = {'s0':git_bytes(S0,'candidates/s0/submission/prompts/system.md'),
                 's1':git_bytes(S1,'s1/egv_v01/candidate/prompts/system.md')}
    prompt_data = dict(baselines, noegv=no.encode(), full=full.encode())
    write(HERE/'PROMPT_LENGTHS_PRE_CPU.json', (json.dumps({a:dict(bytes=len(b),sha256=sha(b),
        words=len(b.decode().split()),tokens=None,token_status='TOKENIZER_CPU_MEASUREMENT_PENDING')
        for a,b in prompt_data.items()},indent=2)+'\n').encode())
    print(json.dumps(audit,indent=2))


if __name__ == '__main__':
    package()
