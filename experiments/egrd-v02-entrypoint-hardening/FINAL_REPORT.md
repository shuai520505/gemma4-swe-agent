# EGRD V0.2 Native environment recovery

**Final status: BLOCKED_INFRASTRUCTURE.** Full autopsy is complete. There is no compliant environment repair under the current approved dependency set and unchanged socket confinement. No new Kaggle run, GPU or real model execution was performed.

## Required decisions

1. **183 httpbin errors:** OBSERVED recursive fixture resolution at Requests tests/conftest.py:25; the upstream plugin fixture is not available to pytest. Required provider2.0.0 is absent from the actual59 supplied wheels. Installed-distribution version beyond that inventory is UNKNOWN.
2. **4 httpbin_secure errors:** OBSERVED same missing upstream-provider mechanism at line30, before TLS initialization. A certificate defect is not established.
3. **One or multiple issues?** The187 setup errors share a provider-resolution cause. Additionally all4 ordinary failure tags are confirmed AF_INET creation EACCES, an independent security/runtime incompatibility, not repair failures. Potential pytest8.4.2 versus repo<=6.2.5 compatibility remains UNVERIFIED.
4. **Environment changes:** None. No package install, fixture replacement, network relaxation, service, prompt/model change or scoring change. Only research trust classification and executed-case accounting were strengthened.
5. **Official source binding:** OBSERVED /workspace/src import in Agent and matching Native source traceback/command; source guard unchanged during verification. Full pre-patch cross-workspace byte parity is UNKNOWN, not fabricated.
6. **All fixtures executed?** NO. Provider resolution failed; HTTP/HTTPS service lifecycle and TLS are NOT_RUN.
7. **Zero infrastructure errors?** NO. Original JUnit contains187 setup errors plus4 failed bodies caused by network confinement.
8. **Independent trust passed?** NO. Original hashes/cleanup pass, but execution integrity fails. The original CPU02 PASS receipt is preserved as historical plumbing evidence only.
9. **300 protected hashes unchanged?** YES, exact before/after comparison; CPU01/02 archive hashes and CRC are unchanged.
10. **Eligible for authorized12B smoke?** NO. Native infrastructure acceptance is still blocked, and this task forbids GPU dispatch.

## Engineering result

Real network-denial failures previously could look like ordinary assertion failures once fixture errors were removed. A failing regression using all4 original failure records demonstrated that gap; the strengthened guard now rejects them. Executed-body accounting is corrected from322 to135:131 pass bodies plus4 failed bodies, excluding187 setup errors and2 skip/xfail records. Official raw resolved remains false.

Existing CPU regressions and actual Compiler checks were rerun; see REQUESTS_REGRESSION_REPORT and exact command receipts. New17 checks are forensic/classifier tests, not fabricated positive HTTP/HTTPS acceptance. The old final report is preserved byte-for-byte under native-recovery/previous/.

## Exact blocker and next decision

An approved provider/dependency closure and a permitted isolated runtime capable of genuine HTTP/HTTPS sockets and the unchanged timeout tests are required. Current seccomp denies socket creation itself. Installing a package alone would not fix that. No compliant solution is claimed, and no restriction is weakened. Further Linux dispatch should wait for a separately approved runtime/dependency solution, rather than repeat a known-broken run or change the official suite.

## Evidence identity and execution boundary

Generated UTC: 2026-11-03T15:07:52.529834+00:00. Audited PR46 source commit: `9ef032ab23335cb5a09c4937d7962205f5962f79`.

Task `requests_6589`, base `7a13c041dbef42f9f3feb14110f02626f6892e9a`, Issue SHA256 `60b61eb2b26e1135174dd59ddc4e29b2d7fe2b5e255b723e9085b36407663d04`, snapshot SHA256 `053f2ea73cb7b604f535ee2eabe596dae9df9d7ff54a365d62b4ff0bebab7115`. Package B SHA256 `9a8566523e4463889a6e8f61d7cb7e760fd48873ea9827e529b29c5abca6fa80`. Official evaluator swegemma0.2.11 source SHA256 `99e2a5fdab2be2b5e0388de29080da9d6e7003cf8b53299cda790464f4ecd2aa`; unchanged.

Original CPU02 archive: `cpu02-output/egrd-v02-cpu-hardening02.zip`, SHA256 `25b2a360c62023c48617fe8c3bb8734d4230a2d3668eccc33cb4e22f20fcf25a`. Raw records: `cpu02-evidence/worker/trusted/NATIVE_RESULT.json`, `native-junit-0.xml`, `NATIVE_COMMANDS.json`; Agent/Native cleanup receipts and original session/done hashes retained. Full191 failure/error case identities, trace hashes and excerpts: `native-recovery/AUTOPSY.json`.

Commands/timestamps/exit codes: `native-recovery/REGRESSION_EXECUTIONS.json`, `FOLLOWUP_EXECUTIONS.json` and referenced logs. Actual prior Native pytest command is recorded verbatim in AUTOPSY.json; exit1. Prior worker stage exit0 did not imply trustworthy test execution. New CPU SaveKernel0, GPU SaveKernel0, Gemma requests0, packages installed0. Local tests validate classification/source evidence; they do not replace Native evaluation. New Linux service acceptance and Native revalidation are NOT_RUN.
