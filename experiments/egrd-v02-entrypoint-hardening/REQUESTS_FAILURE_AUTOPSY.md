# Requests failure autopsy

Status: BLOCKED_INFRASTRUCTURE. The complete CPU02 archive passes CRC and recorded SHA checks. All324 JUnit cases were inspected, including every error and ordinary failure tag.

| Group | Count | Confirmed cause | Original evidence | Compliant action |
|---|---:|---|---|---|
| HTTP fixture resolution |183|Requests tests/conftest.py:25 defines httpbin(httpbin), but no upstream fixture definition resolves; available fixtures show the wrapper only|Every matching raw JUnit error chain; AUTOPSY records each case/index/trace SHA|An approved registered provider and its dependencies would be necessary; none supplied in the59 actual wheels|
| HTTPS fixture resolution |4|tests/conftest.py:30 defines httpbin_secure(httpbin_secure), with the same missing upstream provider class|All4 distinct secure-fixture chains|Same provider prerequisite; no TLS startup occurred|
| Network confinement, encoded as failure |4|Socket creation itself raises EACCES before connect; urllib3 wraps it as NewConnectionError and Requests ConnectionError instead of the expected ConnectTimeout|test_connect_timeout[timeout0/1], test_total_timeout_connect[timeout0/1]; socket.py:232 and urllib3/util/connection.py:64|Existing confinement cannot support these unchanged tests; do not suppress or reinterpret them as repair failure|

There are at least two independent capability defects: provider resolution and real network capability. The187 errors share a fixture-provider failure mechanism; the other4 failures are independently observed network denial. Installing a provider alone cannot establish acceptance.

The locked source requires pytest-httpbin==2.0.0, httpbin~=0.10.0 and trustme. Supplied wheels contain pytest8.4.2 but no pytest-httpbin or httpbin. The installed distribution version was not directly probed in CPU02, so it remains UNKNOWN; absence of a registered usable provider is confirmed. Repository dev requirements constrain pytest<=6.2.5; compatibility with8.4.2 is an additional UNVERIFIED risk, not the observed cause of all errors. Official subprocess setup skips install_test_dependencies for the manager class; this adapter depends on its explicitly supplied wheel set. No automatic dependency provisioning repaired that omission.

Read-only [PyPI2.0.0 release metadata](https://pypi.org/pypi/pytest-httpbin/2.0.0/json) and SHA-verified released source were audited without installing or importing it. The plugin registers both fixtures via pytest11, starts WSGI servers on127.0.0.1 with port0 by default, and uses a thread with context-manager shutdown/join. SecureServer uses bundled certificate/key material and SSLContext. Provenance: PROVIDER_SOURCE_PROVENANCE.json. Actual HTTP/HTTPS startup, bind conflict, TLS handshake, CA validation and fixture-thread teardown remain NOT_RUN because fixture resolution failed first.

The inherited launcher constructs a clean environment: no host HTTP_PROXY/HTTPS_PROXY/ALL_PROXY/NO_PROXY values are inherited. Native uses the same launcher and exact59-wheel list as Agent. The shared source prefix is /workspace/src:/workspace:/opt/approved; Agent import receipt and Native src/requests trace confirm source binding. Full cross-workspace byte-fingerprint parity was not captured and is UNKNOWN. Native before/after source guard is unchanged.

Policy and runtime corroborate each other: inherited seccomp denies connect and AF_INET/AF_INET6 socket creation; the actual CPU02 isolation probe reports NETWORK_DENIED, and all4 failure traces show AF_INET SOCK_STREAM construction rejected with errno13. DNS, proxies, certificate expiration and port collision are not established causes of the187 setup failures. Numeric10.255.255.1 timeout cases cannot acquire their required socket behavior under the current policy.

## Evidence identity and execution boundary

Generated UTC: 2026-11-03T15:07:52.529834+00:00. Audited PR46 source commit: `9ef032ab23335cb5a09c4937d7962205f5962f79`.

Task `requests_6589`, base `7a13c041dbef42f9f3feb14110f02626f6892e9a`, Issue SHA256 `60b61eb2b26e1135174dd59ddc4e29b2d7fe2b5e255b723e9085b36407663d04`, snapshot SHA256 `053f2ea73cb7b604f535ee2eabe596dae9df9d7ff54a365d62b4ff0bebab7115`. Package B SHA256 `9a8566523e4463889a6e8f61d7cb7e760fd48873ea9827e529b29c5abca6fa80`. Official evaluator swegemma0.2.11 source SHA256 `99e2a5fdab2be2b5e0388de29080da9d6e7003cf8b53299cda790464f4ecd2aa`; unchanged.

Original CPU02 archive: `cpu02-output/egrd-v02-cpu-hardening02.zip`, SHA256 `25b2a360c62023c48617fe8c3bb8734d4230a2d3668eccc33cb4e22f20fcf25a`. Raw records: `cpu02-evidence/worker/trusted/NATIVE_RESULT.json`, `native-junit-0.xml`, `NATIVE_COMMANDS.json`; Agent/Native cleanup receipts and original session/done hashes retained. Full191 failure/error case identities, trace hashes and excerpts: `native-recovery/AUTOPSY.json`.

Commands/timestamps/exit codes: `native-recovery/REGRESSION_EXECUTIONS.json`, `FOLLOWUP_EXECUTIONS.json` and referenced logs. Actual prior Native pytest command is recorded verbatim in AUTOPSY.json; exit1. Prior worker stage exit0 did not imply trustworthy test execution. New CPU SaveKernel0, GPU SaveKernel0, Gemma requests0, packages installed0. Local tests validate classification/source evidence; they do not replace Native evaluation. New Linux service acceptance and Native revalidation are NOT_RUN.
