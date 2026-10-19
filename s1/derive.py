"""Derive factor candidates; never write to frozen candidate directories."""
import difflib
import hashlib
import json
from pathlib import Path
from experiments.prepare import archive_bytes, write_new
from .config import Config

ROOT=Path(__file__).resolve().parents[1]
MEMBERS=('agent.yaml','eval_config.yaml','prompts/system.md')
LOCATE='''
Bounded localization: extract the Issue's identifiers and expected behavior. Use
bounded file/symbol search, then read the local implementation. Inspect one layer
of callers or a parallel implementation only when it resolves a concrete risk.
Each further read should answer an unresolved question; avoid repeating unchanged
reads or empty searches. Once evidence supports a small repair plan, edit and
verify early. Do not force dynamic tracing or guess edits to meet a timing target.
'''
VERIFY='''
Choose verification by the changed contract. For modules, CLI or automation,
confirm actual import/export names, caller or entry-point wiring, arguments,
configuration and dependencies from the repository; use an import or harmless
startup/help check where appropriate. For behavior changes, run a focused
reproducer or existing test plus a relevant boundary or old-behavior check.
Use mocks or dry runs for external effects. Syntax checks alone do not establish
behavior. Keep this work within the existing budget; finish with a reviewed
Patch and state which requirements remain unverified. Do not run broad tests
without a specific reason.
'''


def sha(raw): return hashlib.sha256(raw).hexdigest()


def derive():
    source=ROOT/'candidates/s0/submission'
    baseline={n:(source/n).read_bytes() for n in MEMBERS}
    assert sha((ROOT/'candidates/s0/submission.zip').read_bytes())=='3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9'
    variants={
        'control':(Config(),''),
        'e1_output8192':(Config(output_tokens=8192),''),
        # E2/E3/E4 are independent preparations at the original output cap.
        # No GPU registration for them until their fixed comparator is chosen.
        'e2_thinking0':(Config(thinking_budget=0),''),
        'e3_locate':(Config(),LOCATE),
        'e4_verify':(Config(),VERIFY),
    }
    manifest={}
    for name,(cfg,addition) in variants.items():
        files=dict(baseline)
        tc=f'    thinking_budget: {cfg.thinking_budget}\n'
        generation=(f'generate_content_config:\n  max_output_tokens: {cfg.output_tokens}\n'
                    f'  seed: {cfg.seed}\n  thinking_config:\n'+tc)
        files['agent.yaml']=baseline['agent.yaml']+generation.encode()
        files['prompts/system.md']=baseline['prompts/system.md']+addition.encode()
        path=ROOT/'s1/candidates'/name
        for n,b in files.items(): write_new(path/n,b)
        package=archive_bytes(files)
        write_new(ROOT/'s1/packages'/name/'submission.zip',package)
        diff=''.join(difflib.unified_diff(baseline['prompts/system.md'].decode().splitlines(True),
            files['prompts/system.md'].decode().splitlines(True),fromfile='S0/system.md',tofile=name+'/system.md'))
        write_new(ROOT/'s1/diffs'/(name+'.prompt.diff'),diff.encode())
        manifest[name]=dict(config=cfg.snapshot(),zip_sha256=sha(package),bytes=len(package),
            members={n:sha(b) for n,b in files.items()},prompt_changed=bool(addition),
            readiness='CPU gate required; E2-E4 GPU not registered')
    write_new(ROOT/'s1/candidates.json',(json.dumps(manifest,indent=2)+'\n').encode())
    return manifest


if __name__=='__main__': print(json.dumps(derive(),indent=2))
