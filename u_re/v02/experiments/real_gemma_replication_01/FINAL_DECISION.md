# V02b real Gemma replication: partial, negative observed results

**V02B_REAL_GEMMA_REPLICATION_PARTIAL**

Two unique GPU SaveKernel requests were dispatched under the new authorization.
Batch1 is confirmed COMPLETE:140361137/v1,4×NVIDIA L4, real Gemma4 31B QATv2,
four real Sessions, original native verification and complete cleanup. Batch2
returned empty HTTP499 at2026-10-23T09:23:44.120814Z. Its platform acceptance and
execution are still **UNKNOWN**, not rejected, ERROR or proven not-run. There
was no retry, third GPU Notebook, new CPU Notebook or formal Submission.

## Native results

|Task|Role|NoEGV|Action-First|
|---|---|---|---|
|fastapi_5077|Predeclared carry|false|false|
|fastapi_11355|New|false|false|
|fastapi_14463|New|null / unobserved|null / unobserved|
|fastapi_9555|New|null / unobserved|null / unobserved|

Observed repair totals are **A0/2,B0/2**, not0/4. Paired categories:
Both0,A-only0,B-only0,Neither2,Unknown2. The carry pair failed in both arms;
among the three new tasks only11355 is observed, also failed in both arms.
The remaining two pairs cannot be counted as failures or successes.

GPU03 remains a separate exploratory A1/2,B2/2 cohort. Across the four observed
tasks from both studies, A1/4,B2/4; the planned six-task description still has
two unknown pairs. Different cohorts/dependency environments and FastAPI task
dependence preclude a homogeneous confirmatory or cross-repository claim.

## What the four observed Sessions did

|Run|Task/arm|Agent seconds|Charged tools|Received tokens|Physical production edit|Native/stop|
|---|---|---:|---:|---:|---|---|
|1|5077 A|211.797|22|219622|None|false / Context Guard|
|2|5077 B|170.969|22|240336|153.133s,DEBUG print only|false / Context Guard|
|3|11355 B|144.637|22|172289|None|false / Context Guard|
|4|11355 A|154.221|23|203275|135.377s,behavioral candidate|false / Context Guard|

Actual source hashes changed in runs2 and4; that does not make either a correct
repair. Run2's sole production change was diagnostic instrumentation. Its green
local pytest had a pass-body testcase with no explicit behavior assertion and
already passed before the production edit. It supplies no discriminating repair
support. Run4 changed annotation-evaluation logic but still failed the original
native contract. TRACE_REVIEW.json binds derived categories to private event
indices and the immutable archive; raw code, model text and patch remain private.

The existing first-source-edit timestamp is retained even for a DEBUG print,
alongside diagnostic-only classification. Generic patch application is also
distinct from correct repair. Diagnostic-only final patches occurred in A1/2
and B2/2 observed Sessions. Neither candidate explicitly submitted a patch in
these Sessions. Zero post-submit calls is therefore not evidence of improved
successful closure. One repeated-search proxy was observed in A,none in B;
strict unchanged-test repeats were0 in both. Those proxies do not certify that
all diagnostic work was useful or that every test input was observed.

Guard reject input counts:15413,15895,15655,15853, above the unchanged15360 input
reservation cap. The300s Agent and60-tool ceilings were not exhausted. All89
model requests received HTTP200 with complete usage. There was no observed
backend collapse, model identity drift, native environment error or chroot leak.
Guard prevented another generation request; all final native results are false.
There is no evidence that extra context would necessarily produce correct fixes.

## Observed cost, including failures

|Metric, confirmed Batch1 only|NoEGV|Action-First|
|---|---:|---:|
|Native resolved|0/2|0/2|
|Agent wall seconds|366.018|315.606|
|Worker wall seconds|422.828|372.233|
|Charged tools|45|44|
|HTTP requests/responses|45/45|44/44|
|Prompt tokens|411215|402797|
|Completion tokens|11682|9828|
|Total received tokens|422897|412625|
|Explicit submits|0|0|
|Context Guard Sessions|2|2|

Action-First observed Agent time is about13.77% lower and total tokens about2.43%
lower in this batch, with no repair success. Token direction differs by task:
Action-First consumes more on5077 and less on11355. Earlier Guard termination is
not a successful-repair efficiency improvement. Tokens per successful repair are
undefined/null because successes are0; Batch2 cost and outcome remain unknown.

Confirmed Notebook code elapsed1468.494s; Agent sum681.624s,Worker sum795.061s.
Non-Agent code time786.870s includes infrastructure and verification. Model-start
to first Worker is a308.818s upper bound including health/idle/supervisor work,
not pure measured weight loading. Account timeUsed rose2986.424 report seconds
between timestamped snapshots; this is not an independently metered Notebook
bill. Per-GPU active time, individual billed GPU seconds and per-Session peak
memory were not independently exposed. Batch2 unknown consumption is not0.

## Empty499 recovery and stopping

Batch2's claim and original HTTP metadata/receipt are untouched. Exact GetKernel
returned403. Two complete owned listings each contained196 records and no target
slug. A delayed listing did not repeat the failed Get query. These visibility
observations do not establish rejection or prove zero platform runs. No
Notebook ID/version/output/JUnit/TaskResult can be attributed to this batch.
Runs5–8 are UNKNOWN_UNOBSERVED with null results. The two-save authorization has
been consumed by two requests; another save cannot be silently substituted.

Current resource identity, if it later becomes visible, must be recovered read
only and bound to the exact frozen source/version before accepting outputs.
Any additional GPU dispatch needs a separate explicit scope acknowledging the
unknown request; this report does not grant one or claim it is safe to resend.

