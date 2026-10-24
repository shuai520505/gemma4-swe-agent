"""Deterministic artifacts: A original EGR, B skill verifier, C matched prompt-only skill."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
EGR=ROOT/'u_re/v04/experiments/evidence_guided_repair_01/submission_egr_v04.zip'
EXPECTED='07263740c5ee22bf6611d7fa31dafbc84d7fb50288d22355b9201cd6954a6840'
SKILL='''---
name: meer-evidence
description: Bounded source-bound assertion checks with explicit uncertainty; not an official scorer.
---

Use this skill for local repair evidence. Create a small Python reproducer under
/tmp with assertions directly tied to the normal Issue and public workspace.
Call run_skill_script with skill_name meer-evidence, file_path scripts/verify.py,
and args {check: /tmp/your_check.py, seconds: "10"}. The workspace is /workspace.
SUPPORTED concerns only this executed, unchanged-source check. It never proves
Issue coverage or Native Resolved. UNKNOWN or CONTRADICTED supplies no success
evidence. OBSERVED repeated checks supply no new evidence. After an edit, obtain
fresh evidence; inspect failures rather than repeating unchanged checks. Keep
verification small and leave time for diff review and official submit_patch.
If this interface cannot execute, report that limitation and use normal official
tools. The skill cannot intercept direct tool calls or force submission.
'''
PROMPT_ONLY='''"""Matched interface with advisory guidance, deliberately no evidence mechanism."""
import json
print(json.dumps(dict(schema="MEER_PROMPT_ONLY_CONTROL",verdict="UNKNOWN",
    observed=False,subprocess_invocations=0,
    guidance="Use official tools to run your Issue-relevant assertion reproducer. Check that it executed after the latest source edit; do not repeat unchanged diagnostics. Passing an assertion does not prove the whole repair. Review the diff and submit when justified.")))
'''


def sha(raw):return hashlib.sha256(raw).hexdigest()


def archive(files):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for name,raw in sorted(files.items()):
            item=zipfile.ZipInfo(name,(2026,10,24,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED
            item.external_attr=0o100644<<16;z.writestr(item,raw)
    return stream.getvalue()


def frozen_write(path,raw):
    if path.exists():
        assert path.read_bytes()==raw,"Frozen artifact differs; create a new version rather than overwrite"
    else:
        path.write_bytes(raw)


def build():
    raw=EGR.read_bytes();assert sha(raw)==EXPECTED
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        base={n:z.read(n) for n in z.namelist()}
    assert set(base)=={'agent.yaml','eval_config.yaml','prompts/system.md'}
    variants={'A':base}
    for arm,script in [('B',(HERE/'verify.py').read_bytes()),('C',PROMPT_ONLY.encode())]:
        files=dict(base)
        files['agent.yaml']+=b'\nskills:\n  - skills/meer-evidence\n'
        files['skills/meer-evidence/SKILL.md']=SKILL.encode()
        files['skills/meer-evidence/scripts/verify.py']=script
        variants[arm]=files
    records={}
    for arm,files in variants.items():
        target=HERE/'candidates'/arm;target.mkdir(parents=True,exist_ok=True)
        for name,content in files.items():
            dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);frozen_write(dest,content)
        packaged=raw if arm=='A' else archive(files)
        out=HERE/f'submission_{arm}.zip';frozen_write(out,packaged)
        with zipfile.ZipFile(io.BytesIO(packaged)) as z:assert z.testzip() is None
        records[arm]=dict(ZIP_sha256=sha(packaged),bytes=len(packaged),members={n:sha(b) for n,b in files.items()})
    assert variants['B']['agent.yaml']==variants['C']['agent.yaml']
    assert variants['B']['prompts/system.md']==base['prompts/system.md']==variants['C']['prompts/system.md']
    lock=dict(experiment='MEER-V01',base_EGR_sha256=EXPECTED,arms=records,
              main_mechanism_contrast='B vs C: only skill script implementation differs',
              EGR_contrast_limitation='A vs B adds official SkillToolset declarations/instructions as well as script; not a pure script-only contrast',
              GPU_authorized=False,formal_submission_authorized=False)
    manifest=HERE/'CANDIDATE_MANIFEST.json'
    if manifest.exists():
        assert json.loads(manifest.read_bytes())==lock,'Frozen manifest semantics changed'
    else:
        frozen_write(manifest,(json.dumps(lock,indent=2)+'\n').encode())
    print(json.dumps({k:v['ZIP_sha256'] for k,v in records.items()}))
    return lock


if __name__=='__main__':build()
