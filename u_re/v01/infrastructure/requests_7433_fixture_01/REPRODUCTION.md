# Reproduction and artifact map

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

Task base `0b401c76b6e80a4eecf3c690085b2553f6e261ca`, snapshot SHA `96292b6471c5f428feedcbf65a013c234ac9e2a0ced8b802d7450720ba9d22f3`, Issue SHA `2753a02000cf17c5258bc23b9a91257403e57b34dcd934adbe3956b0523444db`, test overlay SHA `8286a1547ba1bf923a0d5c7feb50104f1f353c705b4b773b28a55bf2ea4b3da4`. Exact complete task record hash is task_identity.json. No reference repair is read/applied. Preserve raw archive `c92e03b706c109d9be7b05fcb00dccc1751d138a83b1592420781cfeccbb429e` and its internal manifest/CRC verification. assess.py is an offline report reader, never an online scoring classifier; reproduce the assessment with `python -m u_re.v01.infrastructure.requests_7433_fixture_01.assess <PRESERVED_VALIDATION_DIRECTORY> <NEW_JSON_FILE>`.
