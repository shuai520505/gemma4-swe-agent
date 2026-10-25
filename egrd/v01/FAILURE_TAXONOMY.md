# Reproducible taxonomy

Labels are nonexclusive and use observed events, not guessed beliefs. Denominator for repair-failure frequencies is **12 interpretable false sessions**; one environment-confounded run is excluded. Successful sessions can contain inefficient or risky patterns. Counts describe availability-selected development cases, not population prevalence.

| Label | Required evidence | Insufficient evidence |
|---|---|---|
| F1 localization | Missing relevant implementation inspection within observed trace, after task-specific review | No final repair; keyword search alone |
| F2 root cause | A visible causal claim plus directly contradictory available evidence | Reading source; native false; an unspoken model belief |
| F3 generation | Actual defective behavioral edit with a demonstrable local defect, or no suitable edit despite specifically supported repair direction | Any nonempty patch; native false by itself |
| F4 revision | Relevant adverse feedback followed by unchanged failed checks/no correction, or demonstrated loss of a previously supported patch | Multiple edits; final failure alone |
| F5 verification | Wrong/no-op check, known invalid path/test, stale/no post-edit execution, or overly broad unrelated collection | Every diagnostic command; every optional dependency error |
| F6 selection | Exact repeated investigation with unchanged relevant state, or reviewed spending without a discriminating question | All searches; necessary repeated confirmation |
| F7 budget/closure | Recorded guard/deadline/tool stop while unresolved work remains, or redundant post-submit continuation | A stop proves insufficient budget; no submit necessarily means no native patch |
| F8 environment | Independent fixture/dependency/runtime/observer failure with source evidence | Any collection error; the word ERROR anywhere in stdout |
| F9 indeterminate | No justified more specific causal explanation | Permission to convert unknown to algorithm failure |

`review.py` stores reviewed event indices, observations and label strength; `audit.py` verifies them against raw event identities. F6 in V03 is explicitly interpretive. F7 frequency measures a terminal pattern, not a counterfactual effect of extra time. F3 includes one repaired intermediate AttributeError and one uncorrected syntax regression; it does not mean both final failures share that cause.

Information ladder: source inspected → visible hypothesis (if actually expressed) → discriminating failing execution → production behavior changed → source-bound local pass → native resolved. Each step needs separate evidence. AST assertion presence is neither assertion execution nor Issue relevance. Exit0 with printed error or an empty test is not a repair verdict.

Corrected parsing rule: extract only the final structured JUnit or terminal pytest summary. Never scan arbitrary traceback/test parameter text for error counts. S1 Rich test data contained “4 errors” while the final summary had zero errors. S1 FastAPI collection failure instead points to Agent-modified syntax and is a genuine repair regression. Both historical records remain untouched; the new view preserves raw values and records interpretation separately.
