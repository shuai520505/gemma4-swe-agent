# Prospective controlled S0 versus EGRD protocol

Version RESET-V1-LOCK-01; NO EXPERIMENT DISPATCHED. Primary question: does the assigned EGRD V0.2 system improve trusted Native Resolved over exact frozen S0 under matched serving and300s? This is a whole-system comparison, not a single-module causal ablation.

## Arms and immutable sources

| Setting | A | B |
|---|---|---|
| Package | Exact S0 ZIP3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9 | Exact V0.2 D ZIP13fccbc33adc6f14c7a3f89bca5f6feaf797925be29f29d77ec0c60ead72d1f1 |
| Model | gemma-4-31b-it-qat-w4a16-ct, official version2 | Same exact weights and serving process |
| Architecture | One LlmAgent; original prompt; six tools; no Skill | One LlmAgent; frozen V0.2 prompt; same six tools + official SkillToolset |
| Generation | Common public Compiler defaults | Existing explicit settings match those defaults |

31B is selected to preserve S0's declared model. Using12B B versus31B S0 would confound this experiment. A12B model-size study is separate, not authorized or launched here. B means the D package of the existing four-arm naming scheme, not an altered package.

### Configuration parity demonstrated on CPU

Official default S0 compilation yields max_output16384/thinking4096, while V0.2 explicitly uses8192/.2/.95/include_thoughts=true. They are not historically equal. `compile_parity.py` uses the official public `generation_constraints` parameter with common defaults8192/.2/.95/thinking4096/include_thoughts=true. Actual Compiler output proves equal compiled generation and equal six base tool names without editing either ZIP or the evaluator. See [CONFIGURATION_PARITY.json](CONFIGURATION_PARITY.json). This is prospective serving normalization, not a reproduction of historical S0's generation settings. No hidden controller, callback override, or package substitution is involved.

Both: context32768; no LoRA, no prefix cache; tensor parallel4 on the same observed4L4 allocation; same runtime dependency set;300s SDK Agent clock starting at official Agent Loop,120s command limit,60 charged tools,80turns. Set common EvalConfig public budget fields; parse the immutable package files without rewriting them. Use identical compaction parameters, then verify and freeze effective output before dispatch. No seed added unless supported and identical; current packages do not declare one.31B must not inherit12B hf-overrides. Exact eight model file hashes come from frozen31B config and must be checked at allocation. Model file-manifest identity, Compiler module hashes, runtime payload, evaluator and SDK distributions, prompt expansion and actual advertised schemas must all enter the final dispatch lock.

Compilation is proven. Full Linux runtime parity, command constraints and Native fixture acceptance are NOT yet proven. If a runtime cannot honor these public parameters, stop before model execution rather than silently editing S0 or calling matched control C the original S0.

## Cohorts and order

[TASK_COHORT_LOCK.json](TASK_COHORT_LOCK.json) freezes six diagnostic pairs and sixteen separate confirmation pairs using a deterministic pre-outcome hash seed. Public129-task pool is a source pool, not official hidden task count. Source selection reads only instance_id/repo/base_commit/problem_statement; no reference patches, hints or hidden evaluator content. Exclude all audited historical/planned IDs. The pool has only one HTTPX task and it is exposed, so the independent cohort covers Rich/FastAPI/Requests. That scope limitation is prespecified.

Pilot:2tasks per eligible repository. Confirmation:6Rich,6FastAPI,4Requests. SHA rankings decide membership and pair sequence; within each phase order is block-balanced AB/BA. Full task/Issue/base identities are frozen now. Snapshot SHA values remain null/NOT_MATERIALIZED: this is **not yet a fully dispatch-ready lock**. Acquire exact official snapshots read-only, verify source/base, and add their hashes in a separate pre-outcome freeze commit before any model request. No task may be replaced because of difficulty or environment results. Prior exposure outside the audited sources is UNKNOWN, so confirmation is held out from this audit/development set, not claimed universally unseen.

Each session uses independent source tree, sandbox, context and patch. No conversations, diagnostics or patches pass between arms. Reuse a healthy identical server without cross-session prefix cache. Preserve raw HTTP/ADK traces, usage, commands/results, source-bound edits, fallbacks, submitted patches, Native JSON, original XML, cleanup and admission records.

## Endpoints and coding

Primary: original official Native Resolved **only after independent trust guard passes**. Preserve raw boolean even if invalid; never rewrite it or use it in the trusted denominator. Valid target failures/timeouts/no-patch outcomes are unsuccessful repairs if the evaluator and evidence are valid. Agent timeout plus valid evaluated fallback can have resolved=true with explicit-submit=false; report both rather than collapsing them. No self-evaluation substitutes for Native.

