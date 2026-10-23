# U-RE V0.4 Evidence-Guided Repair

Status: **V04_EGR_CPU_READY** (engineering only). No real V04 Gemma, GPU Notebook or formal Submission was authorized or executed.

Starting point: actual open/unmerged PR28 `cc432feb8de585bd976fa3e0b676365e60b18603`; branch `feat/u-re-v04-evidence-guided-repair`. The first preparation commit `8ef16bd` was frozen before the CPU SaveKernel. The exact packaged runtime has not changed after its CPU acceptance.

- `FAILURE_MECHANISM_ANALYSIS.md` / `TRACE_BEHAVIOR_METRICS.json`: all315 actual tool actions in12 historical GPU sessions, three raw archive SHA pins, conservative evidence grades/limits; detailed source/model/tool contents remain private.
- `candidate_egr_v04/`, `submission_egr_v04.zip`, `build.py`: standard official three-member submission candidate; only the strategy block changes. `PROMPT_EXACT.diff`, build manifest and Prompt lock explain the change.
- `worker.py`, `session.py`, `notebook.py`, `payload.zip`: reuse accepted production Compiler/ADK/Runner/Verifier/chroot and durable CPU dispatch/readonly collector. New worker only passively checks actual compiled Prompt/generation/tool schemas; no new decision controller. CPU transport is external to the production ZIP.
- `cpu-e2e01/`: one durable CPU dispatch, original UNKNOWN_STOP preserved, independent readonly identity/source/version reconciliation. Notebook140405959/v1 is COMPLETE.
- `CPU_END_TO_END_ACCEPTANCE.json`, `audit.py`: source-byte/version-bound actual output verification; both owned scripted Agent runs execute all6 tools,207-byte source patch,explicit submit,native resolved=true,JUnit1passed and complete cleanup.14 scripted HTTP requests;0 Gemma.
- `GPU_REPLICATION_PROTOCOL.json`: prospective independent confirmation,seed17,two tasks/four ABBA runs proposed;five remaining conservative metadata candidates,all NOT_ADMITTED. No GPU authorization or final selected task identities.
- `release.py`, `INTEGRITY_MANIFEST.json`: old tracked-file/ZIP preservation, accepted payload-to-working-source comparison, raw archive CRC/SHA and publication checks.

## Reproduction

From repository root (do not repeat a dispatch):

```powershell
python -m u_re.v04.experiments.evidence_guided_repair_01.build
python -m u_re.v04.experiments.evidence_guided_repair_01.traces
python -m unittest u_re.v04.experiments.evidence_guided_repair_01.test_local -v
python -m u_re.v04.experiments.evidence_guided_repair_01.release
```

The build is deterministic; acceptance requires the already downloaded private raw CPU archive and historical trace analysis requires the three pinned private historical ZIPs. No model or task code from a downloaded archive is executed by the offline auditors. Payload and protocol constructors deliberately refuse overwriting existing frozen artifacts. A future execution change requires a new payload and CPU acceptance, not editing a PASS flag.

`CANDIDATE_BUILD_MANIFEST.json:CPU_acceptance=NOT_RUN` is the immutable pre-execution build fact; the separate final acceptance derives the later result from raw bytes. The inherited `ABBA_EXPERIMENT_LOCK.json`/`ADMISSION_RECONCILIATION.json` bind only two development-task baseline environment rechecks used by the reused CPU coordinator. They are not the prospective GPU sample; that sample remains unselected in the new GPU protocol.

No reference/gold patch, private evaluator assertion, historical repair, or reasoning trajectory is supplied to the new Agent. The owned scripted repair is solely an engineering fixture. Original NoEGV,Full andAction-First bytes and historical UNKNOWN/ERROR results remain unchanged. PR27 Batch2 HTTP499 remains UNKNOWN.
