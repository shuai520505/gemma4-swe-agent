# Feasibility and expected value

| Dimension | M1 causal localization | M2 evidence-aware action selection | M3 bounded patch selection |
|---|---|---|---|
| Target evidence | Relevant code read in 12/12 failures; causal understanding unknown | 7/12 verification gaps; direct unchanged failures and no-op checks | No proven lost natively correct intermediate patch |
| Executable change | Optional sandbox AST/call-site inventory | Existing MEER source/check identity, stale/duplicate verdict; prospective decision use | Optional snapshot/revision/check comparison |
| Allowed interface | Official Skill sandbox subset | Official Skill subset; global callback controller unavailable | Sandbox files possible; reliable automatic selection unverified |
| Added cost | Parsing, context tokens, invocation | Hashing + selected check + Skill/model turns | Copies/diffs, repeated checks, extra model revision |
| Failure risk | False static relationships, context growth | Wrong assertion appears supported; bypass; bureaucracy | Restore good edits away; choose overfitted patch; exceed budget |
| CPU validation | Known caller fixtures; bounds; parser failure | Freshness/duplicates/assertion execution/timeout already tested in MEER | Atomic snapshot/restore, stale version rejection; no correctness proof |
| GPU validation | Whether localization changes actual repair | Adoption, discriminating checks, useful next actions, native outcome | Whether revisions improve native results and preserve prior successes |
| Causal isolation | Inventory versus same interface inert | Executable B versus interface-matched C, unchanged prompt | Snapshot/select versus same metadata with no selection |
| Expected value | Plausible semantic aid, not evidenced as dominant need | Best diagnostic priority; benefit not yet established | Highest unsupported assumptions/cost; defer |

**Competition evidence:** official [data/competitor guide](https://www.kaggle.com/competitions/gemma-4-developer-agent/data) and [rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules). Web readers returned no rule body, so current unseen private infrastructure is not certified. Independently rehashed guide `445000…aa1f`, compiler0.2.13, ADK1.36.1, swegemma0.2.11 and module identities are in SOURCE_AUDIT.json.

Pinned guide2.1–2.3 permits declarative registered LlmAgent/Sequential/Parallel/Loop workflows, AgentTool and sandbox skill scripts. It does not permit arbitrary competitor Python host entry points or changing trusted tools/evaluator. `callbacks.py:84` returns no callbacks without organizer registry; native Runner supplies none. A YAML callback name is not a supported global controller. The compiler passes the official sandbox executor to Skills. Built-in workflows can order Agent execution but do not enforce semantic evidence quality and introduce further inference.

| Claim | Status |
|---|---|
| Native six tools and official Skill scripts | CONFIRMED for pinned interface |
| Helper-local assertion, freshness, duplicate and timeout behavior | CONFIRMED implementation capability; historical scripted tests, no new efficacy claim |
| Enforce use of Skill / intercept every search or submit | NOT AVAILABLE through established competitor interface |
| Host callback registry injection / modified Verifier | Rejected; unsupported competitor change |
| Model understands relevance or follows advisory next action | UNVERIFIED until real inference |
| Scratch evidence is tamper-proof trusted state | False; do not claim |

M2 is the most defensible research priority, but choosing a new M2 production mechanism now would duplicate MEER before measuring its unresolved adoption bottleneck. M1/M3 remain hypotheses. No numerical predicted gain or probability is assigned.
