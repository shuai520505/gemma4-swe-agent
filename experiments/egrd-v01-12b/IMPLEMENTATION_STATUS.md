# EGRD V0.1 implementation status

Evidence labels: CPU_VERIFIED, STATIC_ANALYSIS, OFFICIAL_RULE, REAL_GPU_OBSERVATION, UNKNOWN and NOT_RUN are distinct. This file describes shipped capabilities; PILOT_REPORT.md supplies actual evaluation results when recovered.

| Module | Shipped mechanism | Boundary |
|---|---|---|
| A Issue Contract | Original text/hash, Issue ID, expected/actual, I/O, boundaries, acceptance and questions; mandatory provenance and quoted OBSERVED text | Exact Issue authenticity is unverified when relayed by Gemma; semantic completeness is not proved |
| B Evidence State | Actual bounded source reads, source/check hashes, stale marking, atomic scratch state, executed MEER checks and duplicate reuse | Not a protected adversarial attestation channel; dedicated runtime/call graph producers deferred |
| C Localization | Evidence-linked causal hypotheses, contradictions, predictions and next experiment | Gemma supplies semantic reasoning; confidence is self-reported |
| D Issue anchoring | Required Issue/evidence links and intent files/regions/behavior/preservation/counterexample; actual outside-intent flags | Structural traceability only; cannot prove semantic relevance or globally block unrelated edits |
| E Next action | Executable repeated-action/source-state/reserve rules, no LLM request | Advisory through the optional official Skill; not a global tool interceptor |
| F Patch lifecycle | Actual patch recording, configurable revision bound, scoped rollback, current target/regression/diff gate | Refuses its own invalid acceptance only; official submit remains callable directly |
| G Budget/context | Helper monotonic/reserve, check durations, observed category totals; SDK hard 300s Agent cap | Helper starts late; official host tools/tokens/context cannot be read from Skill and stay null |

The official Compiler and actual sandbox Skill execution passed. Six original workspace tools are retained and the official SkillToolset adds four accessors. Exactly one LlmAgent is compiled, with no competitor host callback or second LLM. Unregistered callback names are inactive in the inspected official runtime.

CPU receipt: cpu-output/egrd-v01-12b-cpu01.zip, attempt03. The dispatch proof contains sixteen module tests, four official Compiler packages, real non-root Skill lifecycle, then comment-only Worker/native-evaluation plumbing all pass. The comment patch correctly yields SDK resolved=false and is not repair evidence. Attempt02's ambiguous scripted edit failed and is preserved; the correction uses a unique original four-line anchor without changing any trusted expectation.

Engineering pilot: one prospective GPU Notebook, three previously exposed public dev tasks, 12B A/B first, optional 31B C/D afterward. Configuration/source/package identities are frozen in gpu-notebook/BUILD.json. No performance claim follows from CPU simulation. A/C are S0-derived matched-interface controls rather than exact frozen S0. Exact-S0 and untouched held-out comparisons remain required.

Not implemented: compulsory global action/submit interception; deterministic semantic root-cause/Issue correctness; hidden evaluator access; reliable all-task global clock/context telemetry in the deployed Skill; best-patch semantic ranking; a second Agent. No original S0/R2/EGR/Full or historical result is edited.

Reproduction: run `python -m unittest discover -s experiments/egrd-v01-12b -p "test_*.py"` with Python3.12 and Git; Compiler requires the pinned official SDK. `build.py` consumes the hash-pinned copied original S0 prompt in inputs/s0, CPU/GPU builders require hash-pinned offline assets described by BUILD/CPU_BUILD and source pins. Dispatch is a separate authorized operation with a durable one-shot claim; never invoke it as a unit test or retry.


Post-freeze correction boundary: pilot-frozen contains the dispatch-time core/packages/manifest/CPU proof identity. The current implementation fixes four newly reproduced advisory-state/policy edge cases, with separate RED/GREEN tests and CPU revalidation. The GPU experiment cannot be used as evidence for the corrected script. No frozen historical asset was modified.


Final evidence: current CPU attempt06 passes27 module/package tests, all four Compiler packages, actual Skill lifecycle and Worker/native plumbing. Existing infrastructure checks6 pass. Real pilot terminates after3/12 attempted12B sessions;0 raw SDK resolved,0 valid final repairs,0 explicit submits,0 EGRD Skill invocations. Nine sessions are NOT_RUN.12B serving/ordinary tools work,31B comparison is UNKNOWN. Final statuses EGRD_PARTIALLY_IMPLEMENTED and PILOT_FAILED; not READY_FOR_CONTROLLED_EVALUATION. See FINAL_REPORT for the wrong-clock audit and aggregate-supervisor integration blockers.
