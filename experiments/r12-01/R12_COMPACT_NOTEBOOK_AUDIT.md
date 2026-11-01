# R12 compact Notebook audit — Recovery V0.2

Gate: **R12_REDISPATCH_READY**. Packaging and actual CPU-mounted native entry validation PASS. This is not GPU dispatch authorization.

## Exact bytes and CLI source

New RUN_02 Notebook: 46330 UTF-8 file bytes; code cells 45791 bytes; Kaggle 2.2.2 `kernels_push` JSON reserialization 46254 bytes. All are strictly below 1,048,576 and 100,000. SHA256: `eedaa333b3b2d757903c5628a4d4b7274aee7eaad030646f6f92001dfaab8658`.

JSON/Python compilation PASS. Installed CLI implementation was inspected: `code_file` selects `study.ipynb`, reads that file and clears outputs/joins source lists before `json.dumps`; the upload representation was measured locally without calling SaveKernel. The guard checks all three sizes before authentication or any write. Only five small metadata/helper files are base64 embedded; largest decoded file 11348 bytes; no embedded ZIP/source archive. No Codex-local C:/D: path occurs in Notebook code.

## Packaging repairs

Copied, never overwrote, the 40,831-byte historical compact alternative. Replaced consumed RUN_01 receipt with RUN_02 `explicit_user_GPU_authorization=false`; moved the new working root and cleanup confinement assertion to `/kaggle/working/gemma-r12-authorized-gpu-02`. Authorization is checked before creating that root or probing any GPU. The actual new Notebook cell and dispatcher were executed locally and rejected before subprocess/GPU/Kaggle code. The dispatcher also refuses an uncleared dependency gate. New title/id normalize consistently: `R12 Authorized GPU Run 02` / `wudangdexiaodoashi/r12-authorized-gpu-run-02`.

Retained private, Internet-off, NvidiaL4, TPU-off metadata, pinned image, competition and model-v2 sources. Source extraction uses the unique hash-pinned mounted CPU output; wheelhouse selection now requires uniqueness rather than relying on a fragile directory-name substring. PYTHONPATH is extension + extracted source; no Internet install is used. Existing offline INSTALL remains unchanged. An exhausted outer time window now stops rather than replacing it with a one-second run.

## Dependency closure and path validation

| Resource | Evidence this turn | Result |
|---|---|---|
| Runtime/source carrier | Fixed CPU output archive SHA/CRC, 251 registered source files, 14 extension/overlay hashes | PASS |
| Dispatch ZIP | Nested archive SHA/CRC, actual extraction | PASS |
| Candidates | All three frozen ZIP hashes, four members each | PASS |
| Tasks/Issues/checks | Actual unchanged materialize and trusted_binding function bodies; local filesystem mapping only; nine bindings, snapshot/wheel/check hashes | PASS |
| Task extras | R12_INPUTS manifest plus all 23 local source/wheel hashes | PASS |
| Official wheelhouse | Current listing plus actual CPU mount: all 41 frozen wheel hashes match | PASS |
| Model v2 | Actual CPU mount: all eight frozen file SHA values match, no model load | PASS |
| New default-deny bootstrap | Actual Notebook cell and dispatcher reject; standard library imports resolve | PASS |
| Full native compact entry | Actual Kaggle Linux CPU mount: 13 native imports and three official SDK compilations | PASS |

Mount resolution uses `/kaggle/input/**` with exact filenames, SHA checks and a unique source/wheelhouse selector; it does not assume the private dataset directory prefix. Production task paths from the old CPU root are rebound under the new execution root by unchanged `materialize()`. The local Windows Path adapter was used only to test that function, not to replace native SDK imports. It is not a Linux end-to-end execution.

## Read-only resource observation

UTC 2026-10-31T04:56:33.962322+00:00: private egrd dataset v2 READY (47 files), R12 inputs v1 READY (24 files), source-carrier Notebook COMPLETE, model v2 eight filenames, official SDK 41 filenames. Metadata is not proof of file bytes or real mounts. Quota: total 108000.0, used 0.0, reserved 0.0, available 108000.0 seconds; frozen floor 73200. This snapshot is not future dispatch admission or four-L4 capacity evidence.

## Failure tests and preserved history

21 CPU guard/admission tests PASS, plus two explicitly labeled CPU mocks rejecting three L4 / four T4. Oversize, metadata errors, missing resource, bad candidate/model hash, low quota, >5h and consumed/absent authorization stop. Ordinary no-patch/timeout/tool-argument/incorrect-patch cases continue; backend/context, missing evidence, cleanup, protected-check and positive-control failures stop. No selective reruns. No original Issue reproduction or nine-session simulation was rerun.

All 23 historical RUN_01 files were hashed before/after and unchanged, including failed Notebook, authorization, HTTP400, request/claim, timestamps and quota. Original blocked Manifest byte SHA remains `90593990ea2bacba29e94ab0941063f1d2e31063b6235739c744192fdc8739d2`. No one-time READY manifest was created. RUN_02 GPU SaveKernel requests=0, GPU sessions=0, model requests=0. Separately authorized CPU validation SaveKernel requests=1.

## Actual Kaggle CPU validation closes the local verification gap

After the user explicitly permitted Kaggle CLI Notebook validation, one private CPU-only/Internet-off Notebook v1 was dispatched. Its source is 84,048 bytes. Actual result PASS: 13 native modules imported, all 41 official wheel hashes matched, three frozen candidates compiled through the official SDK, all nine bindings materialized with real Kaggle paths, all eight mounted model files matched frozen SHA values without loading weights. CUDA device count=0. The exact GPU Notebook bytes `eedaa333b3b2d757903c5628a4d4b7274aee7eaad030646f6f92001dfaab8658` and actual default-deny dispatcher were tested and rejected before any GPU/service/Kaggle write. No Issue reproduction or nine-session replay ran.

CPU output archive SHA256 `c220aeb8867c458c3f9e2035b92c9c940edd4f21ca654630de3816304dc8bf10`; CRC PASS; the downloaded target Notebook is byte-identical to the local GPU artifact. `CPU_COMPACT_ENTRY_RESULT.json` records actual mounts and import/hash results. The local UNKNOWN rows above are retained as earlier observations and superseded by this returned CPU evidence. RUN_02 BUILD alone is promoted to REDISPATCH_READY; the original RESOURCE_BLOCKED manifest is unchanged.

The original one-shot GPU receipt remains consumed. New GPU receipt and new explicit human authorization are still absent; both Notebook and dispatcher deny execution. CPU SaveKernel=1, GPU SaveKernel=0 this recovery. Real exactly-four-L4 capacity is still unverified and is a future runtime gate. No non-GPU packaging blocker remains.

Post-validation quota snapshot: available 108000 seconds, used=0, reserved=0 at 2026-10-31T05:14:03.039129+00:00. This does not authorize a GPU request.
