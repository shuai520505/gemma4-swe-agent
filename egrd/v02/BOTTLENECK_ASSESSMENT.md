# Competing explanations

Denominator: three actual Sessions on one FastAPI task; forty generations,
forty tools. Missing 14297 arms are excluded. Frequencies are descriptive within
this selected cohort, not independent estimates over SWE issues.

| Hypothesis | Classification | Evidence and boundary |
|---|---|---|
| H1 premature context termination | SUPPORTED_BY_OBSERVATION | Actual tokenized inputs exceed 15360 by 247/324/629. Guard prevents generation with approximately 158/219/170 Agent seconds and 40/48/52 tool calls unused (A/B/C). No production patch exists. This proves the stop constraint, not that continuation would repair. |
| H2 inefficient evidence gathering | SUPPORTED_BY_OBSERVATION, narrow cases | A varies order before correcting an invalid scratch graph, then uses print-only checks. B reads runtime solving before explicitly redirecting to OpenAPI. Their counterfactual savings are unmeasured; most source windows are new and legitimate uncertainty remains. |
| H3 evidence-to-patch decision gap with a defensible edit already available | PLAUSIBLE_NOT_ESTABLISHED | Relevant code and candidate hypotheses are visible, but no correct repair direction is independently validated before termination. No observed earlier-edit opportunity meets the stated criterion. |
| H4 insufficient root-cause understanding | PLAUSIBLE_NOT_ESTABLISHED | Emitted text explicitly questions sharing/visitation assumptions; A's reproducer does not expose the defect. This establishes unresolved hypotheses, not an exhaustive diagnosis of internal capability. |
| H5 optional Skill non-adoption | SUPPORTED_BY_OBSERVATION | B/C real schemas expose Skills but list/load/script calls are 0/0/0. Awareness, deliberate avoidance and counterfactual utility are unknown; no assertion script was ready in B/C. |
| H6 inadequate verification design | SUPPORTED_BY_OBSERVATION in A | Five diagnostic execution attempts,0 assertions, malformed early graph and later non-failing examples. B/C execute no check; their nonexistent check quality cannot be graded. |

## Primary bottleneck judgment

The most strongly established **technical termination mechanism** is fixed
reservation plus uncompressed accumulated history. It is not an arithmetic bug,
vLLM failure or time exhaustion. The most concrete **decision defect** is A's
confounded reproduction/weak verification, not proof that all agents should
have edited sooner. H3 does not receive a stronger label simply because all
native outcomes are negative.

Three negative findings matter: no compaction/restoration growth, almost no
repeated source lines, and no previously supported production patch. They weaken
respectively a compaction-bug fix, a generic duplicate-read cache, and bounded
patch-selection priority. The old V03 experiment also falsifies a blanket claim
that removing guard stops suffices for another resolved task.

Context management is a more directly supported mechanical target than a
proven evidence-to-edit controller, but neither intervention has established
repair efficacy here. Global context mutation lacks a verified competitor
deployment path. An additional optional evidence Skill does not address its own
observed non-adoption and would duplicate MEER. No causal probability, dominant
population failure rate or official-score explanation is assigned.
