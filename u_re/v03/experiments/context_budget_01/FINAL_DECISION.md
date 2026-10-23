# V03_CONTEXT_PILOT_COMPLETE

Reducing the output allowance from16384 to8192 released real usable input
context and removed the two observed guard stops. It did **not** improve Native
Resolved on these two exposed FastAPI tasks. Both policies resolved1/2, while P1
used more time, tools and received tokens. This is a mechanism improvement
without an observed repair-success improvement; no formal entry is changed.

## Actual execution and evidence

Base: PR27 open/unmerged HEAD `e3fe17d56c05b6a52442b329450dcd88d0c80bcc`.
Preregistration/production source commit `568931a3a3d5d64e54f2d4839ac75cdb51849985`;
sealed CPU proof and GPU build commit `9f60b12` (full commit in Git).

Production payload SHA256:
`0ab04d368e5f911ca7d6c83c3ea2275858abcb4128babd727d14938901466186`.
Original Action-First ZIP remains
`70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8`.
All four runs used this same Prompt, not NoEGV versus Action-First. The trusted
ephemeral YAML override changes only max_output_tokens. Compiler generation,
Config, guard reservation and actual HTTP cap agree. Context32768, safety1024,
thinking4096, seed17, 300s/60charged tools/120s commands stay fixed.

CPU `140394362/v1 COMPLETE`: actual sealed package entry, two real native
empty-patch baselines and two owned synthetic scripted Agent repair cycles.
Both completed Patch/submit/TaskResult/JUnit/HTTP/cleanup; all five real guard
boundary cases passed. `CPU_MODEL=SCRIPTED_ONLY`, real Gemma requests0.
Two earlier local draft builds were never dispatched. Only one CPU Notebook ran.

CPU raw ZIP:1408448bytes, CRC valid, SHA256
`f088eb1377eab33a423277078990e90ba425f75df6d40b6e87897dbf1bb40228`.
`CPU_END_TO_END_ACCEPTANCE.json` is re-derived from that private archive before
GPU launch, including every production member and actual model wire cap.

GPU `140395342/v1 COMPLETE`, private
`wudangdexiaodoashi/gemma4-u-re-v03-context01`: actual4×NVIDIA L4,
23659151360bytes each, TP4, Gemma4 31B QATv2, vLLM0.19.1,
torch2.10.0+cu128/CUDA12.8. All eight weight/tokenizer/template identities match.
Frozen trusted environment before/after matches; native baselines again have
ordinary failures and0errors. GPU chroot canary passed. All four independent
Workers completed and cleaned; seven known model-service processes are gone,
idle_error=null. Exact source/version is checked before and after download.

GPU raw ZIP:4394149bytes, CRC valid, SHA256
`05bbbe3626123f1c4dbc7ce01382867e2d84affca942314fda733b3692d50580`.
See `RAW_ARCHIVES.json`, `GPU_EXECUTION.json`, `NATIVE_VERIFIER_RESULTS.json`
and `INTEGRITY_MANIFEST.json`. Original traces, full patches, JUnit and
TaskResult remain in controlled private evidence outside the public repository.

## Results in frozen order

|Run|Task|Policy|Native|Stop|First behavioral edit s|Agent s|Tools|Requests/responses|Received tokens|
|---|---|---|---|---|---:|---:|---:|---:|---:|
|1|fastapi_5077|P0/16384|true|Guard164.449s,input16858|149.530|164.456|23|23/23|209405|
|2|fastapi_5077|P1/8192|true|Normal end; explicit submit253.112s|182.513|259.806|27|29/29|352727|
|3|fastapi_11355|P1/8192|false|300s Agent deadline|288.080|300.000|40|40/39|452593*|
|4|fastapi_11355|P0/16384|false|Guard145.961s,input15530|none|145.967|32|32/32|255781|

