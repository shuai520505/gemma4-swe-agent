# R12 GPU Run 02 — final report

Nine of nine real Gemma sessions completed in frozen order on four actual NVIDIA L4 GPUs. Seven nonempty patches were retained; six satisfy the frozen repair endpoint after separate post-run semantic review. No selective reruns, R3 construction, or formal competition submission occurred.

| Candidate | Validated repairs | Valid explicit submits | Missing-parameter edits | Charged / attempted tools | Observed tokens | Agent seconds |
|---|---:|---:|---:|---:|---:|---:|
| BASELINE | 1/3 | 1/3 | 5 | 61 / 71 | 721,041 (incomplete) | 1094.59 |
| R1 | 2/3 | 2/3 | 0 | 64 / 68 | 720,207 (incomplete) | 1119.33 |
| R2 | 3/3 | 3/3 | 0 | 67 / 70 | 757,609 | 1161.87 |

| Session | Task | Candidate | Final endpoint | Agent outcome | First production edit interval (s) |
|---:|---|---|---|---|---|
| 1 | django__django-11964 | BASELINE | INVALID_REPAIR | TIMEOUT_WITH_FALLBACK | Not observed (not zero) |
| 2 | django__django-11964 | R1 | VALIDATED_REPAIR | EXPLICIT_SUBMIT | 214.15–214.37 |
| 3 | django__django-11964 | R2 | VALIDATED_REPAIR | EXPLICIT_SUBMIT | 256.18–256.40 |
| 4 | pydata__xarray-6721 | R1 | NO_PATCH | NO_EXPLICIT_SUBMIT | Not observed (not zero) |
| 5 | pydata__xarray-6721 | R2 | VALIDATED_REPAIR | EXPLICIT_SUBMIT | 326.30–326.36 |
| 6 | pydata__xarray-6721 | BASELINE | NO_PATCH | EXPLICIT_SUBMIT | Not observed (not zero) |
| 7 | pytest-dev__pytest-5631 | R2 | VALIDATED_REPAIR | EXPLICIT_SUBMIT | 133.67–133.75 |
| 8 | pytest-dev__pytest-5631 | BASELINE | VALIDATED_REPAIR | EXPLICIT_SUBMIT | 92.37–92.46 |
| 9 | pytest-dev__pytest-5631 | R1 | VALIDATED_REPAIR | EXPLICIT_SUBMIT | 109.14–109.22 |

## Required conclusions

1. Completion: 9 workers, 9 saved session results, 9 real Gemma sessions with HTTP requests, 9 independent evaluations, no NOT_RUN suffix. PAIR_RESULTS.complete=true; no coordinator STOP.
2. Repairs: BASELINE 1/3 (pytest), R1 2/3 (Django, pytest), R2 3/3 (all three). These are owned Issue-grounded development endpoints, not canonical SWE-bench or official competition scores.
3. R1 parameter hygiene: BASELINE made five edit_file calls missing old_string (four Django, one xarray); R1 and R2 made zero. Three sessions per arm; this is an observed pilot difference, not a causal estimate.
4. R2 first production edit: Django 256.18–256.40s and xarray 326.30–326.36s, while BASELINE never changed production code on either. On pytest R2 was slower (133.67–133.75s versus BASELINE 92.37–92.46s). R2 improves edit coverage, without evidence of uniformly faster edits.
5. R2 valid explicit submissions: 3/3 versus R1 2/3 and BASELINE 1/3. BASELINE explicitly submitted on two sessions, but its xarray submission was empty. Django BASELINE timed out with a diagnostic-only fallback; R1 xarray timed out without any patch.
6. R2 has the highest observed repair rate. With only three tasks and one run per pair, this does not establish general superiority or predict public leaderboard 0.5.
7. Failures: BASELINE Django repeated four malformed edit calls, spent its deadline without a production fix, and retained only temp_app reproduction files. BASELINE xarray diagnosed the relevant code but omitted old_string, exhausted 28 charged calls, then submitted an empty patch; BudgetExceeded responses are recorded. R1 xarray reached its deadline without editing. These are tool-interface/model-action and time-allocation failures, not observed GPU/backend/environment failures. The data do not isolate the causal contribution of each.
8. Usage is recorded per session and candidate in R12_GPU_RESULTS.json. Token totals for timed-out BASELINE Django and R1 xarray are incomplete observations, not exact totals or zero missing usage. Charged calls and attempted calls are reported separately.
9. All nine required positive controls passed; no observed control regression and no task where an alternative loses a BASELINE success. Broader regression suites were NOT_RUN; absence of broader regressions is not established.
10. Both independent candidates show positive signals, so the precondition for proposing a separately frozen R3 evaluation is met. A combination is not yet demonstrated better than R2; no R3 has been built or run.

