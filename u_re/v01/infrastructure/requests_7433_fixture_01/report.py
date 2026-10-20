"""Finalize a separate, evidence-backed diagnostic report without historical writes."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def write(name,value):
    raw=value if isinstance(value,bytes) else value.encode() if isinstance(value,str) else (json.dumps(value,indent=2)+'\n').encode()
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as out:out.write(raw)


def main():
    a=json.loads((HERE/'ASSESSMENT.json').read_text())
    assert a['root_cause_proven_in_research_environment']
    assert a['native_command_equal_except_random_junit_path'] and not a['observer_in_native_command']
    assert a['source_test_configuration_unchanged'] and a['cleanup_complete']
    old=json.loads((HERE/'evidence/INITIAL_HISTORY.json').read_text())
    mismatches=[p for p,h in old['files'].items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    assert not mismatches,mismatches
    zip_pins={'noegv':'2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608',
              'full':'887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821'}
    for arm,h in zip_pins.items():assert hashlib.sha256((ROOT/f'u_re/v01/submission_{arm}.zip').read_bytes()).hexdigest()==h
    write('HISTORY_AUDIT.json',dict(base=old['base'],inherited_files_checked=len(old['files']),mismatches=mismatches,
                                 only_new_namespace_expected='u_re/v01/infrastructure/requests_7433_fixture_01/',candidate_zip_sha256=zip_pins,
                                 original_CPU02_110_result_and_CPU03_failure_unchanged=True))
    # Only two generated comment lines; reconstruct from captured official code
    # and prove it matches the actual root-conftest hash, not a guessed fixture.
    root_conftest=b'# Hermetic test discovery hook for SWE-gemma\n\n'
    hierarchy=json.loads((HERE/'results/cpu01/validation/diagnostics/conftest_hierarchy.json').read_text())
    expected=next(x['sha256'] for x in hierarchy if x['path']=='conftest.py')
    assert hashlib.sha256(root_conftest).hexdigest()==expected
    write('evidence/root_conftest_reconstruction.txt',root_conftest)
    write('evidence/root_conftest_reconstruction.json',dict(sha256=expected,method='Two-line literal reconstruction from captured native configure_test_discovery source; matches actual root-file hash',contains_fixtures=False))
    build=json.loads((HERE/'registrations/cpu01_build.json').read_text())
    archive=json.loads((HERE/'results/cpu01/COLLECTION.json').read_text())
    identity=a['task_identity']
    write('ROOT_CAUSE.md',f'''# Requests 7433 fixture root cause

**Confirmed in the pinned official-Linux research subprocess environment: the required outer fixture provider is absent, not merely installed but disabled. Outcome: ENVIRONMENT_BLOCKED.** This does not establish the package state of Kaggle's inaccessible private scoring container. No Issue repair or Agent/model execution occurred.

## Evidence chain

One new CPU-only Notebook, `wudangdexiaodoashi/gemma4-u-re-requests-fixture-cpu01`, version1, kernel139838876, completed. Python3.12.13, pytest8.4.2, pluggy1.6.0, swegemma0.2.11, adk-submission0.2.13. Image is the same frozen CPU03 image. GPU/TPU/internet are false and model_sources is empty. Notebook SHA: `{build['notebook_sha256']}`; payload SHA: `{build['payload_sha256']}`. Raw archive SHA: `{archive['raw_archive_sha256']}`. All {archive['manifest_verified_files']} internal manifest entries and ZIP CRC verified.

The unchanged native verify_task path, empty Agent patch and exact evaluator test overlay reproduce **142 passed,1 skipped,1 xfailed,195 errors**, native exit1, official baseline resolved=false retained verbatim. JUnit has339 cases,0 failures,195 error nodes and2 skipped entries (one represents xfail). Every error is a recursive fixture setup error:191 httpbin and4 httpbin_secure. None is a normal assertion regression or collection/internal error. This is not an Agent repair failure. Native files are under results/cpu01/validation/native_baseline; their command equals CPU03 except the normal random JUnit filename. No observer is in that command.

`tests/test_requests.py:124` requests httpbin. At `tests/conftest.py:34`, local function-scoped httpbin(httpbin) wraps the expected server object with prepare_url. At line39 the secure wrapper does the same. The collected fixture definition chain contains **exactly one definition each**, both local to tests/conftest.py, with baseid=tests. No outer/plugin definition exists. The separately labelled passive probe records `_fillfixtures → getfixturevalue → _get_active_fixturedef → FixtureDef.execute → SubRequest._get_active_fixturedef → FixtureLookupError`, preserving the actual exception. `_pytest.fixtures.py:596–611` permits same-name overrides, moves from index-1 to index-2 for the wrapper dependency, then fails because the list length is1. Its rendering calls this recursive dependency. This is resolution exhaustion before the wrapper body or relevant Requests behavior, not evidence of infinite Requests execution. Normal httpbin lookup has a full observed stack; secure absence is supported separately by its collected definition and four native JUnit setup traces.

There are only root conftest.py and tests/conftest.py in the recorded hierarchy. The root file hash exactly matches the native helper's two comment lines and defines no provider; its reconstruction and provenance are recorded separately. Active discovery config, pyproject, tox and test configuration are preserved in diagnostics/configuration. The original test dependency group declares pytest-httpbin==2.1.0, httpbin~=0.10.0 and trustme. No pytest_plugins declaration supplies an alternative provider.

## Why it is missing

Current sandbox inventory finds no distribution or module for pytest-httpbin/httpbin/trustme. pytest11 metadata includes anyio,typeguard,langsmith only. PYTEST_DISABLE_PLUGIN_AUTOLOAD, PYTEST_PLUGINS and PYTEST_ADDOPTS are unset. Actual plugin registration loads typeguard and langsmith; anyio is explicitly blocked by the unchanged native -p no:anyio. Thus plugin discovery is operational and there is no installed httpbin entry point for it to discover. Explicit `-p pytest_httpbin.plugin` fails with ModuleNotFoundError: pytest_httpbin. This disproves the explanation that merely removing an autoload-disable flag or explicitly naming an already-installed plugin would fix this environment.

Both approved caches are completely inventoried, including embedded wheel entry-point metadata:124 task wheels and41 official Wheelhouse wheels. No pytest-httpbin/httpbin/trustme provider wheel/module is present. Sandbox-local pip **dry-run** with --no-index and both --find-links paths fails: no matching distribution for pytest-httpbin==2.1.0. No external dependency was downloaded or installed into execution. Static host-side PyPI metadata and maintainer source were excluded from the payload.

Captured official container_setup.py:512–513 and529–530 returns early for SubprocessManager/SubprocessSandbox editable/test-dependency setup. The pre-existing research adapter separately installs the workspace editable with --no-deps for provenance, not the project's test dependency group. The inherited host lacks this test provider and the approved offline inputs cannot supply it. This is the confirmed research-path environment boundary. The available official sandbox/setup.py was inspected only, hash0263995ade90f83c8efa0ab5c7c9b7629696f39bc75274d58fc27ab774568409; it is not invoked to rewrite configuration or alter the scoring path.

## Provider identity and semantics

Maintainer [v2.1.0 pyproject](https://github.com/kevin1024/pytest-httpbin/blob/v2.1.0/pyproject.toml) declares pytest11 entry point httpbin = pytest_httpbin.plugin; [the plugin](https://github.com/kevin1024/pytest-httpbin/blob/v2.1.0/pytest_httpbin/plugin.py) defines both session-scoped server fixtures using the httpbin application. The local module and distribution are absent, so these are the **intended**, not actual loaded, providers. Raw static source receipts and PyPI release metadata hashes are saved under evidence; they were never installed/executed or uploaded as a provider. Pytest [override documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html#overriding-fixtures-on-various-levels) and captured installed source explain why legal same-name wrappers need an outer definition.

Four isolated synthetic studies with sentinel strings, outside Requests, agree on Windows Python3.11/pytest9.0.3 and pinned Linux Python3.12/pytest8.4.2: missing provider→2 setup errors; explicit provider→2 passes; pytest11 autoload provider→2 passes; autoload disabled→2 setup errors. These controls demonstrate name resolution only. They neither provide HTTP behavior nor constitute a Requests workaround. No pytest version regression is needed to explain the observed missing-provider failure; compatibility of the real absent provider remains untested.

## Historical comparison and limits

Read-only requests_7328 r05 has the same one-wrapper/no-provider chain, absent module/entrypoint/cache and failed offline resolution, with193 errors on its different unpatched original public test set. Historical GPU194, current195 and old CPU193 are not interchangeable outcomes. No prior compliant provider repair was demonstrated. Current independent reproduction adds current task/plugin/cache/lookup evidence rather than treating historical hypotheses as proof.

All {a['files_checked']} measured source/test/config bytes match before native execution, after it and after diagnostics. Native JUnit was captured before cleanup; no sandbox directories remain. The native helper's own normal setup-generated discovery files are preserved; no research patch was made to original tests/config or verifier. Existing import observer records real requests and requests.sessions execution from workspace/src. Its coarse outside_workspace verdict also includes external requests.packages aliases to installed urllib3; that raw verdict is retained, not silently converted into a behavior PASS.

Unresolved: real-provider/Flask/Werkzeug/TLS compatibility after an approved provider becomes available; private scoring-container contents; complete Requests discriminating baseline after environment recovery. Trustme absence is secondary, not an explanation substituted for the191+4 recursive errors. None of these unknowns justifies a fixture stub, external installation, test exclusion or task replacement. No repair candidate was applied; Outcome A/B is not claimed.
''')
    write('ENVIRONMENT_MATRIX.md', '''# Environment and outcome matrix

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
''')
    write('REPRODUCTION.md',f'''# Reproduction and artifact map

Frozen implementation commit before execution:10ed97fe00aac56111b54dcce8a299ad3d21f576; parent PR9 cd7fe8e19950003b59819c7accf7292ce2e151b9. All new work is below this directory. Run commands from the repository root.

## Existing evidence, no compute rerun

```powershell
python -m u_re.v01.infrastructure.requests_7433_fixture_01.cpu_host observe
python -m unittest u_re.v01.infrastructure.requests_7433_fixture_01.tests.test_safety -v
```

Read registrations/cpu01_build.json and results/cpu01/SAVE_REQUEST.json/SAVE_RESPONSE.json. Saved Notebook is [CPU-only Notebook](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-u-re-requests-fixture-cpu01), versionNumber=1 in the authoritative API receipt. enableGpu=false, enableTpu=false, enableInternet=false, modelSources=[]; request timeout3600. The host's preexistence-query/PowerShell sequencing exception is preserved in evidence/CPU_LAUNCH_SEQUENCE_NOTE.md. SaveKernel was sent once and returned version1; do not repeat it.

## Repeat the synthetic mechanism locally

```powershell
python -m u_re.v01.infrastructure.requests_7433_fixture_01.minimal <NEW_EMPTY_OUTPUT_DIRECTORY>
```

Uses the current interpreter's installed pytest, prints its version, records all four commands/environment/JUnit/stdout/stderr. It does not need network, Requests, HTTP service or model. A new output path is mandatory. It defines synthetic providers only outside the official workspace.

## Repeat official Linux diagnostics in a separately authorized CPU replica

The frozen Notebook is self-contained: source is embedded in its payload and hash-checked before execution. Mount the same competition inputs and metric/gemma-4-developer-agent-wheelhouse, pin the identical image, CPU only and offline. Execute both saved cells as-is in a **new** evidence namespace; do not overwrite this version/output. The first cell creates runtime_paths.json from actual mount discovery, verifies all pinned official/task wheel hashes, then the second installs only cached pinned runtime wheels and runs:

```bash
python -m u_re.v01.infrastructure.requests_7433_fixture_01.diagnose <NEW_EMPTY_OUTPUT_DIRECTORY>
```

This command requires the Notebook's verified source/pinned installed runtime and runtime_paths.json; a generic Windows Python is not an official-Linux substitute. Do not invoke repeated launch commands in this delivery. New compute needs a new immutable build/version and preserves this first run. prepare.py refuses differing existing build artifacts rather than overwriting them.

diagnose.py calls the real verify_task with empty Agent patch, original snapshot, base overlay if applicable and original test overlay. The native command in native_baseline/phase2_command.json is unchanged from CPU03 except random JUnit path. Read raw execution output, TaskResult and JUnit **before** labelled diagnostics. The after-native diagnostic executor bypasses only the research Phase2 writer so independent probes cannot overwrite native evidence; it does not replace any official verifier result.

Inspect environment.json, plugin_trace.json, fixture_lookup.jsonl, explicit_provider_import.json and offline_provider_resolution.json under validation/diagnostics. Captured official _pytest.fixtures.py:596–611 explains the failing lookup index. minimal/result.json contains all four real Linux subprocess outcomes. cleanup.json confirms no remaining sandbox.

Task base `{identity['base_commit']}`, snapshot SHA `{next(iter(identity['input_files'].values()))}`, Issue SHA `{identity['issue_sha256']}`, test overlay SHA `{identity['test_patch_sha256']}`. Exact complete task record hash is task_identity.json. No reference repair is read/applied. Preserve raw archive `{archive['raw_archive_sha256']}` and its internal manifest/CRC verification. assess.py is an offline report reader, never an online scoring classifier; reproduce the assessment with `python -m u_re.v01.infrastructure.requests_7433_fixture_01.assess <PRESERVED_VALIDATION_DIRECTORY> <NEW_JSON_FILE>`.
''')
    write('ADMISSION_RESULT.md', '''# Admission disposition — ENVIRONMENT_BLOCKED

**Outcome C: ENVIRONMENT_BLOCKED. Official baseline NO-GO.** The missing provider is now directly established, but no approved offline artifact can restore it. Neither OFFICIAL_BASELINE_GO nor RESEARCH_ONLY_ENV_FIX is claimed. A toy provider was never used in Requests.

The original U-RE-V01-MECHANISM-01 draft remains DRAFT_BASELINE_BLOCKED. This is a supplement, not an edit to its historical protocol or CPU03 record. Keep fastapi_14458 NoEGV→Full and requests_7433 Full→NoEGV. FastAPI was not rerun. Candidate Prompt, ZIP, model,300s/60 tools/120s,one Agent and six tools are unchanged. CPU02's110/110 remains immutable compatibility evidence, not GPU algorithm evidence.

| Question | Conclusion and evidence |
|---|---|
| Q1 recursion root cause |High-confidence research-environment fact: only the local wrappers exist, and the real provider is absent; fresh native JUnit plus diagnostic lookup, metadata, import and wheel resolution all agree. ROOT_CAUSE.md/ASSESSMENT.json |
| Q2 actual provider |No outer provider actually loaded. Intended pytest-httpbin2.1.0, pytest_httpbin.plugin, pytest11:httpbin, with both session-scoped server fixtures; maintainer source receipts and sandbox environment.json |
| Q3 failure domain |Research subprocess test-dependency environment, before relevant Requests behavior; no demonstrated pytest version defect or Requests production bug. Private scoring container unexamined |
| Q4 minimal reproduction |Yes,4 synthetic cases on each of local pytest9.0.3 and pinned Linux8.4.2; original tests unchanged; minimal/result.json |
| Q5 legal repair path |Not available from current approved inputs.124 task+41 official wheels contain no provider; offline dry-run fails. Candidate environment fix NOT_RUN |
| Q6 unchanged native revalidation |Original blocked baseline rerun through native verify_task and same command. No repaired baseline exists, so cannot claim recovery validation |
| Q7 remaining counts |142 passed,0 assertion failures,195 setup errors,0 collection errors,1 skipped+1 xfailed (2 JUnit skipped nodes),native exit1 |
| Q8 history and identities |All inherited file hashes and both ZIPs match; task/snapshot/Issue/base/overlay match CPU03;43 source/test/config files unchanged during native+diagnostics; HISTORY_AUDIT.json |
| Q9 draft advancement |No. DRAFT_BASELINE_BLOCKED stays in effect; old protocol unmodified |
| Q10 request GPU execution now |No. First obtain approved versioned provider/dependency inputs, prove a clean unchanged native baseline and discriminating tests. Separately require GPU quota,4×L4,model/request identity,Notebook/window,cleanup,final preregistration and explicit execution authorization |

Next external condition: a competition-approved, hash-pinned offline provider/dependency bundle or an official supported test environment demonstrably supplying the declared real providers. After source admission, verify actual HTTP/TLS fixture behavior and all unchanged native tests; missing packages could conceal further compatibility issues. A setup-error-free baseline may retain genuine Issue assertion failures. Do not change selected tasks, spoof fixtures, install unapproved network dependencies or modify native scoring logic to bypass this condition.

No GPU, Gemma inference, training or leaderboard Submission occurred. Formal S0 remains historical0.13; this environment diagnosis produces no repair-rate or leaderboard result.
''')
    write('README.md','''# Requests fixture diagnostic 01

Start with ROOT_CAUSE.md and ADMISSION_RESULT.md. Outcome ENVIRONMENT_BLOCKED: root cause confirmed in the pinned research environment, approved dependency recovery unavailable. No GPU/Agent/model or formal submission. ENVIRONMENT_MATRIX.md and REPRODUCTION.md describe actual native and isolated synthetic runs. ASSESSMENT.json mechanically binds conclusions to raw files. History and both U-RE candidates remain unchanged.

One CPU-only Notebook version1 completed; results/cpu01/raw.zip retains complete source and original output. Native baseline and post-native diagnostic outputs are distinct. No provider was injected into original tests. Static maintainer/PyPI sources are receipts, not runtime dependencies. The host preexistence-query sequencing exception is separately retained; it did not create a second version.
''')
    print('Reports generated. Run safety tests, then seal INTEGRITY_MANIFEST.json.')


if __name__=='__main__':main()
