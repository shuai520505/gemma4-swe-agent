# Failure autopsy

26 real-model sessions and 784 tool actions were read from the enumerated original archives. There are 25 interpretable native outcomes (13 true / 12 false) and one unknown due to fixture errors. Three true outcomes are owned synthetic repeats; five further true outcomes use the older S2 500s architecture. These counts are audit coverage, not a pooled success-rate estimate for any candidate.

## Observable frequencies

Among 12 interpretable failures, all 12 inspected relevant implementation; seven later attempted a behavioral production edit and five did not. Across all 26, 21 attempted a behavioral edit, including all 13 successes and the fixture-confounded run. “Behavioral” means intended to change task behavior, not necessarily correct. Debug-only/import-only changes are excluded; two documentation-example repairs count because the example is the task's production target.

| Supported pattern among 12 failures | Count | Interpretation limit |
|---|---:|---|
| F7 guard/deadline before satisfactory closure | 12 | Does not show more budget would help |
| F5 verification defect/gap | 7 | Does not prove it caused the native failure |
| F6 repeated/low-information selection | 2 | One direct repeated-test chain; one reviewed interpretation |
| F3 demonstrable generated defect | 2 | One intermediate defect was corrected |
| F4 failure to use adverse feedback | 1 | Exact repeated failing check without revision |
| F1/F2 supported causal assignment | 0 assigned | Not proof localization/causal reasoning were correct; internal understanding remains unknown |

F8 independently confounds one additional real run. F9 remains the appropriate causal explanation wherever event patterns do not establish why a patch is wrong. Global semantic information-gain frequency is null: 784 actions were inspected but no trustworthy oracle labels every action's counterfactual usefulness. Conservative labels must not be reported as exhaustive incidence.

## Located but not repaired

GPU03 NoEGV on 9425 and V02B NoEGV on 5077 read relevant helpers without making behavioral edits. Action-First on V02B 5077 produces green self-tests whose body does not test the defect and adds debug output only. Two 11355 sessions inspect implementation yet produce no edit; V03 P1 eventually edits near 288s after a long sequence of examples and searches. This supports a diagnosis-to-decision gap. It does not establish that a valid minimal repair was already known earlier.

11355's brief Issue and external context make contract uncertainty a plausible contributor. The existing observations do not separate insufficient semantic capability, weak reproduction design, and poor action selection. A more assertive edit deadline could simply make an incorrect patch sooner.

## Verification without dependable repair progress

Direct examples include empty tests, literal rather than stringified annotation checks, self-authored reproductions with nonexistent APIs, no execution after the latest edit, and three identical failing targeted tests with no intervening edit. A stricter assertion counter catches only a subset: an evaluated assertion can still test the wrong contract. S1 EGV's fail→revise→three-pass sequence ended with 42 native failures, demonstrating incomplete local coverage despite real feedback use.

## Successful contrasts and lost opportunities

GPU03 14786 has a compact fail→edit→same-check-pass chain and native success; its Issue also supplies explicit implementation guidance. GPU03 9425 Action-First distinguishes the relevant representations, edits and verifies. These are useful contrasts, not causal proof of a new controller.

Success also coexists with waste: V03 5077 P1 runs 702 collected tests / 162 collection errors, then an invalid path, before focused checks and submission. S2 succeeds without any AgentTool delegation. Three native successes have no explicit submit, thanks to official fallback. CURE's post-submit calls remove a scratch file, whereas some other repeats do no repair work; do not classify every post-submit action as harmful.

No archived sequence establishes that a previously natively correct intermediate patch was later lost. Intermediate local support is weaker and native checks generally occur only at the end. The number of lost correct patches is therefore **unknown**, not zero. M3 checkpoint/selection cannot presently be justified as the primary bottleneck.

## Confounding and negative findings

Task contracts, prior exposure, repository, 300s versus 500s, optional sub-Agent interfaces, output budget, compaction and restored test environments vary. The same FastAPI tasks recur across cohorts. No randomized aggregate comparison or significance claim is made. Formal score decline cannot be attributed from these development traces to EGR instructions. Expanded context removed guard events in V03 P1 but did not add resolved tasks, so budget is not a sufficient explanation.
