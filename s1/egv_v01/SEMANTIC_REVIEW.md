# Offline semantic review, not inference

These are human review cases against the frozen103-word rule. No model or
scripted fixer supplies these actions;they are not new Gemma trajectories or
counted repair successes. There is no synthetic policy function whose output
is presented as proof that the Prompt works.

| Hypothetical evidence | Intended unified EGV decision | Clause and limit |
|---|---|---|
| Parser probe is valid text but cannot select the handler under repair | Repair the minimal input/route gap before treating its output as a check | input reaches relevant behavior;successful execution alone is insufficient |
| A reproducer imports installed package while workspace differs | Resolve import provenance using existing setup/path evidence or a targeted check | current workspace implementation;does not demand extra path-printing on every call |
| Same code,input,environment and hypothesis;output already known | Inspect the existing failure or choose a discriminating observation instead of identical rerun | what new result could change Patch/plan;not a universal ban on repeats |
| Patch changes code that the earlier test exercises | Rerun focused assertions and relevant old-behavior regressions | code change makes repetition legitimate;regressions expressly retained |
| Reproducer raises due to Patch initialization | Correct Patch/plan and rerun the valid input | consequence link;an unrelated script API error must be distinguished |
| New case passes but old behavior fails | Investigate old failure and preserve required contract;do not submit as fully verified | retain relevant old-behavior regressions;no evaluator knowledge assumed |
| Supported repair,focused and relevant old checks complete,no unresolved actionable evidence | Review diff and explicitly submit with real remaining limitations | sufficient checks then review/submit;no invented clock nudge or automatic success |

The rule expresses all seven intended decisions without task-specific names or
long output schemas. This is semantic plausibility,not measured model
compliance. Misjudging reachability,overconfidence about sufficiency and
using provenance investigation as a new time sink remain open risks.
