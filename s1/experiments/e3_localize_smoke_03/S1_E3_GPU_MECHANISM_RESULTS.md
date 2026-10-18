# E3 GPU smoke03: stopped; no complete pair

**No-Go for multi-task confirmation. E3 was not run, so its mechanism and
relative repair benefit remain untested.** The real31B Control ran and produced
an applicable but incorrect Patch. The frozen stop classifier falsely treated
an assertion's test data as an environment error and prevented E3 from starting.
No hotfix, retry, continuation or trajectory splicing was performed.

## What actually executed

Preregistration and accepted CPU evidence were pushed in e72d78a before GPU
dispatch. Protocol SHA256:
`83e1eadca7d4c0efeb3d2e5107240e6dc4409c009236504350ae63790ec3436e`.
GPU Notebook version1 completed; completion means the Notebook finished, not
that the pair passed. Only control/rich_3278 ran. E3 is explicitly not_run in
the frozen batch gate. All model, candidate, task, source and wheel checks passed.

CPU02 passes100/100. Actual native clean-base Phase2 gave7 passed/16 ordinary
assertion failures, with no environment error. The same readiness check passed
again on the GPU host before model startup. No reference repair was used or
provided to the Agent. The first CPU preparation's missing required models
argument is separately archived; it did not qualify for GPU. See CPU_VALIDATION.md.

Real Gemma4 31B QAT v2 on4 L4/TP4 passed model route, actual READY generation
(16 input+2 output Tokens), tokenizer/usage equality and oversize rejection.
Both frozen candidates compiled under identical registered constraints. Only
Control then executed: output16384/thinking4096/seed17,300 seconds/60 tools,
six official tools, omitted include_thoughts and sampling parameters. No Prompt,
ZIP, model, timeout or strategy was changed after registration.

## Why the pair stopped

Native Control Phase2 is **19 passed,4 failed**, exit1, resolved=false. All four
failures are existing assertions in test_decode_issue_2688, not fixture setup or
collection errors. The saved raw official result and supervisor classify a
nonzero test exit. The new research audit instead emitted unknown/environment
and stopped because session.py searches all test output using:

```text
\bERROR\b|\b\d+ errors?\b|INTERNALERROR|ModuleNotFoundError
```

An existing test string says `Found 4 errors in 2 files`. That string appears
in parametrized node names and assertion source, matching the predicate14
times. The final Pytest summary has4 failed/19 passed and no setup/collection
error sections. This is a **stop-classifier defect**, not an unresolved Rich
Verifier dependency. CPU reproduction against the exact retained output is
analysis/reproduce_gate_false_positive.py, with its actual stdout/stderr logs
and match locations in classifier_false_positive.json.

The executed audit's unknown, raw native resolved=false/exit1, batch STOP and
not_run are all retained unchanged. A separate posthoc attribution records a
confirmed Control assertion regression. This attribution does not reopen the
experiment, retroactively start E3, or create a complete pair.

## Comparison permitted by the evidence

Times below are successful tool-response times after native Agent start.

| Metric | Control | E3 |
|---|---|---|
| First relevant implementation read |10.189s,rich/ansi.py |not_run |
| First production diff |72.839s,incorrect |not_run |
| First complete correct repair |none observed |not_run |
| Tool calls before production edit |4 |not_run |
| Exact repeated reads / overlapping read operations |0 /2 |not_run |
| Failed tool calls / schema errors |1 /0 |not_run |
| Post-edit execution of actual changed workspace code |yes,4 Python probes |not_run |
| Agent execution of existing tests |no pytest run |not_run |
| Patch |1254 bytes,applied;4 old-behavior regressions;2 leftover diagnostic files |not_run |
| Explicit submit_patch |none;native fallback captured Patch |not_run |
| Actual official Phase2 |19 passed/4 failed,exit1 |not_run |
| Official resolved |false |not_run;no verdict |
| Native LLM / tool calls |18 /17 |not_run |
| HTTP requests / received responses / cancellation |20 /19 /1 |not_run |
| Observed input/output/total Tokens |101572 /8966 /110538,partial |not_run |
| Agent /worker seconds |300.043 /328.111 |not_run |

The legacy automated first_edit_action_seconds=62.394 refers to writing a
diagnostic script, not a production repair. It is not used as the production
edit endpoint. A successful edit response does not establish correctness.
No success-rate or relative Token/time advantage can be estimated from this
incomplete pair. B is not a confirmed failure and is not assigned zero usage.

## Actual trajectory and negative evidence

