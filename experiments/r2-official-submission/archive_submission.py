"""Freeze exact package identity and current receipt; no network or inference."""
import base64,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;O=D/'attempt-01';P=O/'publication'
read=lambda p:json.loads(p.read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
r=read(O/'SUBMISSION_RECEIPT.json');s=read(O/'LATEST_STATUS.json');pre=read(O/'PREFLIGHT.json')
expected='af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5'
assert r['submission_id']==s['submission']['ref']==57843305 and r['status']=='ACCEPTED'
assert r['explicit_mutation_calls']==1 and not pre['blockers']
assert sha((O/'submission.zip').read_bytes())==sha((ROOT/'experiments/r2-final-audit/submission_r2_candidate.zip').read_bytes())==expected
old=read(ROOT/'experiments/r2-budget-optimization/FROZEN_INPUT_IDENTITIES.json')|read(ROOT/'experiments/r2-budget-optimization/HISTORY_ADDITIONAL_IDENTITIES.json')
for p,h in old.items():assert sha(Path(p).read_bytes())==h,p
manifest=dict(competition='gemma-4-developer-agent',submission_id=57843305,zip_sha256=expected,zip_bytes=3646,candidate='Exact frozen R2',formal_submit_calls=1,accepted=True,latest_status=s['submission']['status'],public_score=s['submission']['public_score'],score_observed_at_utc=s['checked_at_utc'],historical_best_public_score='0.15',candidate_A_included=False,R1_combination=False,R3_created=False,original_assets_verified_unchanged=len(old),local_GPU_notebooks_started=0,local_model_inference_calls=0,budget_audit_gate_not_overwritten='R2_BLOCKED_BY_BUDGET',human_authorization=pre['current_user_authorization'],compiler_evidence='../r2-final-audit/CPU_COMPILER_RESULT.json',compiler_receipt_sha256=sha((ROOT/'experiments/r2-final-audit/CPU_COMPILER_RESULT.json').read_bytes()))
(O/'SUBMISSION_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
report=f'''# Frozen R2 — first authorized formal submission

Kaggle accepted one direct ZIP submission: **57843305**. Current observed status: **{s['submission']['status']}** at {s['checked_at_utc']}. Public Score: **{s['submission']['public_score'] if s['submission']['public_score'] is not None else 'UNKNOWN / not returned'}**. Acceptance is not scoring completion or proof of repair success.

The user authorized submission with: “我觉得我们可以先把目前最好的先打包提交一下”. This supersedes the earlier audit-only prohibition for this single formal submission. Historical audits remain unchanged; the previous R2_BLOCKED_BY_BUDGET finding is not rewritten as READY. Hidden workload coverage, official timing and generalization remain unknown and are now subject to actual official scoring.

The uploaded submission.zip is a byte-identical copy of the frozen R2 candidate, SHA256 `{expected}`, 3646 bytes. Root agent.yaml, includes and four member hashes match the previous genuine official CPU Compiler PASS. No repacking, prompt/config/budget/model changes, R1 merge, Candidate A or R3 is included. Baseline and all 74 protected historical assets rehash unchanged.

Fresh authenticated Kaggle API preflight confirmed the team had entered, direct upload was enabled, deadline had not passed, no same-R2 marker existed in the returned submission history and one submission remained. After acceptance the API reported today's count 1 and remaining allowance 0. These are team submission counts, not GPU quotas. No unrelated job or submission was modified.

Only one explicit competition_submit call was made. A persistent exclusive attempt marker prevents local re-dispatch even if a response becomes uncertain. Subsequent get_submission/submission-limit calls are status reads only. No SaveKernel, new Notebook, local Gemma inference or local GPU allocation occurred. The competition's own scoring lifecycle is separate and not claimed to be GPU-free.

The previous best observed Public Score stays 0.15 until this submission returns an actual score. A missing score is null/UNKNOWN. Pending status cannot be used as Native Resolved, a hidden-task success count, a regression or a score improvement. Later scoring updates must preserve this original acceptance receipt and the original R12/audit evidence.

[Official submission page](https://www.kaggle.com/competitions/gemma-4-developer-agent/submissions) · [Official competition](https://www.kaggle.com/competitions/gemma-4-developer-agent)
'''
(O/'SUBMISSION_REPORT.md').write_text(report,encoding='utf8')
files=[D/'r2_official_submit.py',D/'archive_submission.py']+[O/n for n in ('PREFLIGHT.json','SUBMISSION_ATTEMPT_LOCK.json','SUBMISSION_RECEIPT.json','LATEST_STATUS.json','STATUS_HISTORY.jsonl','SUBMISSION_MANIFEST.json','SUBMISSION_REPORT.md')]
entries=[];hashes={}
for f in files:
    raw=f.read_bytes();text=raw.decode('utf8')
    assert not re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|KGAT_[A-Za-z0-9]{25,}',text),f
    path='experiments/r2-official-submission/'+f.relative_to(D).as_posix()
    entries.append(dict(path=path,mode='100644',type='blob',content=text))
    hashes[path]=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
raw=(O/'submission.zip').read_bytes();binary=dict(path='experiments/r2-official-submission/attempt-01/submission.zip',base64=base64.b64encode(raw).decode(),sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
P.mkdir(exist_ok=True)
(P/'ELEMENTS.json').write_text(json.dumps(entries,ensure_ascii=True),encoding='utf8')
(P/'ZIP_BLOB.json').write_text(json.dumps(binary),encoding='utf8')
(P/'EXPECTED.json').write_text(json.dumps(hashes|{binary['path']:binary['sha']},indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(files=len(entries)+1,payload_characters=len((P/'ELEMENTS.json').read_text()),submission_id=57843305,status=s['submission']['status'],public_score=s['submission']['public_score'],original_assets_unchanged=len(old))))
