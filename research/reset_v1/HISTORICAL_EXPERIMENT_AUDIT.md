# Historical evidence audit
Research branch research-reset-v1; parent ff111c21f8926367fe440e254070db38c2ca3f4a, the reviewed PR46 successor to the directive's stale9ef032a. Created 2026-11-03T15:45:37.709866+00:00.

## What can be counted
56 records have actual model/ADK execution evidence, out of 61 retained execution/evaluator records. Copies are deduplicated by exact raw result plus trace hashes, not candidate/task names; repeated real runs retain separate IDs. CPU replay found inside the R2-A GPU archive is explicitly excluded. A CPU host-environment baseline, pre-first-request CURE failure, and incomplete legacy traces are not counted as confirmed Gemma sessions. See [dataset](HISTORICAL_EXPERIMENT_DATASET.json) and [archive inventory](ARCHIVE_PROVENANCE.json).

| Family | Confirmed Gemma sessions | Interpretation |
|---|---:|---|
| EGRD_SKILL_V01 | 3 | Raw execution; endpoint trust kept separate |
| R12 | 9 | Raw execution; endpoint trust kept separate |
| S0_SUPERAGENT_PAIR | 6 | Raw execution; endpoint trust kept separate |
| R2_EARLY_DECISION | 8 | Raw execution; endpoint trust kept separate |
| LEGACY_cure-gpu-mechanism-01 | 1 | Raw execution; endpoint trust kept separate |
| LEGACY_cure-gpu-mechanism-02-c1 | 2 | Raw execution; endpoint trust kept separate |
| LEGACY_formal-paired-01 | 7 | Raw execution; endpoint trust kept separate |
| LEGACY_harness-v2 | 6 | Raw execution; endpoint trust kept separate |
| RECOVERED_egrd-v032-real-gemma-evidence-ab | 2 | Raw execution; endpoint trust kept separate |
| RECOVERED_gemma4-u-re-actionfirst-abba03 | 4 | Raw execution; endpoint trust kept separate |
| RECOVERED_gemma4-u-re-v02b-gemma-batch01 | 4 | Raw execution; endpoint trust kept separate |
| RECOVERED_meer-v01-gpu-batch02 | 3 | Raw execution; endpoint trust kept separate |
| RECOVERED_gemma4-s2-t500-smoke-gpu01 | 1 | Raw execution; endpoint trust kept separate |

## Candidate identities must not be collapsed
- Exact S0 ZIP 3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9 has six official tools, no Skill, and no explicit generation block. Its historical official submission57261002 now reports0.13.
- Later nine-tool Baseline/SUPERAGENT ZIP 944e1d23ce5e93a77af3e993834487e829487aff0a92ec7fe3e115590bfaf9f1 reports0.15 in submission57666970. It is not S0.
- R2 ZIP af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5 reports0.15 in submission57843305, COMPLETE. It did not exceed that Baseline's public score. R12's3/3 is a scoped development result, not Native3/3.
- EGR V0.4 formal submission57566588 reports0.10. Full's historical0.12 is consistent with submission57505115; the current API description is empty, so that candidate-to-submission mapping remains historical attribution, not a newly proven ZIP binding.
- Current executable-Skill EGRD V0.1 used frozen A/B packages, not today's edited source tree. A is a matched-interface, S0-derived control with shared prompt/generation; it is not exact S0. Two B sessions actually ran. Nine planned sessions did not run.
- Older EGRD V0.3.2 A/B is a different Prompt lineage. Its B is not the current executable Skill system. Two31B sessions do not provide a current Skill activation denominator.
- EGRD V0.2 has CPU scripted sessions only, zero real Gemma sessions. Native trust remains BLOCKED_INFRASTRUCTURE.

Current score observations are read-only Kaggle API observations in [OFFICIAL_SUBMISSION_OBSERVATIONS.json](OFFICIAL_SUBMISSION_OBSERVATIONS.json). Exact immutable candidate/member hashes are in [CANDIDATE_IDENTITIES.json](CANDIDATE_IDENTITIES.json). Prompt file hash and compiled instruction hash are separate: compiler expansion changes the effective instruction bytes.

## Endpoint audit
R12 and the S0/SUPERAGENT development pair have official_native_resolved=null. CHECK_PASS_NON_DISCRIMINATING must not be promoted to Native success. R2-A preserves raw SDK booleans separately from the previously authorized exact-case/semantic evaluation amendment; weak matcher successes are not trusted automatically. CURE C1 and Checklist successes are on lumen_interface_01 synthetic tasks, not hidden public-code repair evidence. Context-guard batches contain both admission rejections and raw verification failures; do not equate them.

For current Skill Pilot Native XML, A Pylint and B Pylint each execute20 cases with2 failures,0 setup errors; B Sphinx executes10 cases with2 failures,0 setup errors. These are real negative results. A separate Sphinx Agent dependency/clock confound remains. These XML observations do not repair the newer Requests CPU02 trust failure.

## Completeness and uncertainty
Dataset fields include exact raw result/trace hashes and member references for each row. Missing commit, exact start/end, hardware allocation, evaluator binary identity or token usage remains null. Earliest/latest model-event timestamps are NOT relabeled as session boundaries. Runtime composite hashes are explicitly identified as composites. Source path classification is a heuristic, not semantic repair adjudication. Model usage from received responses is not total billed usage when cancelled responses are unknown.

MEER matched batch01 currently returns zero output files by API: execution remains UNKNOWN. Full/EGR formal hidden-task trajectories are inaccessible. Three older legacy result wrappers lack sufficient available model trace identity. This is a complete inventory of the inspected sources, not a claim that every historical session ever executed has been recovered or semantically reviewed. Newly recovered raw ZIPs remain locally preserved under raw_recovered/; publication includes hashes/indexes and sanitized derived records rather than duplicating large archives.
