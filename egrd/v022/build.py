"""Only prompts differ; reuse the original immutable MEER ZIP writer."""
import difflib
import io
import json
from pathlib import Path
import zipfile

from meer.v01.build import archive, frozen_write, sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE_SHA = 'd962044f264d8f36aea6263abf4dcdb118d5755e82a91cb9b2bd0bc1f6f7c9cd'
ANCHOR = b'\n\nEvidence-guided repair:\n'
PROMPT = 'prompts/system.md'


def original():
    raw = (ROOT / 'meer/v01/submission_B.zip').read_bytes()
    assert sha(raw) == BASE_SHA
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None and len(z.namelist()) == len(set(z.namelist())) == 5
        files = {n: z.read(n) for n in z.namelist()}
    assert files[PROMPT].count(ANCHOR) == 1
    return files


def variants():
    base = original()
    result = {}
    for arm in ('N', 'D'):
        cue = (HERE / 'instructions' / (arm + '.txt')).read_bytes()
        assert b'\r' not in cue and cue.endswith(b'\n')
        files = dict(base)
        files[PROMPT] = base[PROMPT].replace(ANCHOR, b'\n\n' + cue.rstrip() + ANCHOR, 1)
        result[arm] = files
    changed = [n for n in base if result['N'][n] != result['D'][n]]
    assert changed == [PROMPT]
    for name in base:
        if name != PROMPT:
            assert result['N'][name] == result['D'][name] == base[name]
    return result


def build():
    files = variants()
    records = {}
    for arm in ('N', 'D'):
        packed = archive(files[arm])
        frozen_write(HERE / f'submission_{arm}.zip', packed)
        with zipfile.ZipFile(io.BytesIO(packed)) as z:
            assert z.testzip() is None and set(z.namelist()) == set(original())
        cue = (HERE / 'instructions' / (arm + '.txt')).read_text(encoding='utf-8')
        records[arm] = dict(ZIP_sha256=sha(packed), bytes=len(packed),
            members={name: dict(sha256=sha(body), bytes=len(body)) for name, body in sorted(files[arm].items())},
            cue_text=cue, cue_sha256=sha(cue.encode()), cue_words=len(cue.split()), cue_characters=len(cue),
            full_instruction_words=len(files[arm][PROMPT].decode().split()),
            full_instruction_characters=len(files[arm][PROMPT].decode()),
            rendered_initial_tokens=None, added_initial_tokens=None)
    manifest = dict(experiment='EGRD-V022-MEER-ADOPTION', base_PR35='765530b39a7666a78ece099756fac925a932c617',
        source_active_MEER_B_ZIP_sha256=BASE_SHA, arms=records,
        factor='Only the adoption-cue block at the same instruction location; both scripts active',
        changed_member=PROMPT, unchanged_members=sorted(n for n in original() if n != PROMPT),
        original_prompt_recoverable_byte_exact=True,
        tokenizer_status='UNKNOWN_EXACT_LOCAL_TOKENIZER_TEMPLATE_UNAVAILABLE',
        tokenizer_difference_N_to_D=None, GPU_authorization='NOT_GRANTED', formal_submission=False)
    frozen_write(HERE / 'CANDIDATE_MANIFEST.json', (json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode())
    diff=''.join(difflib.unified_diff(files['N'][PROMPT].decode().splitlines(True),
        files['D'][PROMPT].decode().splitlines(True),fromfile='N/prompts/system.md',tofile='D/prompts/system.md',n=0))
    text=('# Prompt single-factor audit\n\nBoth arms derive from the frozen active MEER B ZIP. '
          'Only prompts/system.md differs; all four other members match each other and the original byte for byte. '
          'Removing the inserted cue recovers the original Prompt exactly. No instruction outside that block changes.\n\n'
          'The cue begins after the original opening paragraph and before Evidence-guided repair in both arms. '
          'Both mention an existing optional Issue-relevant probe; D adds the concrete route/arguments and lack of discovery prerequisite. '
          'This is adoption guidance, not enforced execution or an active/inert verifier contrast.\n\n'
          f"N cue: {records['N']['cue_words']} whitespace words / {records['N']['cue_characters']} characters. "
          f"D cue: {records['D']['cue_words']} words / {records['D']['cue_characters']} characters. "
          'These are not model tokens. Exact rendered initial token counts and their difference remain UNKNOWN; '
          'no surrogate tokenizer or semantic filler is used. Added identifier/syntax salience and unequal token length remain part of the intervention.\n\n'
          '```diff\n'+diff+'```\n')
    frozen_write(HERE / 'PROMPT_DIFF_AUDIT.md', text.encode())
    return manifest


if __name__ == '__main__':
    m=build()
    print(json.dumps({a:r['ZIP_sha256'] for a,r in m['arms'].items()}))
