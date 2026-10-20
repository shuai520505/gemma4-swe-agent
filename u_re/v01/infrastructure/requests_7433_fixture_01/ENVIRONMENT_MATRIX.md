# Environment and outcome matrix

| Case | Environment/config | Observed result | Interpretation |
|---|---|---|---|
| Historical CPU03 native | Frozen original task + evaluator overlay, pinned image, pytest8.4.2 |142 passed,1 skipped,1 xfailed,195 setup errors |Original immutable block, replay only |
| A fresh native CPU01 | Same hashes and literal native command; only random JUnit path differs |Same142/1/1/195, exit1; JUnit339 |Independent reproduction, ENVIRONMENT_BLOCKED |
| Diagnostic registration | Same sandbox after native returns; passive observer + original selected test |One local definition per name; normal wrapper raises FixtureLookupError |Diagnostic only, cannot replace native result |
| Explicit real provider import | Same sandbox; -p pytest_httpbin.plugin |ModuleNotFoundError; exit1 |Provider absent, not merely unloaded |
| Approved dependency source | pip --dry-run --no-index, both approved caches |No matching pytest-httpbin==2.1.0; exit1 |No installation, no compatible artifact available |
| B synthetic missing provider | Isolated toy repo, autoload disabled, no provider path |2 setup errors |Expected negative control |
| B synthetic explicit provider | Same toy; -p toy_provider with sentinel strings |2 passed |Legal same-name wrapping |
| B synthetic automatic provider | Same toy; synthetic pytest11 metadata visible, autoload enabled |2 passed |Entry-point discovery works |
| B synthetic autoload disabled | Same visible toy entry point, autoload disabled |2 setup errors |Shows a distinct unloaded-provider mechanism |
| C candidate environment repair |No approved required artifact exists |NOT_RUN |No external download/injection, no fake provider |

The four toy controls ran independently on local Python3.11.9/pytest9.0.3 and pinned Linux Python3.12.13/pytest8.4.2. They are semantic controls, not Requests repair tests. A passing toy is not RESEARCH_ONLY_ENV_FIX.

Actual baseline dependencies: pytest8.4.2,pluggy1.6.0,swegemma0.2.11,adk-submission0.2.13; pytest-httpbin/httpbin/trustme absent. Installed pytest11 metadata: anyio4.13.0,typeguard4.5.1,langsmith0.7.34. Anyio blocked by native command; typeguard and langsmith loaded. Full order, configuration, sys.path, package origins, wheel SHA/entry points and native stdout/stderr are in ASSESSMENT.json and results/cpu01/validation. All raw errors and ordinary passes are retained.
