# Candidate A paired pilot: final audit

**Gate: `NO_CANDIDATE_PROMOTION_PROTOCOL_DEVIATION`.** The sole authorized Notebook physically completed all eight frozen sessions. The audit is complete; the experiment is inconclusive as a confirmatory comparison. Preserve R2 as the established candidate. Do not promote A, construct R3, selectively rerun these tasks or claim a Public Score improvement.

## Actual results and endpoint separation

| Task | R2 unchanged SDK / exact tests | A unchanged SDK / exact tests | Separate semantic review |
|---|---|---|---|
| xarray-6599 | fail / fail; timeout, no patch | fail / fail; irrelevant annotation patch | NO_PATCH / INVALID_REPAIR |
| pylint-8898 | fail / fail; reproducer/config only | fail / fail; reproducer/config only | INVALID_REPAIR / INVALID_REPAIR |
| sphinx-11445 | pass / pass; timeout fallback | pass / pass; explicit submit | Both PARTIAL_REPAIR |
| sympy-24661 | pass / pass | pass / pass | Both bounded VALIDATED_REPAIR; observations after stop-rule violation |

The raw SDK and exact-test totals remain **2/4 for each arm**. Do not rewrite those receipts to match semantic findings. Under the approved combined endpoint, the descriptive all-eight tally is **1/4 each**, plus one partial repair each. Both validated observations occur after the strict stopping boundary; they are retained as exploratory observations, not protocol-conforming confirmation. The eligible prefix has three R2 and two A sessions, zero combined-endpoint validations and no balanced four-pair estimate.

These are selected public development tasks, not hidden competition Native Resolved or canonical SWE-bench harness scores. The semantic stage was conducted separately from the test scorer by the same Codex analyst, unblinded. It is not an external independent reviewer. All original patches, tests, SDK results and model traces remain available in the immutable raw artifact.

## Sphinx: why passing tests did not establish a complete repair

Both patches pass the complete frozen file, 10 tests. R2's `prepend_prolog` lookahead accepts only `=`, `-`, `~` through the existing SECTIONING_CHARS list. Legal heading underlines such as `^`, `*`, `+`, `#` still get separated from a role title. A instead changes the regex to `:\w+:(?!\x60)`: it fixes the short `:mod:` role, but still treats domain-qualified `:py:mod:` and `:std:ref:` role titles as docinfo.

`POST_RUN_CPU_SEMANTIC_DIAGNOSTICS.json` runs the exact original function AST and exact frozen patched code with the actual pinned docutils StringList. Across the explicitly exploratory 21 role/underline combinations, original preserves 0, R2 preserves 9, A preserves 7. All three preserve the ordinary author/date docinfo case. These counts are diagnostic case counts, not model repair rates or a newly substituted primary test suite. Neither patch earns full Issue-level semantic approval. No frozen test or expectation was changed.

Sympy's two production patches address the actual relational AST path, all six operators and recursive operands. Both pass 29/29 frozen tests. Additional CPU checks import the original Sympy source and compile each exact transformer in memory: six unevaluated comparisons, chained/nested expressions and the unchanged evaluate=True path behave as intended. These checks use Windows Python 3.12 and complement, rather than replace, the actual Linux 3.11 receipts. Arbitrary custom namespaces and unsupported operator mixtures are not exhaustively proven. ast.NameConstant remains a future maintenance concern.

## Stopping-rule implementation gap

Session 6, A/Sphinx, encountered `sphinx-build: command not found` at Agent +47.17s and `locale.Error: unsupported locale setting` at +59.26s. These are actual CLI/runtime affordance failures, even though trusted Python tests and non-root admission passed. The frozen rules required infrastructure/environment errors to stop the suffix. The implementation classified independent verifier failures but missed errors embedded in Agent tool responses. It continued sessions 7 and 8.

This is a **protocol deviation**, not evidence that the model caused every failure. Do not falsely mark physically executed sessions NOT_RUN. Retain all eight, flag session 6 as environment-affected and exclude sessions 6–8 from confirmatory interpretation. No retry was performed. Future infrastructure admission must cover the Issue's source CLI and locale, and stop classification must inspect relevant Agent tool errors. An expected nonzero bug reproduction, empty grep or lint finding must still be distinguished from infrastructure failure.

A also temporarily wrote `test_regex.py` and later removed it. This violates its prompt's no-test-file instruction; it is not mutation of the trusted evaluation tests. Source fingerprints before/after trusted verification stayed unchanged. This distinction must remain visible.

## Time, tools and usage

| Observed all-eight descriptive metric | R2 | A |
|---|---:|---:|
| Agent seconds, all successes and failures | 1831.78 | 1733.34 |
| Mean Agent seconds | 457.95 | 433.33 |
| Worker lifecycle seconds, including native verification | 1959.57 | 1862.55 |
| Charged tool calls | 82 | 100 |
| Explicit submits, including invalid patches | 2/4 | 4/4 |
| Semantically validated explicit submits | 1/4 | 1/4 |
| Missing-required-argument edit calls | 0 | 0 |
| Denied calls after tool-budget exhaustion | 2 | 2 |
| get_status calls | 0 | 1 |
| Observed total tokens | at least 887623 | 1082892 |
| Full usage available | No: 2 cancelled requests UNKNOWN | Yes |

