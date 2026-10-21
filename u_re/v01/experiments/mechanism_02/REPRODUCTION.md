# Reproduction and evidence limits

Start at PR10 base794e5fc. Selection commit ac20c47 freezes SELECTION_PROTOCOL.json,select.py,the entire metadata pool,exclusion ledger,rank and screen.py. Hashes in protocol and Git bind the algorithm before any CPU attempt. Frozen CPU-only build commit98efddb contains Notebook,payload registration and guarded host launcher. Do not regenerate an immutable build from a later working tree containing new report files: use the saved self-contained Notebook or checkout the build commit in an isolated worktree. A new build/run must have a new identity,not overwrite old artifacts.

Local reproducible checks:

```powershell
python -m unittest u_re.v01.experiments.mechanism_02.tests.test_policy u_re.v01.experiments.mechanism_02.tests.test_readiness -v
```

These are Windows policy/integrity/readiness checks,not official native task runs or Gemma results. The blocked GPU stub can be run locally: it exits nonzero with NOT_AUTHORIZED before imports or external work. No GPU Notebook is emitted by any build script in this directory.

The CPU Notebook's first cell verifies embedded source and pinned approved wheel hashes,installs nothing from the network,then its second cell installs only the approved pinned runtime wheels and would run `python -m u_re.v01.experiments.mechanism_02.screen <new-empty-output>`. This requires official Linux inputs/runtime and never constructs an Agent. It uses real verify_task with original snapshot/test overlay and empty Agent Patch,retains JUnit before stop and source/provenance/cleanup records. Pytest stage classification is the inherited structured path,not an independent idealized substitute. max8,known-Requests-block rejection,all-pass rejection,unknown-global-stop and same-repo skip are source-frozen.

Actual execution in this delivery stopped at Kaggle SDK authentication import before owner listing/SAVE_INTENT/SaveKernel. AUTH_AVAILABILITY.json records initial auth failure and one distinct cached-source attempt; credentials are not logged. No accepted Notebook version/status/result exists; source existence and requested7200s CPU window do not mean the platform accepted it. No baseline output is reconstructed or replaced with Mock data. The local environment has no official swegemma/adk-submission and no Docker executable; no Windows substitute was used.

Independent metadata check: RANKED_POOL.json has50 entries and exactlyone repository. All other supplied repositories are conservatively excluded by existing histories/reservations; no criterion was relaxed after observing this. Restoring auth alone cannot produce a valid different-repository pair. A further change to exclusions/pool must be independently justified and versioned without rewriting this blocked study.

Historical scope: REMOTE_HEADS.json lists actual PR1–10 heads. EXCLUSION_LEDGER_V02.json stores730 inspected relevant unique Git blobs,per-ID source indices and all28 inherited source pins. Four old source paths were actually ignored local archives; evidence/HISTORICAL_ARTIFACT_RESOLUTION.json records exact expected/actual SHA and original paths. Remaining raw ignored archives are not claimed retrievable through Git. The prior failed audit source attempt is retained; correction occurred before ac20c47 and before any new baseline. No answer/Trace/stdout/repair content is used in task ranking. Unknown reference/model history remains UNKNOWN; model pretraining/unrecorded work cannot be excluded.

The report-schema KeyError during finalization was a host reporting bug,not a native task run; its source/correction is retained. It changed no candidate,selection rule,CPU payload or result. Final selected identities remain empty,all50 task results not_run,with unassessed quantities null. INTEGRITY_MANIFEST.json and HISTORY_AUDIT.json provide final byte audit.

Final seal check (no external requests):

```powershell
python -m u_re.v01.experiments.mechanism_02.seal
```

The manifest excludes itself and caches. It includes the seal source and raw evidence, verifies all5699 inherited file bytes and both ZIP member pins. Creation is exclusive; verification refuses drift rather than rewriting the seal. The directory .gitattributes preserves raw bytes on checkout.