*Run3 has one explained deadline cancellation with no response/usage. Received
token sum is observed; total token consumption for all dispatched requests is
UNKNOWN. No unknown usage is filled with zero. Native verification completed
after cancellation and found an ordinary target assertion failure,0errors.

Paired: Both Resolved1, P0 Only0, P1 Only0, Neither1, Unknown0. Both1/2.
In particular, P0/5077 had a correct final patch even though its next model
request was guard-rejected and it never explicitly submitted. Native success,
guard stop and explicit submission are separate facts. The Runner salvaged the
actual workspace patch; no submit semantics or termination controller changed.

Historical PR27 Action-First/5077 failed, but this fresh P0 control succeeded.
Using the old failure as sole control would have falsely attributed a benefit
to P1. Same seed does not make different real Agent trajectories equivalent.

## H1–H6

H1 supported: cap15360→23552, +8192/+53.33%. P1 actually completed generations
with20430 and22716 input tokens; its cancelled final request was admitted at
23236. P0 maximum completed inputs15206 and14490. All actual transmitted
generation caps match their guard/compiler caps; no guard bypass occurred.

H2 supported in this pilot: P0 Guard2/2, P1 Guard0/2. P1/11355 instead used
the entire300s. This is a changed stopping mechanism, not a repair by itself.

H3 no observed truncation or JSON tool-format regression:123 received HTTP200
responses,122 tool_calls finishes and1stop;0length finishes and0malformed tool
argument JSON. Maximum received completion1963, below8192. The124th dispatched
request was cancelled at the deadline; its completion length/finish/usage remain
UNKNOWN. These observations do not guarantee future long outputs cannot truncate.

H4 limited behavioral change, no success gain: P1 made behavioral edits in both
tasks, P0 in one. On5077 P1 edited later,182.513s versus149.530s. On11355 it
spent most time in repeated searches/diagnostics: an import-only change at
274.974s precedes the first behavioral change at288.080s. Final native still
failed. Edits to imports, diagnostics or DEBUG instrumentation are not counted
as verified repairs. No earlier discriminating local proof is invented.

H5 observed cost increase: P1 has67 versus55charged tools,69 versus55requests,
559.806 versus310.423 Agent seconds (+80.34%),615.704 versus366.717 Worker
seconds (+67.90%),805320 versus465186 received tokens (+73.12%, P1 incomplete
for one cancelled request). Prompt788210/455618, completion17110/9568.
P1 has1 successful explicit submit versus0, with0post-submit calls and0repeated
successful submits. Received tokens on the successful task alone352727/209405;
including failures, received tokens/native success805320/465186. These are
received-usage comparisons, not monetary token invoices or complete cancelled
generation costs. `COST_ANALYSIS.json` preserves per-run and total costs.

H6 directly observed: fewer guard stops and more completed model requests
(68 versus55) did not increase Native Resolved. Lower reservation enables
additional work; it does not ensure that work is useful.

## Trace and measurement qualifications

P1/5077 ran an unnecessarily broad pytest:702collected items/162collection
errors, including unavailable optional pydantic_settings; another command named
a nonexistent directory. Later it passed4wrapped-dependency and1signature
regression tests, removed its diagnostic files and explicitly submitted. Those
green existing tests are recorded as related regression support, not a proven
same-test pre/post reproduction of the hidden native contract. P0 diagnostic
scripts print/catch exceptions; exit0 is not treated as a successful assertion.

These are Agent-side full-suite availability/test-selection limitations. The
trusted frozen native evaluator has0errors in every run and no infrastructure
STOP. Run3's final native assertion failure and300s stop are not a model backend
crash. No dependency was installed differently between policies.

`TRACE_REVIEW.json` binds behavioral classifications to the raw archive. Source
edit timestamps are operation-end upper bounds, never model intentions. First
direct native confirmation occurs after Agent termination at172.310s/267.487s
for the two successful5077 patches; it is not backdated to the first edit.

