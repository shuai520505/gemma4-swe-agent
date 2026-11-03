# Pilot outcome: PILOT_FAILED

REAL_GPU_OBSERVATION. One SaveKernel request, accepted Notebook `wudangdexiaodoashi/egrd-v01-12b-pilot01` version1, actual4×NVIDIA L4, exact official12Bv2 bytes. Notebook terminal status COMPLETE means process completion, not a passed engineering gate. No retry, task substitution or competition Submission occurred.

| Session | Task | Arm | SDK Agent seconds | Charged/ADK calls | Raw SDK resolved | Explicit submit | Final patch |
|---|---|---|---:|---:|---|---|---|
| 1 | Pylint8898 | A12B |299.908|22|false|false|285B, diagnostic/config only|
| 2 | Pylint8898 | B12B |299.887|28|false|false|1486B, diagnostic/config only|
| 3 | Sphinx11445 | B12B |295.308|24|false|false|100308B, reproduction/build output only|

All three timed out and produced fallback patches. Separate post-run unblinded semantic review finds0 valid final repairs. Sphinx first changed the causally relevant prepend_prolog production function at157.947880422s and reverted that change at226.209592252s; the final patch contains no surviving production repair. The transient proposal was not independently validated. Do not infer absence of an attempted production edit from its absence in the final diff.

The first HTTP requests visibly advertise six original workspace tools plus four official Skill accessors. Nevertheless all three sessions have **zero Skill loads/script calls, zero EGRD states, zero get_status and zero submit_patch calls**. Thus B's executable EGRD mechanisms were never activated. This pilot cannot estimate the effect of the implemented ledger/action policy. The one complete Pylint A/B pair is0/1 versus0/1; the additional Sphinx B is unpaired. A0/1 versus B0/2 is not an efficacy comparison or a hidden benchmark score.

## Why the sequence stopped

Original Session3 HTTP audit failed `unexplained_cancellation`; the Coordinator preserved it and stopped immediately. Remaining12B sessions4–6 and all31B sessions7–12 are NOT_RUN. No missing outcome is zero-imputed.

Posthoc diagnostic, kept separately from original admission: the cancel is at Agent Loop phase+300.000776s and the SDK reports its5minute timeout. The source CLI preflight consumed4.699780s between that phase and the later Agent counter start, so ctx elapsed is295.308s. The Worker requires ctx elapsed>=299 to recognize deadline cancellation and computes cutoff from that later clock. This mismatch explains the original audit failure. Re-evaluating the **same** wire evidence with the independently observed phase deadline passes the old auditor while keeping cancelled usage UNKNOWN. This does not change the original failed audit, allow retrospective continuation or prove a model/backend failure. Official Runner creates asyncio.timeout before the preflight/start counter; the source and exact timestamps are recorded.

A separate integration defect remains: the reused aggregate outer supervisor expects single-session output/CLEANUP names, so it records `official_result_missing`/`cleanup_unconfirmed` despite coordinator process exit0. Specific Worker/native CLEANUP receipts, final known model-process list and owned-root recovery pass. The contradictory aggregate receipt is retained and the overall trust/engineering gate remains failed; do not report blanket cleanup PASS until this adapter is repaired and CPU-tested.

The Pylint command-line entrypoint was absent, while `python3 -m pylint` worked; this wasted time and is an environment/interface limitation. One read of nonexistent `pylint/utils.py` returns the helper's overbroad CHROOT_SETUP_FAILED FileNotFoundError label. Source inspection shows read mode performs that file access after confinement, so this is not evidence of isolation escape/setup failure. File/package path discovery and source CLI availability need explicit separate categories.

## Cost and measurements

12B model load209.261s. Agent counters total895.103s; Worker and native costs are separately preserved. Notebook measured wall1445.435s (24.09min). Account quota delta2933.676s=0.81491quota-hours; this is an observed account change, not isolated monetary attribution. Remaining quota at recovery87060.092s. A device-hour is not a quota-hour.

83 HTTP requests =77 main requests +6 inherited SDK conversation summaries.80 received responses report757877 prompt tokens +35221 completion tokens =793098 observed total tokens. Three cancelled requests have unknown usage, so this total is incomplete. SDK LLM counter74 and charged tools74 are not the full HTTP request count. No request is added solely for deterministic next-action selection. HTTP latency includes server wait/prefill/decode, not isolated model thinking. No31B load exists;12B-vs31B latency is UNKNOWN.

## Decision

PILOT_FAILED; EGRD_PARTIALLY_IMPLEMENTED. Do not promote this candidate, claim a score improvement, claim frozen-S0 superiority, launch a larger benchmark, or attribute a mechanism contribution. First establish a compliant executable entrypoint that is actually reached in real sessions, and repair/CPU-test the clock and aggregate-supervisor contracts. The post-freeze current CPU fixes are separately validated and were not the GPU-tested script. Future real-model work needs its own prospective version/task/resource plan, not a selective replay of the failed suffix.