## Q1–Q20

**Q1. Shared payload/CPU identity:** Exact match. Original CPU140352940/v1 raw
archive is re-audited before dispatch; shared ZIP SHA
815d51b0528934283823c7469f42503fb6f388fc406c9e0870a46276be398e63.
The shared production ZIP was not changed. Only outer authorization/batch/read
and offline analysis code were added. Original preparation false authorization
is intact; current independent grant is GPU_AUTHORIZATION_RECORD.json.

**Q2.4×L4:** Confirmed Batch1,each23659151360 bytes. Batch2 allocation unknown.
BATCH_01_EXECUTION.json has actual devices; BATCH_02_EXECUTION.json retains null.

**Q3. Real model:** Confirmed Batch1. All8 GemmaQATv2 files match,TP4,vLLM0.19.1,
torch2.10.0+cu128,CUDA12.8 and the served route match. Batch2 loading unknown.

**Q4. Requests/tokens:** Confirmed89 requests/89 HTTP200 responses,
814012 prompt+21510 completion=835522 received tokens. All confirmed response
usage complete. Whole-experiment totals including Batch2 cannot be established.

**Q5. Eight Sessions:** Runs1–4 completed official Agent/native verification;
all native false,Context Guard true. Runs5–8 unobserved/unknown, not proven not-run.

**Q6. Per-task outcomes:** Matrix above; four known false outcomes, four nulls.
NATIVE_VERIFIER_RESULTS.json binds genuine JUnit/TaskResult hashes for observed
runs; no synthetic or empty-patch baseline is counted as Agent evidence.

**Q7. Success counts:** NoEGV0/2 and Action-First0/2 among observed pairs; two
planned tasks per candidate remain unknown. Do not use a four-task denominator.

**Q8. Action-First-only:** None observed. Two other pairs remain unknown.

**Q9. NoEGV-only:** None observed. Two other pairs remain unknown.

**Q10. Diagnosis without repair:** No improvement observed. B5077 only adds
production DEBUG instrumentation; B11355 never edits production. A5077 also
remains diagnostic; A11355 makes a behavioral candidate edit but fails native.
Physical edit timestamps must not be presented as valid repair timestamps.

**Q11. Submission/closure:** Both arms0/2 explicit successful submits. No
post-submit tools or repeated successful submits were observed, because there
were no successful submits. This does not replicate GPU03's closure advantage.

**Q12. Guard:** A2/2,B2/2 observed Sessions trigger it. Planned Batch2 unknown.
CONTEXT_GUARD_ANALYSIS.json retains each admission/reject/input growth/usage.

**Q13. Guard/result:** It observably blocks the next request before time/tool
caps. None of these final patches resolves natively. No counterfactual success
claim is justified; native outcome and stop event remain independent fields.

**Q14. Costs:** Confirmed costs table above; B slightly lower aggregated Token,
tool and wall costs, but no success and inconsistent per-task Token direction.
No full eight-session cost comparison or Token/success rate is available.

**Q15. New versus carry:** Carry5077 and observed new11355 both have neither
arm resolved. New14463/9555 are unknown. The full three-new-task group is incomplete.

**Q16. GPU03 signal:** Not replicated on the two observed V02b tasks. This
partial study neither establishes a general Action-First advantage nor a
statistically reliable disadvantage. Combined cohorts are descriptive only.

**Q17. Errors/integrity:** Batch1 model,environment,chroot,native identity and
cleanup pass. Batch2 dispatch response is unresolved; it is not a model or
algorithm failure. Offline analysis initially missed Worker guard events, used
a legacy writer bound to the old output directory, and failed to decode a
C-quoted Unicode diagnostic filename. Each was fixed without changing shared
production code or raw archives. Four temporarily overwritten historical
worktree JSON files were restored exactly from their initially clean Git state;
their original hashes and historical commits are unchanged. Repair records and
failed tests are retained; regression tests now check history preservation.

**Q18. Notebook/resources:** Two SaveKernel attempts; one confirmed COMPLETE
GPU Notebook with4 real Sessions,one unknown request. Confirmed code wall time
1468.494s. Account report delta2986.424s is recorded only as an account snapshot
difference. Total platform Notebook/Session consumption including Batch2 is null.

**Q19. Unobservable costs:** Independent GPU billing,per-device active time,
pure model loading,per-Session peak memory and all unobserved Batch2 model usage.
Unknown costs and Sessions are never zero-imputed. RESOURCE_ACCOUNTING.json
retains raw quota snapshots and separates observed/unknown quantities.

**Q20. Formal candidate recommendation:** No new basis to recommend replacing
the official system with Action-First. Observed repair benefit did not recur and
the full four-task replication is incomplete. First resolve the existing Batch2
identity/output, or obtain a separately scoped attempt if appropriate; preserve
this negative evidence. Context/diagnostic behavior may motivate a distinct
future hypothesis, but no hot-fix or rerun is performed here. Action-First still
has no formal Public Score; S0.13/Full.12 remain separate historical results.

## Evidence and publication

Batch1 raw ZIP:3551455 bytes,CRC valid,SHA
6ecb9bfceb0b230ea3f4a2281b219d1e94c1ff2e50d4b0960b8701b4e7af2e45.
Raw HTTP/model/tool traces,evaluator tests,full patches and original TaskResult/
JUnit remain in controlled private evidence. Public files contain hashes,
derived metrics and redacted errors. All original candidate ZIP/member hashes,
task identities,Verifier and PR26/earlier files are verified unchanged.