Secondary: availability and calls/success for load_skill/run_skill_script; initialized exact Issue contract; ledger, hypothesis and Patch Intent existence; first relevant code inspection; first meaningful production edit; revisions; target/regression quality; final source identity; diff review; submit success; response-observed tokens/completeness; tool calls; SDK Agent/Worker/Native/server/setup/archive time separately. First edit is an observation interval if exact event missing. Native time and Agent time are not official competition-wide billed time.

Two reviewers, blind to arm labels where practical, code original Issue/source/patch and test utility after execution; disagreements are retained and adjudicated. A second reviewer is a requirement, not an already completed review. Do not call tests generated by the Agent independent acceptance. No reference repair patch is used by developers/reviewers; official Native evaluator remains unchanged and isolated.

## Trust and stop rules

Before either arm: valid source bindings and snapshot identity; Linux Native fixture/provider and HTTP/HTTPS behavior supported within approved isolation; original evaluator result/XML identity, exit status, nonempty real tests, no setup/runtime infrastructure errors, cleanup independently confirmed. Current Requests CPU02 fails this gate. Fixing it belongs to PR46 engineering; do not weaken restrictions or remove fixture tests.

If infrastructure/evaluator/source/cleanup/evidence integrity fails, stop subsequent sessions; mark scheduled ones NOT_RUN. Retain interrupted pair as invalid, separate from valid repair failures. Do not count it as a loss, silently discard it, replace its task, or selectively rerun it. Any recovery requires a new fully reported authorization/amendment, keeping the original attempt visible. No automatic retries.

After the first two scheduled B sessions: if both have available advertised Skill tools yet neither initializes an exact-Issue contract, stop pilot and diagnose entrypoint only. Missing tool and failed call have different codes. If Skill activates but records are unusable, stop for state-integrity analysis. Do not extend the pilot to fish for a successful activation. Normal difficult repair failures do not stop or change the schedule. Pilot completion and entrypoint validity are prerequisites for any later confirmation authorization.

## Statistical plan

Report n00 (both fail), n01 (B-only success), n10 (S0-only success), n11 (both success), valid complete-pair n, assigned n, invalid/incomplete/NOT_RUN counts and reason. Difference=(n01−n10)/n. Relative difference=(B−S0)/S0 is null if S0 succeeds zero times. No inference from invalid pairs; additionally bound assigned-cohort difference by all missing paired outcomes to expose attrition sensitivity.

Use exact95% Clopper–Pearson intervals for each arm and for B's win proportion among discordant pairs; conservative paired risk-difference95% interval from Bonferroni joint97.5% CP intervals for n01/n and n10/n. Its coverage is at least95%, not an efficient Wald approximation. Two-sided exact McNemar uses2×Binomial(discordant,.5) smaller-tail probability, capped1; no discordance →p=1. Report exact interval method explicitly. `paired_statistics.py` implements this analysis; unit examples are synthetic mathematical checks, not experimental outcomes.

Pilot6pairs is diagnostic only. Confirmation16pairs is the only planned confirmatory cohort; no significance claim from pilot or optional sample extension. Modest improvements will often remain inconclusive at this n. Report Native difference and intervals regardless of p. Secondary outcomes and mechanism associations are exploratory, with no multiple-endpoint significance claims. Do not select favorable tasks or combine past development data with confirmation. Cost per repair is undefined/null if no trusted repairs.

Practical continuation target: at least+10percentage points Native difference, no unacceptable correctness regressions, and no more than25% time/token cost increase in the preregistered matched summary. This is a decision threshold, not a prediction or a powered guarantee. Positive lower confidence bound plus acceptable costs supports expansion; a CI spanning zero requires an inconclusive label, not a claim of superiority. Compare total valid time and token costs as well as per-resolved ratios; canceled usage remains unknown.

## Costs and nonauthorization

At300s caps: six pairs=12sessions≤3600Agent-seconds; sixteen pairs=32sessions≤9600Agent-seconds. Four GPUs would make Agent-only upper bounds4.0 and10.667 physical GPU-hours. These exclude model startup, sandbox setup, Native evaluation, archive and cleanup, and are **not Kaggle quota-hour estimates**. Setup/runtime/resource windows and live platform billing remain UNKNOWN until separately checked. Historical12B load209s is not a31B startup estimate. No dispatch, quota reservation, or formal submission is performed or authorized by this document. Existing CPU gate and explicit run authorization must be rechecked against the concrete immutable package.
