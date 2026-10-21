# U-RE-V01-GEMMA-SMOKE-01 — engineering only

One candidate NoEGV, one task fastapi_14492, one planned Agent run, at most one future GPU save. Proposed slug wudangdexiaodoashi/gemma4-u-re-gemma-smoke01. This protocol grants no GPU authorization.

Frozen limits:300s Agent,60 counted tools,120s command,output16384,thinking4096,seed17; omitted sampling/include_thoughts remain omitted. A successful submit_patch is an observation, not forced termination. Capture first success, subsequent tools/repeated submissions, final boundary error, latest pre-end checkpoint and Native TaskResult independently.

PREFLIGHT → LOAD_MODEL → READY_CHECK → INIT_AGENT → LOAD_TASK → RUN_AGENT → COLLECT_PATCH → NATIVE_VERIFY → EXPORT → CLEANUP are reporting phases. Native verification is executed by the same official evaluator inside the supervised worker. Aggregate observations do not invent timing for nested phases. Native stage timestamps remain authoritative. Candidate submit_patch normally occurs inside RUN_AGENT before native Phase2; no altered submit semantics.

Engineering success requires a real model response, actual tool interaction, returned patch (possibly empty and separately flagged), parseable native TaskResult/JUnit, explained HTTP terminals and verified worker/server cleanup. resolved=false can be a valid engineering observation. COMPLETE alone proves none of these. No score, EGV effect, or repair-rate claim follows.

STOP on hash drift, wrong hardware/model/task, missing/inconsistent JUnit, incomplete HTTP lifecycle, unknown resource identity, insufficient full window, unproven evaluation isolation or failed cleanup. No task substitution or retry. Raw evidence stays outside the public checkout. This exposed historical task is excluded from independent mechanism confirmation.