One offline aggregate initially counted workspace bootstrap as an Agent source
edit. `METRIC_TEST_FAILURE_01.log` preserves the actual regression failure;
the repaired analysis filters by agent_started and observes edit counts2,2,3,0.
No production code, raw result or historical experiment was changed. All13final
local/evidence regression tests pass, including native+guard independence,
cancelled-usage preservation and the source-observation correction.

## Required decisions 1–10

1. 16384 versus observed output: historical195 real responses have P50=90,
P90=521.8,P95=873.9,P99=1741.34,max1936,0length. This is conservative relative
to observed output, not proof that the reservation arithmetic is wrong. Files:
`OFFLINE_OUTPUT_DISTRIBUTION.json`, archive SHAs above and historical source SHAs
inside that file. All195 guard counters match received prompt usage exactly.

2. 8192 frees input in real execution: yes, the actual completed input20430 and
22716 exceeds P0 cap15360. `CONTEXT_GUARD_COMPARISON.json` separates admitted
counts, rejected counts, and completed-response input usage.

3. Output truncation: none observed among123 complete responses; one cancelled
response is unobserved, not a normal finish. Exact separate thinking token
allocation is UNKNOWN. vLLM0.19.1 nonstream usage counts generated token IDs,
including reasoning; the4096 thinking ceiling is not an extra usage charge.
See `VLLM_USAGE_SOURCE_AUDIT.json` and
[tagged upstream source](https://github.com/vllm-project/vllm/blob/v0.19.1/vllm/entrypoints/openai/chat_completion/serving.py#L1474).

4. Guard frequency/timing: P0 at164.449s/16858 and145.961s/15530; P1 none,
with normal259.806s completion and300s timeout. Native outcome is independent.

5. More effective model requests: more completed requests68/55, but no new
successful repair. Request count alone is not useful work. `AGENT_BEHAVIOR_METRICS.json`.

6. More supported production repair: behavioral coverage2tasks/1, native-positive
coverage1/1. No evidence that8192 improved correctness. Local regression and
trusted final-native proof are distinguished in trace review.

7. Native Resolved: P0=1/2,P1=1/2;5077bothtrue,11355bothfalse. Per-result
TaskResult/JUnit SHA256 and0error counts in `NATIVE_VERIFIER_RESULTS.json`.

8. Costs: table and H5 above. Total124 requests,123responses,1270506 received
tokens; entire-request token sum UNKNOWN. Notebook code1668.620s, Agent sum
870.228s, Worker sum982.422s; outside-Agent798.392s. Model-start-to-first-Worker
293.630s is an upper bound including health/idle/imports. Account report usage
delta3378.776s, remaining72830.324s; not an independently itemized GPU bill.
Per-session GPU billing/peak memory UNKNOWN. `RESOURCE_ACCOUNTING.json`.

9. Low-value use of extra context: yes, particularly11355 repeated searching
and late unsupported editing;5077 also spent extra resources on broad pytest
environment errors/invalid paths before useful regression and submission.

10. Replacement decision: **do not replace the formal/default16384 policy on
repair-efficacy grounds from this pilot**.8192 is an engineering-valid option
with demonstrated larger usable history, but the same success and substantially
higher observed cost. Further independently preregistered work may test bounded
diagnostic/tool-output context or dynamic reservation/compression, preserving
native correctness and cost endpoints. No such change or new run is performed
here. Two previously observed tasks in one repository cannot establish a
population advantage, statistical significance, or a Kaggle score prediction.

One CPU and one GPU SaveKernel were sent; no second GPU save, extra Agent,
LoRA, Full/NoEGV comparison, model change or Competition Submission occurred.
Original HTTP200/UNKNOWN_STOP events remain; independent source-pinned reads
confirmed both actual resources and version1. PR27 Batch2 stays UNKNOWN.
Its new distinct status read returned403; preflight complete visibility and
official quota/reservation checks found no observable current resource conflict.
This does not prove its old request was rejected or that historical consumption
was zero. Original candidates and all historical tracked files remain unchanged.
