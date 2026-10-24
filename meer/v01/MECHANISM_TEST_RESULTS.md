# Mechanism enforcement and adversarial evidence

Source: final actual CPU140511729/v1,12Linux tests plus4native Runner sessions. The important distinction is local Skill enforcement versus global Agent behavior.

| Scenario | Observed mechanism behavior | Enforcement | EGR difference / limit |
|---|---|---|---|
| Repeated same source/check | B calls3times:CONTRADICTED,SUPPORTED,OBSERVED; child counts1,1,0 | Duplicate helper subprocess actually suppressed | EGR has no such verifier; C only returns UNKNOWN |
| Repeated search outside helper | B_BYPASS executes identical grep twice, unchanged results | NONE | Same bypass is possible in EGR; no global search controller |
| Success declaration without evidence | Scripted B_BYPASS declares success; Runner nudges then continues | Helper never accepts text as evidence; global declaration NOT intercepted | Do not claim hard success/termination control |
| Green before edit, failure after edit | Actual Python source edit changes hash; next helper runs and CONTRADICTS | Old receipt not accepted for current tree | Cannot stop Agent quoting an old result without invoking helper |
| Test has no evaluated assertion | print-only,assertTrue,ifFalse assert and unused test function all UNKNOWN | No SUPPORTED from exit0 alone | Structurally nonconstant expression can still be a semantic tautology |
| Initial repair/check fails | Real local assertion failure is CONTRADICTED; corrected source then SUPPORTED | Actual child execution/hash observation, not model JSON | Does not invent a correct fix |
| Diagnostic has no new information | Identical check/tree skips actual rerun, new_evidence=false | Only inside opt-in check | Arbitrary diagnostics remain allowed |
| Direct submit without relevant verification | B_BYPASS emits successful official submit, no helper or targeted test | NONE; actual bypass positively demonstrated | Native owned fixture later passes because scripted edit was correct; not pre-submit proof |
| Verification exceeds local budget | Hanging child times out, becomes UNKNOWN, process group killed | Max15s helper bound; native executor also limits global remaining time | No separate controller reserves future edit/submit time |
| Missing dependency / exception | Real ImportError check contradicts local success claim; classification retained as exception_type | Not promoted to support | Not proof the target Issue is unsolved or Agent algorithm failed |
| Source changes during check | Before/after hash mismatch -> UNKNOWN | Fresh evidence invalidated | Does not make untrusted workspace code tamper-proof |

Supported statement: this particular selected assertion script executed successfully on this observed unchanged tree. Semantic correctness, Issue coverage and Native Resolved remain UNKNOWN inside the helper. Tests of state flags alone are not used to establish global enforcement; B_BYPASS provides the explicit real counterexample.
