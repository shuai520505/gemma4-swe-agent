# Matched descriptive comparison

| Task | A EGR | B executable MEER | C advisory |
|---|---|---|---|
| fastapi_14297 | NOT_RUN | NOT_RUN | NOT_RUN |
| fastapi_14459 | false | false | false |

Primary B/C: one neither-resolved pair, one unknown pair, zero B-only or C-only
wins. B's executable Skill is bypassed1/1observed sessions, as is C's advisory
Skill1/1. Both real request schemas expose the same four Skill tools and six
official tools, but neither arm lists, loads or invokes the Skill. There are
zero actual verifier checks/verdicts and zero production edits. The executable
algorithm's efficacy therefore remains untested despite real Gemma inference.

| Observed fastapi_14459 cost | A | B | C |
|---|---:|---:|---:|
| Real model requests / HTTP200 | 20/20 | 12/12 | 8/8 |
| Prompt tokens | 156970 | 96284 | 49990 |
| Completion tokens | 4488 | 2527 | 4075 |
| Total received tokens | 161458 | 98811 | 54065 |
| Charged tools | 20 | 12 | 8 |
| Agent seconds | 142.019 | 80.655 | 130.356 |
| Worker seconds | 172.905 | 111.292 | 160.883 |
| Skill script calls | N/A | 0 | 0 |
| Actual production edits | 0 | 0 | 0 |
| Explicit submits | 0 | 0 | 0 |
| First actual input tokens | 2199 | 2999 | 2999 |

B/C have identical first request messages and tool schemas, with the same normal
Issue user input as A. The interface/instruction package adds800counted input
tokens at the first request versus A (5.21%of the15360input allowance), even
though its script is unused. This identifies initial interface token overhead,
not its causal effect on eventual repair or all later trajectory costs. The
missing opposite-order task also prevents a two-task order-balanced comparison.

B/C observed token cost is82.76%higher and tool use50%higher, while Agent time
is38.13%lower. These are divergent realized trajectories, not isolated costs of
the verifier: its script never ran. Faster guard termination without a repair
is not evidence of useful efficiency. B/A and C/A both tie on the observed
negative outcome; their package comparisons also include interface metadata
and guidance differences. There is no evidence that the verifier caused harm,
nor evidence that it improved repair decisions.

All40responses finish with tool_calls; none reports length truncation. Three
new generations are prevented by the common fixed reservation guard. Actual
thinking usage is not separately observed. No confidence intervals, significance,
cross-repository generalization or leaderboard improvement are inferred from
one completed FastAPI task. Classification: MECHANISM_BYPASSED; efficacy
INCONCLUSIVE. S0 remains the best-observed official baseline, unchanged.
