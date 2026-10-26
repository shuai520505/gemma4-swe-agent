# Pinned official interface, not research-host capability

Primary sources: [official competitor distribution](https://www.kaggle.com/competitions/gemma-4-developer-agent/data),
[competition rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules),
hash-verified HARNESS_README and official adk-submission 0.2.13/google-adk 1.36.1/
swegemma 0.2.11 wheels. Current web reads returned 0 body lines. Conclusions below
refer to the pinned distribution; unseen current/private platform behavior is
not guaranteed. Wheel/member hashes and line counts are in SOURCE_PROVENANCE.

## Deployment facts

- **CONFIRMED_ALLOWED:** registered declarative Agent/workflow classes, ordinary
  registered tools, official SkillToolset and sandbox scripts. Guide 2.2–2.3;
  actual Runner constructs AdkSandboxCodeExecutor and passes it to compiler
  (`agent_runner.py:609–625`). Historical CPU evidence validates this Skill path;
  this audit does not launch another Compiler/Agent session.
- **Not available through the pinned competitor interface:** arbitrary host
  Python agents/tool wrappers, custom history processors or a supplied callback
  registry. Strict Agent schema forbids extra fields. Callback names alone
  resolve to no functions when registry is None (`callbacks.py:84–85`); actual
  Runner supplies no registry. The offline test executes that pinned resolver.
- App events_compaction_config is a **host EvalConfig** capability (default None),
  not an Agent YAML field. The guide documents only budget/time/turn evaluation
  overrides. The full local inference-config loader is missing, so do not claim
  either an undocumented allowed compaction override or unseen global policy.
- `include_contents=none` is allowed but retains the current user's task/tool
  chain (`contents.py:541–585`); it is not a per-generation reset or selective
  evidence compactor. A pinned-function offline test confirms this distinction.

## Five candidate mechanisms, all ten required dimensions

| Dimension | M1 context evidence compaction | M2 source-bound evidence state | M3 next-action assistance | M4 adoption intervention | M5 bounded patch revision |
|---|---|---|---|---|---|
| Observed failure | Accumulated history→guard | Stale/unverified evidence in broader history, not exercised here | A's bad probe; B/C unresolved hypotheses | B/C zero Skill calls | No lost production patch observed here |
| Executing code | Host history projector/summarizer; optional script can only compact its own output | Sandbox hash/check/receipt script, already MEER | Sandbox classifier of observed receipts; causal judgment still model | Metadata/instruction edits alone are Prompt; workflow sequencing can execute, Skill call still optional | Sandbox version checkpoints and bounded restore helper |
| Enforceable scope | Global projection unavailable; no host interception | Own receipts/hash freshness only | Own report/timeout, not global action choice | Built-in sequence if Agents finish; cannot force optional tool invocation | Own restore/check budget only |
| Advisory remainder | Which evidence is semantically needed | Test relevance, truth of model-authored state | Repair hypothesis, next tool/edit/submit | Whether to invoke Skill | Which patch is correct, bypass via normal tools |
| Allowed deployment | GLOBAL_UNSUPPORTED_IN_PINNED_AGENT_INTERFACE; local output compaction Skill subset allowed | CONFIRMED_ALLOWED Skill subset | CONFIRMED_ALLOWED advisory Skill subset; global controller unsupported | Prompt metadata allowed but not executable innovation; workflow allowed, no deterministic startup-Skill hook established | CONFIRMED_ALLOWED Skill subset, global revision bound unavailable |
| Added costs | CPU history traversal or extra summary inference; unknown until path exists | Hashing/receipt bytes and optional calls | Extra tools/metadata; possibly repeats MEER | Existing interface adds 800 initial tokens; workflow adds context/model calls | Diff/checkpoint I/O plus repeated tests/calls |
| Harm risks | Erase key counterevidence/Issue/code, summary drift | Tautology/wrong-contract receipt, scratch tampering | Wrong recommendations, overconfident earlier edits | More instructions/latency and still bypassed | Restore inferior patch, spend repair budget comparing |
| Isolation from other factors | Same guard/output/Prompt; approved projection-only hook required | Same interface/inert script as MEER | Matched inert reporter with same interface/guidance | A guidance-only change is not mechanism causality; workflow changes architecture | Active/inert restore interface with equal resources |
| CPU correctness tests | Exact token replay; preserve IDs, Issue, latest source/adverse checks; obsolete receipt tests | Version change invalidates evidence; duplicate and timeout tests already exist | Contradictory/stale/unknown fixtures and no semantic overclaim | Actual compiler plus adoption possible only under real model, not scripted success | Safe revert, failed revision, stale baseline and clean workspace tests |
| GPU falsifier | Smaller history but no repair benefit or new regressions/cost excess | Used fresh evidence but no meaningful change/improved native outcome | Advice used but no better edits/outcomes or causes wrong patches | Same bypass rate or more cost without useful checks | More revisions but no added native success or damages previously successful repairs |

## Selection constraints

Skills can read task workspace/scratch state, not mutate the host ADK event
history through an established supported API. Writing a ledger is not global
context control. A multi-agent handoff can change context boundaries, but adds
inference and can fail to hand off before the guard; it is a separate architectural
factor, not a minimal proven compaction fix. No desired mechanism is smuggled
into the research Runner as if it were a competition submission feature.
