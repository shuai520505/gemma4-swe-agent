# Next action and budget

Deterministic recommendations use actual source identity, recent action signatures, current evidence, declared causal hypotheses, patch state and helper remaining time. No model call is made by the selector.

- Repeating the same recorded action/signature on unchanged source without a supplied justification recommends forming a discriminating hypothesis. Recording an action does not intercept an actual official search, and an Agent can bypass the recorder.
- A populated hypothesis supported by current evidence recommends EDIT. Structural adequacy is not semantic sufficiency; Gemma decides whether the evidence truly supports the causal edit.
- An existing unaccepted patch recommends a targeted check. Accepted local evidence recommends submission. Full-suite execution is not automatically launched.
- The reserve window recommends SUBMIT with an explicit supported_patch flag. It never manufactures a good patch when time is low or blocks the official submit tool.

The official six-tool get_status exposes local session budget, not a reliable all-task global timer or exact context occupancy. Skill calls cannot read that host object. The persisted monotonic clock measures time from helper initialization only and can start late; it is labeled an upper-bound helper scope, not official remaining time. Configured official SDK session budget5minutes is the actual hard research cap; reserve25 seconds is configurable local advice. Checks exceeding the helper reserve are refused within the script.

Tool count, real model tokens and context occupancy remain null when unavailable. Do not fill them with zero. Main request/response usage, model latency and charged tools are collected by external research observers, separately from deployed state. Observed action durations can be accumulated by category; gaps between logs are not called model thinking time.

Fresh official HARNESS_README distinguishes300s command timeout,300s verifier timeout and configurable session time (default60min). We explicitly choose300s Agent,60charged calls,80turns,120s commands for this research. Setup is outside that Agent timer but inside whole-run costs. The model's architectural256K window does not authorize raising the competition serving limit32768.


Post-freeze consistency corrections in the current CPU candidate: changed check bytes invalidate advisory acceptance; stale hypothesis support cannot recommend EDIT; a passing current target advances to regression, then current diff review; fresh contradictory checks or outside-intent changes recommend REVISE_PATCH. The real pilot retains its original frozen script and therefore does not validate these later fixes. See POST_FREEZE_CORRECTIONS and pilot-frozen for exact provenance.


Configuration boundary: revision/reserve values are configurable through the core Python state API, as exercised by unit tests. The deployed V0.1 CLI freezes defaults of2 revisions and25s reserve; dynamic YAML/CLI override binding is not implemented and would require a separately versioned package/retest.