## Evidence and trust

The original archive is 203,886,292 bytes; SHA256 `294a0527f2a92579e4799c789875c6d5c37d1b4b60fd7bf50b0dc15a1c073dfe`; CRC PASS. R12_SESSION_EVIDENCE_INDEX.json hashes every retained member, including raw HTTP requests, ADK events, native traces, token observations, explicit/fallback patches, independent checks and cleanup records. The raw archive remains in the local evidence folder and Kaggle Notebook output; it is not embedded in Git.
Actual nvidia-smi and Torch evidence confirms exactly four NVIDIA L4 devices with CUDA access, each 23034 MiB according to nvidia-smi. All eight mounted model files match the frozen SHA256 map. Candidate ZIP hashes and all nine actual SDK generation/budget/prompt configurations pass the post-run audit. Original manifests and candidates were preserved.
Semantic review used the pre-return rubric, frozen Issue statements, model diffs, locked base source context and independent evaluator receipts. It was performed separately from the tested Gemma sessions by the same orchestrating Codex agent, not by a blinded second human reviewer. Django value string conversion, xarray lazy metadata access, and pytest sentinel identity fixes were reviewed; diagnostic-only changes were rejected.
Generic SubprocessManager status is unknown/official_result_missing because this research runner does not emit that generic official result. This raw status is preserved. All nine R12 SESSION_RESULT/R12_METRICS, protected evaluations, HTTP traces and cleanup records exist; PAIR_RESULTS.complete=true. Do not call this an official competition evaluation.

## Resources, stop conditions and cleanup

Observed account quota use rose from 0.000 to 8877.686 seconds, a delta of 2.4660 quota-hours. Remaining at 2026-10-31T06:58:10.450449+00:00: 27.5340 quota-hours, reserved 0s. This is an account-wide snapshot difference, not isolated job billing.
Notebook logs reach archive creation at 4427.61s (about 73.8 minutes), below the 18000s limit and 10 quota-hour cap. The 73200-second prelaunch floor was satisfied by 108000 seconds available. Four physical GPU-hours per node-hour differ from platform quota accounting; no unit substitution was used.
Normal failed repairs were retained and execution continued in order. Infrastructure, backend/context, dependency, positive-control, isolation, evidence or cleanup failure would stop admission and mark remaining sessions NOT_RUN; no such frozen R12 stop was recorded. All session evaluator/agent cleanup records, final server cleanup and owned-root recovery report complete. The generic supervisor caveat above is preserved, not rewritten as an official PASS.
The first read-only artifact download was interrupted; a second read-only download recovered the same Notebook v1 output and passed CRC. No Notebook redispatch occurred.

## Next executable operation

No further GPU operation is part of this frozen run. Review these results and freeze a separate R3 comparison protocol if desired; do not selectively rerun failed R12 pairs. Existing raw evidence can be downloaded and inspected without allocating GPU.

Total: 192 charged tools / 209 attempted tools, 217 LLM calls, 2198857 observed tokens (incomplete), 3375.79 agent seconds.
