# Implemented changes

Only result_contract.py runtime trust checks changed. No source-binding, package, model, prompt, official tool, official test, SDK evaluator or sandbox-network setting changed. No dependency was installed; released provider source was read as data only and is not on the runtime import path.

native_execution_check now identifies the conjunction HTTPConnection + NewConnectionError + [Errno13] Permission denied in original failure traces. Four actual CPU02 failure records are rejected in an owned classifier regression. Normal assertion failure and an unrelated errno string remain admissible. This is conservative research infrastructure gating, not scoring modification.

Executed testcase bodies now exclude both skipped and setup-error nodes:135 bodies versus324 collection records, including131 passes and4 failed bodies. The187 provider setup errors were never test-body executions.

New forensic code and tests are under native-recovery/. Compiler tests execute the unchanged sdk_acceptance logic against an isolated package copy, preserving historical compiler receipts. Current FINAL_REPORT replaces the landing report only; its exact prior bytes are preserved at native-recovery/previous/FINAL_REPORT.md. Existing CPU archives, raw results, historical reports and claims remain intact. Before/after hashes are recorded separately.

The initial fixture-evidence test run contained a label-format mismatch (NOT_RUN plus reason in one field). It was corrected to separate status and explanation; failure logs and the successful follow-up remain preserved. This did not change the acceptance gate or any official expectation.

## Evidence identity and execution boundary

Generated UTC: 2026-11-03T15:07:52.529834+00:00. Audited PR46 source commit: `9ef032ab23335cb5a09c4937d7962205f5962f79`.

Task `requests_6589`, base `7a13c041dbef42f9f3feb14110f02626f6892e9a`, Issue SHA256 `60b61eb2b26e1135174dd59ddc4e29b2d7fe2b5e255b723e9085b36407663d04`, snapshot SHA256 `053f2ea73cb7b604f535ee2eabe596dae9df9d7ff54a365d62b4ff0bebab7115`. Package B SHA256 `9a8566523e4463889a6e8f61d7cb7e760fd48873ea9827e529b29c5abca6fa80`. Official evaluator swegemma0.2.11 source SHA256 `99e2a5fdab2be2b5e0388de29080da9d6e7003cf8b53299cda790464f4ecd2aa`; unchanged.

Original CPU02 archive: `cpu02-output/egrd-v02-cpu-hardening02.zip`, SHA256 `25b2a360c62023c48617fe8c3bb8734d4230a2d3668eccc33cb4e22f20fcf25a`. Raw records: `cpu02-evidence/worker/trusted/NATIVE_RESULT.json`, `native-junit-0.xml`, `NATIVE_COMMANDS.json`; Agent/Native cleanup receipts and original session/done hashes retained. Full191 failure/error case identities, trace hashes and excerpts: `native-recovery/AUTOPSY.json`.

Commands/timestamps/exit codes: `native-recovery/REGRESSION_EXECUTIONS.json`, `FOLLOWUP_EXECUTIONS.json` and referenced logs. Actual prior Native pytest command is recorded verbatim in AUTOPSY.json; exit1. Prior worker stage exit0 did not imply trustworthy test execution. New CPU SaveKernel0, GPU SaveKernel0, Gemma requests0, packages installed0. Local tests validate classification/source evidence; they do not replace Native evaluation. New Linux service acceptance and Native revalidation are NOT_RUN.
