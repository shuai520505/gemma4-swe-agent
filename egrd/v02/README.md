# EGRD V0.2 context and decision audit

**EGRD_V02_AUDIT_COMPLETE_MORE_EVIDENCE_REQUIRED**. No production Agent or
controller was implemented. No Notebook save, inference, quota query, package
installation or formal submission occurred. S0 and all historical evidence stay
unchanged. See FINAL_DECISION for the 15 required answers.

New work reconstructs all 40 real PR33 requests,3 prevented generations and 40 tool
actions from original SHA/CRC-verified evidence. It independently checks four
old V03 native/config/usage records for the context-cap comparison. PR32's
26 session/784 action autopsy is a hash-verified historical source, not a newly
repeated full autopsy. Raw bodies/reasoning/Issue/patches/tests remain private.

Reproduction, from the repository root with retained private evidence:

```text
python -m egrd.v02.source_audit
python -m egrd.v02.context_audit
python -m unittest egrd.v02.test_context_audit -v
```

The analyzer refuses to replace a differing derived output. `--archive` and
`--output` support isolated replay. Exact component-token replay is NOT_RUN:
local tokenizer/template bodies are missing. All 40 aggregate serving counts do
match received prompt usage. Canonical JSON character counts are not tokens.

Reports: GUARD_PATH_AUDIT, CONTEXT_GROWTH_ANALYSIS, CONTEXT_COUNTERFACTUAL,
ACTION_TIMELINES, EVIDENCE_TO_PATCH_FAILURES, DECISION_OPPORTUNITIES,
BOTTLENECK_ASSESSMENT, OFFICIAL_INTERFACE_AUDIT, ARCHITECTURE_DECISION and
NEXT_EXPERIMENT_PROTOCOL. Machine-readable counts/provenance and offline tests
accompany them. Future study is conditional, not an executable authorized run.
