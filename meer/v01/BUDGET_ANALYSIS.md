# Measured costs and limits

These are CPU engineering measurements on an owned6file tree, not Gemma benchmark estimates. Scripted tokens/usage are artificial and excluded from model-efficacy/cost conclusions. Real Gemma token use and added inference cost: NOT_MEASURED.

| Arm | Scripted HTTP requests | Official charged tools | Agent seconds | Synthetic resolved | Cleanup |
|---|---:|---:|---:|---|---|
|A|9|6|2.966|True|True|
|B|13|9|3.643|True|True|
|C|13|9|2.741|True|True|
|B_BYPASS|10|6|1.017|True|True|

Columns above:arm, scripted HTTP requests, native charged tools, Agent seconds, synthetic resolved, cleanup. Detailed Worker times are in CPU_ACCEPTANCE_CPU03.json. B performs2actual assertion subprocesses plus1duplicate skip; total local helper wall time 0.657835s. B versus matched C Agent-time difference 0.901811s is one sequential CPU observation, not a reliable speed estimate. Native Skill transport/materialization also costs time and is included in Agent/Worker duration. The mechanism makes no model calls internally, but calling/loading it creates model turns/tool calls: actual counts above, not zero-overhead.

Frozen candidate budgets:300sAgent,60official charged calls,120scommand;32768context,16384output,4096thinking,seed17. Safety1024 belongs to a common research Context Guard, not a field magically enforced by candidate YAML. Future GPU uses an identical pinned guard for all arms. The organizer's default session budget is60minutes/100tools, while this candidate explicitly selects5minutes/60/120; these are experiment choices, not universal competition ceilings. Official context/size/allowed-model limits are independently documented.

The helper bounds one check to15s and hashes at most30000files/64MiB; source budget/timeout/unavailable evidence becomes UNKNOWN. No auto-expansion, dependency install, additional model, or verification loop is added. Several15schecks could still waste a substantial fraction of300s: cap is protection, not proof of optimal resource allocation. Repository-scale hashing overhead, live tool-context tokens, Gemma skill uptake and inference latency need the matched GPU experiment. Native charged skill calls count as observed; no custom counting or budget bypass is installed.
