# Result: neither produces a defensible submitted repair

**EGRD_V032_NEITHER_REPAIRS** refers to the preregistered submitted, verified repair
endpoint: A=false, B=false. It does not mean that A's private unsubmitted edit was
proved incorrect. Its correctness and fresh post-edit probe result are unknown.

Actual inference completed in both scheduled Agent invocations. A ended at its
300-second deadline; B ended with an actual vLLM HTTP400 context-admission error.
Both retained modifications, no successful submit_patch. There was no third
Session, retry, formal submission or reference-patch access.

The treatment has no demonstrated repair benefit. B received the exact failure
receipt (+678 initial serving tokens), but did not edit production. A attempted a
behavioral change late. Both lost time on unusable test commands. A plausible
candidate, execution of a target assertion, and timely closure are separate
capabilities; this trial exposes gaps in all three transitions but cannot assign
causal shares to model, evidence supplement or environment.

B's rejection is **not** the prior custom15360 Guard and **not** a300s timeout.
It is native serving admission with context32768 and requested output16384.
The server reports input **at least16385**, not an exact token count. Initial
inputs3430/4108 both fitted. Last successful B prompt15964; next rejected length
is a lower bound. No safety1024 or research Guard was installed, and no output
length truncation was observed in completed responses. More context cannot be
inferred to fix the issue. The receipt overhead alone is not proven to cause the
stop: paths, generated diagnostics and read volumes diverged.

The trusted evaluator ran after both sessions on the exact original base because
neither submitted a patch. The target remained expected1/actual0, all three
controls and bounded regression passed. These are valid base outcomes, **not
tests of the fallback patches**. No additional CPU/GPU Notebook was dispatched to
test the fallback. This is an important assessment limit, not a negative result
on a patch that was never evaluated.

Smallest next engineering question: can the Agent run one legitimate in-sandbox
targeted check using a verified project entry point and dependency closure,
distinguish setup failures from target assertions, and retain time to validate
and submit an actual repair? Supply execution-environment facts without a fix or
trusted probe leakage in a separately frozen study. First evaluate the retained
fallback with an explicitly scoped CPU-only follow-up if desired; its validity
must not be guessed. Do not tune the receipt/Prompt, increase output/context,
invent another optional verifier or replace S0 from these results.

No statistical superiority, official Native Resolved, canonical SWE-bench or
Public Score conclusion follows. S0's best-observed formal0.13 is unchanged.
