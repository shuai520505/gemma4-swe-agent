# Requests environment fix decision

Decision: NO_COMPLIANT_ENVIRONMENT_REPAIR_AVAILABLE under the present constraints. Stop at PhaseB; do not dispatch another CPU acceptance run or GPU job with a known-incompatible environment.

Prerequisites are an approved registered pytest-httpbin2.0.0/httpbin dependency closure, an auditable confinement-compatible real local HTTP/HTTPS service, and legitimate socket/timeout behavior for the four unchanged timeout tests. Current confinement forbids the socket capability itself. This task prohibits weakening it and prohibits unapproved package installation.

No fake httpbin fixture, test skip/xfail, deselection, mocked timeout, external web service, TLS-verification bypass, syscall relaxation, host socket mount or substitute evaluator is introduced. A future separately approved runtime/dependency solution would need engineering and real Linux validation; it is not claimed implemented here. Supporting only loopback would not by itself establish the numeric-address timeout tests' behavior.

The minimal compliant code change in this task is a stricter Native infrastructure classification: real socket EACCES wrapped as HTTPConnection/NewConnectionError is rejected even when pytest puts it in a failure tag. Ordinary behavioral assertion failures remain admissible. Setup-error cases are removed from the executed-body count, correcting322 to135. Neither change can promote a failed trust audit to PASS. Raw official resolved values and scoring code remain unchanged.

## Evidence identity and execution boundary

Generated UTC: 2026-11-03T15:07:52.529834+00:00. Audited PR46 source commit: `9ef032ab23335cb5a09c4937d7962205f5962f79`.

Task `requests_6589`, base `7a13c041dbef42f9f3feb14110f02626f6892e9a`, Issue SHA256 `60b61eb2b26e1135174dd59ddc4e29b2d7fe2b5e255b723e9085b36407663d04`, snapshot SHA256 `053f2ea73cb7b604f535ee2eabe596dae9df9d7ff54a365d62b4ff0bebab7115`. Package B SHA256 `9a8566523e4463889a6e8f61d7cb7e760fd48873ea9827e529b29c5abca6fa80`. Official evaluator swegemma0.2.11 source SHA256 `99e2a5fdab2be2b5e0388de29080da9d6e7003cf8b53299cda790464f4ecd2aa`; unchanged.

Original CPU02 archive: `cpu02-output/egrd-v02-cpu-hardening02.zip`, SHA256 `25b2a360c62023c48617fe8c3bb8734d4230a2d3668eccc33cb4e22f20fcf25a`. Raw records: `cpu02-evidence/worker/trusted/NATIVE_RESULT.json`, `native-junit-0.xml`, `NATIVE_COMMANDS.json`; Agent/Native cleanup receipts and original session/done hashes retained. Full191 failure/error case identities, trace hashes and excerpts: `native-recovery/AUTOPSY.json`.

Commands/timestamps/exit codes: `native-recovery/REGRESSION_EXECUTIONS.json`, `FOLLOWUP_EXECUTIONS.json` and referenced logs. Actual prior Native pytest command is recorded verbatim in AUTOPSY.json; exit1. Prior worker stage exit0 did not imply trustworthy test execution. New CPU SaveKernel0, GPU SaveKernel0, Gemma requests0, packages installed0. Local tests validate classification/source evidence; they do not replace Native evaluation. New Linux service acceptance and Native revalidation are NOT_RUN.
