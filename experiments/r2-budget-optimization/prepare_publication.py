"""Whitelist new audit files; hash Git blobs without touching a checkout."""
import hashlib
import json
from pathlib import Path
import re

OUT=Path(__file__).resolve().parent
PUB=OUT/'publication'
NAMES='''R2_TIME_DECOMPOSITION.json
R2_TOOL_ACTION_AUDIT.json
R2_TRACE_EFFICIENCY_REPORT.md
R2_INSTRUCTION_COMPLIANCE.md
R2_BUDGET_MODEL.json
R2_BUDGET_ANALYSIS.md
R2_OPTIMIZATION_HYPOTHESES.md
R2_NEXT_EXPERIMENT_PROTOCOL.md
R2_BUDGET_OPTIMIZATION_FINAL_DECISION.md
FROZEN_INPUT_IDENTITIES.json
WORKSPACE_CHECK.json
RAW_EVIDENCE_INDEX.json
OFFICIAL_BUDGET_EVIDENCE.json
BOTTLENECK_EVIDENCE.json
ACTION_FIRST_CORROBORATION.json
HISTORY_ADDITIONAL_IDENTITIES.json
CPU_TOOL_CONTRACT_RESULT.json
AUDIT_VERIFICATION.json
analyze_raw_traces.py
build_evidence_models.py
write_reports.py
cpu_contract_check.py
verify_audit.py
freeze_candidate_a_design.py
prepare_publication.py
candidate-a-design/CANDIDATE_A_POLICY_SPEC.json
candidate-a-design/CANDIDATE_A_PROMPT_REPLACEMENT.diff
candidate-a-design/CPU_DESIGN_IDENTITY_CHECK.json
candidate-a-design/EXECUTION_PREREQUISITES.md'''.splitlines()
entries=[];expected={}
for n in NAMES:
    p=OUT/n;raw=p.read_bytes();content=raw.decode('utf8')
    assert not p.is_symlink() and '..' not in Path(n).parts
    assert not re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|KGAT_[A-Za-z0-9]{25,}',content),n
    path='experiments/r2-budget-optimization/'+n
    entries.append(dict(path=path,mode='100644',type='blob',content=content))
    expected[path]=dict(git_blob_sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
PUB.mkdir(exist_ok=True)
payload=json.dumps(entries,ensure_ascii=True,separators=(',',':'))
(PUB/'PUBLIC_ELEMENTS.json').write_text(payload,encoding='utf8')
(PUB/'PUBLIC_EXPECTED.json').write_text(json.dumps(expected,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(files=len(entries),payload_characters=len(payload),raw_bytes=sum(x['bytes'] for x in expected.values()),secret_pattern_scan='PASS_WHITELIST_ONLY')))
