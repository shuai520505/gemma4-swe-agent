# Requests fixture failure: confirmed call chain and unresolved boundary

**Root cause confirmed in the pinned CPU/subprocess research environment;
fixture dependency recovery is not complete.** No replacement fixtures, test
edits or reference repair were used. Requests is blocked as a repair-rate
endpoint until its dependency/provider admission genuinely passes.

## Independent clean-snapshot evidence

Diagnostic r01 uses the original `requests_7328.tgz`, no Agent Patch and no
evaluation test patch. SHA remains
`47f35331fd2dc1d976eeb2aeff5f8aa376cd005911bf35ce164161931a97d8c9`.
Unmodified `test_no_content_length[GET]` fails during fixture setup with the
same recursive-httpbin signature as the historical GPU Phase2.

After fixing editable source import, CPU r03 executes the original public
`tests/test_requests.py` under the native Phase2 command semantics and gets
**142 passed, 1 skipped, 1 xfailed, 193 errors**: 189 httpbin and four
httpbin_secure recursive-dependency errors. The historical Phase2 had 194
errors and included the evaluation test patch; these are different test sets,
not a claim that the clean run reproduced every original case one for one.

Production/test Python bytes remain unchanged (33 files checked). The Task's
declared baseline is `cbce031327be4f1b4b5fd041ff4dcaa8efa2ce53`. The curated archive
retains Git HEAD `7dea5aec68f3c6448eda1a5a6153155baeec82ad`; it was not reset to
force equality. Three critical file blobs are verified against GitHub's actual
contents API at the declared baseline:

| File | Git blob SHA-1 |
|---|---|
| pyproject.toml | 8b77f737f59f572ec1f34117f73f76ac15489dc3 |
| src/requests/sessions.py | 578cc44d5c17a81982c28308b6396760ab9d5946 |
| tests/conftest.py | 530a4c2a5f9917d62ffed2e2eecfdb8164655740 |

This confirms the files relevant to this investigation, not full upstream Git
graph equivalence. Actual source authority remains the pinned official archive.
See [baseline dependency declaration](https://github.com/psf/requests/blob/cbce031327be4f1b4b5fd041ff4dcaa8efa2ce53/pyproject.toml)
and [baseline fixture wrappers](https://github.com/psf/requests/blob/cbce031327be4f1b4b5fd041ff4dcaa8efa2ce53/tests/conftest.py).

## Actual failing lookup

`tests/conftest.py:25` declares `httpbin(httpbin)`; line 30 declares
`httpbin_secure(httpbin_secure)`. These wrappers depend on a same-name fixture
provided at an outer/plugin level.

The read-only CPU diagnostic plugin records the actual Pytest lookup stack:
`pytest_runtest_setup → Function.setup → _fillfixtures → getfixturevalue →
FixtureRequest._get_active_fixturedef → FixtureDef.execute →
SubRequest._get_active_fixturedef`. The top request and subrequest each see
exactly **one** httpbin definition, the local wrapper at conftest.py:25.
Resolving its own argument has no outer definition and raises
`FixtureLookupError`; the diagnostic renders recursive dependency. This occurs
while resolving parameters, before the wrapper body or Requests repair logic.

Evidence: `results/r03/validation/clean_requests/fixture_callchain.jsonl` and
`fixture_callchain.json`; r01 also preserves the original conftest, complete
Pytest plugin trace and setup output. The tracing plugin defines no fixtures
and preserves original results/exceptions.

## Why the provider is absent

The snapshot's dependency group declares `pytest-httpbin==2.1.0`,
`httpbin~=0.10.0`, trustme and other test packages. In the pinned research host:

- Pytest is 8.4.2. Active pytest11 entry points include anyio, typeguard and
  langsmith; pytest-httpbin has no entry point/distribution/module.
- Module admission finds pytest_httpbin/httpbin/trustme absent.
- All 124 official task wheels were inventoried and SHA-audited. They contain
  multiple Pytest versions but no pytest-httpbin/httpbin/trustme wheels.
- A sandbox-local `pip --dry-run --no-index --find-links=<official task wheels>
  pytest-httpbin==2.1.0` fails resolution. No external provider was downloaded
  or substituted to change the outcome.

Actual official swegemma 0.2.11 code explains the research-path difference:
`install_editable_package` and `install_test_dependencies` return immediately
for literal SubprocessManager/SubprocessSandbox classes. Consequently the
normal Docker setup/dependency path is not invoked. The inherited sandbox
venv exposes host site-packages, where these providers are absent. This is a
confirmed missing provider in this research configuration, not evidence that
the inaccessible official scoring container has the same installed packages.

The available official `/sandbox/setup.py` is preserved in r05, SHA-256
`0263995ade90f83c8efa0ab5c7c9b7629696f39bc75274d58fc27ab774568409`.
Its slow path installs only available wheel names, and its fast path injects
paths and rewrites pytest discovery configuration. It provides no missing
httpbin fixture implementation. It was inspected, not executed: no test/config
rewrite or network-capable editable fallback is introduced by this investigation.
Official wheel files and scoring logic remain unchanged.

## Source import repair and remaining blocks

Before the research editable adapter, actual imports resolve to
`/usr/local/lib/python3.12/dist-packages/requests/`. After isolated
`python3 -m pip install --no-index --no-build-isolation --no-deps -e /workspace`,
sys.path includes workspace/src and both Requests modules resolve there.
Passive module-execution evidence confirms this path. Fixture errors persist
afterward, demonstrating that import provenance and provider installation are
separate problems. Path correctness alone is not behavioral correctness.

CPU r03 initially blocked both newly selected tasks at missing build backends
(`poetry`/`pdm`). Inspection then found their declared backends in the official
wheel cache. The r05 adapter installs only requirement-compatible cached wheels,
with SHA checks, before editable installation. Rich `rich_3278` now passes
workspace import, original `tests/test_ansi.py`, and sandbox cleanup. FastAPI
`fastapi_14361` imports its workspace source but remains blocked because the
official Task's target test file set is not present in the clean baseline.
Those tests may be introduced by the evaluator patch; that is not verified by
this baseline-only check. No evaluation patch was applied to make readiness
pass, no replacement task was selected, and no GPU run was started.

To reopen Requests eligibility, supply the repository-declared providers
from an approved, versioned source, hash them, verify sandbox-only installation,
then rerun original fixture/setup and provenance checks. An alternative source
admission for already-correct flat layouts also needs independent CPU validation.
Neither source nor fixture outcome may be fixed by changing tests, suppressing
errors or attributing an environment failure to the Agent.

Final distinction: the **observation and Requests source-import issues are
repaired**; the **official-input-compatible fixture/provider environment remains
blocked**; **E1/E3/E4 algorithm gains remain unproven**. No complete repair rate
or leaderboard improvement is derived from these CPU runs.