The complete17 tool events and returned content are in analysis/*-tools.json
and the companion timeline; original ADK JSONL is immutable under results/gpu.

| Tool event | Time/result | Evidence and implication |
|---|---|---|
|1 |8.332s |grep pipeline exits1 with no output;one failed command,not a schema error |
|2 |10.189s |reads ansi.py lines1–120,including regex and special handling of `(`;correct area found early |
|3–4 |62.420–64.458s |writes/runs regex reproducer against workspace source;private0–? cases do not match |
|5 |72.839s |changes character class from `[(@-Z\\-_]` to `[0-?@-Z\\-_]`,adding required range but dropping `(` |
|6–8 |74.352–92.086s |updated source matches private cases;tokenizer probe prints successful comparisons |
|9–10 |99.552–130.079s |paren probe returns literal ESC( in plain text:counterevidence to preserved old behavior |
|11–13 |150.059–161.745s |partly overlapping reads and caller-symbol grep;no subsequent production correction |
|14–15 |248.146–251.323s |new private7 assertion passes,duplicating a previously checked private path rather than addressing paren behavior |
|16–17 |255.519–257.278s |git status shows diagnostics;git diff shows same wrong production change;no cleanup or submit follows |
|native deadline |300.043s |final HTTP request cancelled;fallback retains production change plus repro.py/reproduce_issue.py |
|native Phase2 |after Agent |all16 new private cases pass,4 of the7 previously passing cases regress |

The production change left about227 seconds. Early editing therefore did not
solve this Control run's verification/submission problem. The old branch
`if sgr == "("` became unreachable for ESC( sequences because the regex lost
that alternative. The final Patch and four assertion tracebacks directly
support this cause; it is not inferred from a reference solution.

Four post-edit Python probes actually executed the modified workspace
rich.ansi. The pre-edit module SHA was
`883eb9df6418aa7066ea1003ba52a3ad5f25f24149fbd7c4568a072471f784c8`;
post-edit Agent and native Verifier both report
`af970abc146f4def7932f67e9da6f7411e0ee27e2c2de5492f3a4d3d21d71d1f`.
This fixes the earlier wrong-installed-package ambiguity. Import provenance
alone is not a passing test. Most probes print results; the final assertion
checks only private7. The paren counterexample is not converted into a repair
or an old-behavior assertion, and no existing test file runs inside the Agent.

Two reads overlap earlier ranges:events11 and13 overlap event2. Their purpose
was investigating tokenization, so overlap alone is not declared waste. The
later private-only repro adds little new contract coverage after events6–8;
this is the stronger content-based redundancy finding. Event1 is an empty
search; no broad repeated-search sequence is invented. None of these Control
observations establishes how frozen E3 would behave.

## Cancellation, reclamation, cost and evidence limits

All20 dispatched requests have20 known terminal records:19 received responses
and one observed CancelledError, request_id
`4ca3231d3b2e40f2864874533e7e1df5`. Cancellation is recorded0.0081 seconds
before the independent native Agent-end event. The native300-second error,
Patch checkpoint and verified worker/sandbox cleanup agree. CancelledError
was propagated; its terminal usage is null/partial, not an inferred zero.

Independent server metrics show running=waiting=0 at9.982,10.994 and12.007
seconds after cancellation. This satisfies the preregistered reported-idle
gate and establishes no reported residual at those observations. It does not
prove immediate backend abort or recover missing usage. Server finished-stop
counter=20 (startup+19 returned Agent responses),abort counter=0. Backend text
log was not exported; an additional read-only output download found only
vllm_config.json and the platform log. Do not invent a request-specific abort
acknowledgement. Seven observed server PIDs terminated with no forced kills;
worker process tree and both sandbox cleanup gates pass.

Observed usage110538 is only the19 received responses,including compaction.
Raw official total_tokens=0/cost_usd=0 are preserved; they are not evidence of
zero model cost. Observed maximum input8263/output3184 and no length finish
do not indicate an output/context cap bottleneck in completed responses.
The platform log spans1020.728 seconds (about17.01 minutes),giving about1.134
L4-hours as a4-device allocation proxy,not billing or pure inference time.
No complete Token cost or A/B cost delta is available.

Native Trace,incremental ADK,all tool results,raw HTTP/lifecycle,Patch/apply,
full Phase2 stdout/stderr,metrics and cleanup are saved. Raw JUnit XML was not
exported on the failing native run before sandbox cleanup; the authoritative
available verdict is the unmodified Pytest output and TaskResult. Backend text
log and the cancelled response/usage remain explicit gaps. B has no artifacts
because it never started,not because its files were lost.

GPU raw SHA256:
`9279f95aadab5b4802c12bd4546ed78db44374173a451eb80bb9b66ce39c0159`.
CRC and319 outer/114 nested manifest entries pass; nested Control ZIP SHA256
`9f99fbcf797bb97253f69b56f4ddf85534072b722521219ca0237aceb1c80894`.
All115 runtime source bytes match accepted CPU and registration,including
the unchanged buggy predicate. Exact model8-file,41 model-wheel and124
task-wheel maps match protocol. See post_execution_integrity.json and delivery_manifest.json.

## Decision and smallest next step

A–D (E3 behavior change,less useless exploration,premature wrong Patch,and
verification/submission headroom) **cannot be answered comparatively**:E3 never
ran. This Control demonstrates an early but regressing edit,not an E3 failure.
E. **No-Go for multi-task confirmation now**,because there is no complete pair.
This is not a rejection of E3's algorithm.

The smallest necessary next infrastructure change belongs to a new version:
classify structured Pytest/JUnit error versus failure outcomes,not arbitrary
traceback/test-string substrings;capture JUnit on failed verification before
cleanup. CPU regressions should include this exact `Found 4 errors` fixture
text,ordinary assertion failures,and genuine collection/setup errors. Verify
backend log export against the actual server API/lifecycle. This study's source
and STOP remain frozen; the diagnostic reproduction does not patch the runner.

Only after that CPU gate should a separately registered new full smoke pair
be considered. Do not reuse this A. Reusing rich_3278 would be exploratory
because its Control behavior is now observed,even with unchanged Prompts. A
later multi-task confirmation requires fresh tasks and balanced control-first/
E3-first order,with source/budgets/criteria frozen before outcomes. No additional
GPU study,Prompt tuning,LoRA or leaderboard submission is launched here.

S0 Public0.13/submission57261002 remains the only confirmed leaderboard result.
