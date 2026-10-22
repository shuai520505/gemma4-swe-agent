"""One insertion only; reuse the frozen U-RE byte-preserving ZIP builder."""
import difflib
import hashlib
import json
from pathlib import Path
import zipfile

from u_re.v01.build import archive, write

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
PINS = {
    'noegv': '2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608',
    'full': '887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821',
}
MEMBERS = {'agent.yaml', 'eval_config.yaml', 'prompts/system.md'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def frozen():
    result = {}
    for arm, pin in PINS.items():
        path = BASE / ('submission_' + arm + '.zip')
        assert sha(path.read_bytes()) == pin, 'STOP: frozen candidate drift'
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None and set(z.namelist()) == MEMBERS
            result[arm] = {n: z.read(n) for n in z.namelist()}
        for n, data in result[arm].items():
            assert (BASE / ('candidate_' + arm) / n).read_bytes() == data
    return result


def build():
    originals = frozen()
    before = originals['noegv']['prompts/system.md']
    block = (HERE / 'ACTION_FIRST_INSTRUCTION_BLOCK.md').read_bytes()
    assert 100 <= len(block.decode().split()) <= 140
    assert block.endswith(b'\n') and b'{' not in block and b'}' not in block
    marker = b'Triage and repair:\n'
    assert before.count(marker) == 1 and block not in before
    after = before.replace(marker, block + b'\n' + marker, 1)
    assert after.replace(block + b'\n', b'', 1) == before
    files = dict(originals['noegv'], **{'prompts/system.md': after})
    for name, content in files.items():
        write(HERE / 'candidate_action_v01' / name, content)
    raw = archive(files)
    write(HERE / 'submission_action_v01.zip', raw)
    diff = ''.join(difflib.unified_diff(before.decode().splitlines(True),
        after.decode().splitlines(True), fromfile='Frozen-NoEGV/prompts/system.md',
        tofile='ActionFirst-V0.1/prompts/system.md'))
    write(HERE / 'CANDIDATE_EXACT.diff', diff.encode())
    result = dict(experiment_id='U-RE-V01-ACTION-FIRST-01',
        candidate='U-RE-NoEGV-ActionFirst-V0.1', parent_commit='b0e4ed05eb64fb0b52759ea63e18db8980723f0b',
        frozen_zip_sha256=PINS, zip_sha256=sha(raw),
        members={n: sha(b) for n, b in sorted(files.items())},
        changed_members=[n for n in files if files[n] != originals['noegv'][n]],
        factor='ACTION_FIRST_INSTRUCTION_BLOCK', factor_sha256=sha(block),
        insertion='Immediately before the unchanged Triage and repair heading',
        reversible_single_insertion=True, block_words=len(block.decode().split()),
        base_prompt_words=len(before.decode().split()), action_prompt_words=len(after.decode().split()),
        agent_count=1, model='gemma-4-31b-it-qat-w4a16-ct',
        budget=dict(seconds=300, charged_tools=60, command_seconds=120),
        generation='Byte-identical agent.yaml; output16384/thinking4096/seed17, omitted sampling/include_thoughts unchanged',
        official_compiler_status='See LOCAL_VALIDATION.md; build is not compiler acceptance',
        execute=False, gpu_authorized=False, formal_submission=False)
    write(HERE / 'CANDIDATE_AUDIT.json', (json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    build()