A used 98.44 fewer Agent seconds, a descriptive **5.37%** reduction; this is not the previously desired conditional 23.45% improvement and does not establish increased effective repairs per official billed second. A spent more charged tools. R2's missing cancelled-request usage prevents a definitive token-cost ratio. Do not impute those tokens as zero.

Each session generated one additional genuine Gemma SDK compaction request, included in HTTP counts, usage and elapsed costs. Main Agent requests all have temperature .2, top_p .95, maximum completion8192, thinking4096 and the same tool schema. SDK compaction requests omit explicit temperature/top_p/completion cap while retaining thinking4096; this is the same inherited SDK behavior in both arms. Do not claim every HTTP request used the main Agent's explicit sampling fields, or count the summarizer as an outside-session probe. Their omission leaves server/default sampling for compaction unverified.

For the two tasks with meaningful production edits in both arms, first observed edit intervals are:

| Task | R2 seconds | A seconds |
|---|---:|---:|
| Sphinx | [355.72, 355.79] | [302.48, 302.55] |
| Sympy | [202.20, 202.35] | [235.14, 235.28] |

A edits Sphinx earlier but Sympy later; there is no consistent earlier-edit signal. Its first Sympy edit adds an unused operator mapping before adding the visitor, so first edit is not time to functional repair. Its xarray edit at [417.88,417.94] changes an unrelated annotation and is not progress on the Issue. Pylint has no production implementation fix in either arm. These are intervals between source observations, not exact edit instants or inferred model thinking time.

R2 receives remaining-call warnings through tool returns even without get_status. Both arms can still exhaust tools before useful edits; A's second xarray annotation edit and R2's attempted Pylint implementation edit were denied. The lack of get_status alone does not prove an absence of budget information. R2 performed actual git diff on Sympy; A did so on Sphinx and Sympy. Explicit submission alone was plainly insufficient.

## Allocation, identity, evidence and cost

REAL_GPU_OBSERVATION: four actual NVIDIA L4 devices, each 23034 MiB, nvidia-smi output plus torch device enumeration/CUDA access. All eight frozen model-file SHA256 values match. Candidate ZIPs and compiled prompts match their frozen identities; model, generation, tool schema and order match across arms. All 16 Agent/verifier isolation probes report non-root network-denied Python3.11.9. Per-session cleanup, model server cleanup and owned-root recovery complete.

Raw artifact: `gpu-output/r2a-real-gpu-01.zip`, **150194283 bytes**, SHA256 **c879ec39a4daf197cc54b7df66c527d9b625ab47fe1c2b71becb8cfc65ee7ef9**, all 7166 ZIP entries CRC checked. `GPU_SESSION_EVIDENCE_INDEX.json` hashes original session traces, HTTP logs, patches, JUnit and receipts. CPU scripted replay entries are excluded from the real-session population. Raw full output remains private locally and in the existing Kaggle output; curated patches/actions/results are archived in this PR.

The reused outer supervisor reports `unknown / official_result_missing` because it expects the old single-result filename. Preserve that raw status. The coordinator exited0 and independently produced PAIR_RESULTS plus eight SESSION_RESULT files; those establish physical completion. It is a reporting-schema limitation, not permission to convert the supervisor's unknown result to pass.

Notebook first-cell window: **4534.29s (75.57min)**, below18000; model-load stage280.35s. Four-device first-cell exposure is approximately5.038 L4 device-hours, excluding any earlier platform startup. Account quota usage rose from8877.686 to18006.232 seconds: **9128.546 quota-seconds =2.5357 quota-hours**. After terminal status, remaining89993.768s, reserved0. This is an account balance observation, not a per-session official competition billing receipt; do not equate quota-hours, device-hours and competition time. Official per-task billing and hidden task count remain UNKNOWN. No official 12-hour coverage prediction follows from four tasks.

## Decision and next concrete work

No candidate is shown to repair more Issues in this pilot. Keep frozen R2, do not promote A or build R3. The small sample, stop-rule deviation, incomplete Sphinx fixes, and censored R2 usage prevent a reliable scoring or efficiency claim. Historical Public0.15 is unchanged; the separately authorized R2 submission57843305 was still PENDING with score UNKNOWN at the read-only check2026-11-01 07:44:03 UTC.

The next useful work is a separate CPU-only infrastructure correction: validate source CLI entrypoints and locale before model requests, and test tool-response infrastructure stop classification end-to-end. Then a new prospective, untouched task cohort and separately frozen experiment would be needed for confirmation. Do not rerun or select better outcomes for this consumed one-shot pilot. No additional GPU dispatch or competition submission is part of this closeout.
