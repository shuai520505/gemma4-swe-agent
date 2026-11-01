# CPU infrastructure hardening after the R2/A pilot

This is a prospective host-infrastructure repair, not another candidate or a repair-capability experiment. Frozen R2/A packages, the earlier GPU Notebook, all eight real sessions and their semantic outcomes remain read-only. No GPU job, model inference or formal competition submission is part of this change.

## Root causes

1. The official subprocess path intentionally skips Docker's editable installation. Source imports worked, but no source-project `sphinx-build` entrypoint was installed. The old CPU admission checked Python trusted tests, not the Issue's CLI affordance.
2. Inherited locale variables named a locale absent inside the minimal chroot. Sphinx CLI startup calls `locale.setlocale(LC_ALL, '')`, which failed before building documentation.
3. The coordinator examined final Agent errors and independent verifier receipts. Ordinary `run_command` error returns were embedded in ADK function responses and never participated in infrastructure classification. A successful independent test run therefore masked the earlier environment failure.

`LEGACY_REGRESSION_FAILURE.txt` records two expected red regressions against the actual frozen classifier, using original session6 responses. Both returned CONTINUE. It is not an Agent outcome or a changed historical verdict.

## Minimal opt-in implementation

- `hardened_runtime.py` subclasses the existing manager and durable context. The manager keeps the literal SubprocessManager name required by the unmodified SDK. It supplies a wrapper outside the task source that invokes `sphinx.cmd.build.main` from `/workspace`; it does not install a different Sphinx package. All task commands use portable `LC_ALL=C`, `LANG=C` and Python UTF-8 mode.
- Before `start_agent_session`, after source/dependency/baseline preparation, admission checks non-root locale activation, source provenance, `sphinx-build --version` and an unrelated minimal HTML build. This is setup overhead, outside the per-Agent clock; it must be included in future whole-experiment budgets.
- `stop_policy.py` inspects structured failed run_command stderr for the observed locale failure, missing required Sphinx CLI and an explicit list of pinned missing dependencies. It does not search read_file contents or equate every nonzero command with infrastructure failure. Expected bug reproductions, AssertionError, agent-created syntax errors, unknown user imports and mistakenly invoking write_file as a shell program remain ordinary failures.
- A durable latch records the first recognized error. The context persists the original ADK event, writes the stop receipt and raises before the next completion can be requested. Already dispatched parallel tools cannot be retroactively undone; this is not a claim of cancellation at every instruction boundary.
- `hardened_worker.py` composes the unchanged worker and binds the live stop receipt into its result. `hardened_coordinator.py` composes the unchanged coordinator. Missing/malformed coverage receipts and latched failures stop before legacy ordinary-patch exceptions can allow continuation. All existing cleanup/evidence/native-control rules remain delegated to the original admission function.

These are opt-in host adapters. They are not embedded into frozen Agent ZIPs or retroactively applied to historical results. A future independently frozen runner can select hardened_coordinator/hardened_worker and place this directory before the prior study, extension and shared-source paths on PYTHONPATH. This directory contains no GPU dispatcher or experiment selection protocol.

## Verification and boundaries

Local tests distinguish the two original failures from ordinary failures and verify sticky stop/fail-closed receipt behavior. The Linux integration uses the pinned official SDK, actual non-root chroot and source CLI, with a localhost scripted endpoint only. Its deliberate failures are fixtures; they are not real model reasoning, task repairs or new scores.

The ordinary-error control must reach a second actual scripted completion/tool, then a fixture-only context terminates it. The infrastructure fixtures must stop after one completion; a deliberately removed CLI during preflight must stop with zero completions. The coordinator composition probe intercepts only the GPU-owning parent entry; it does not start a model server. Final results and exact scope are recorded separately after recovery.

CPU attempt1 is retained as blocked: its original control repeatedly requested an empty submit_patch and exhausted80 turns. The corrected control terminates after observing a continuation marker. This was a test-driver defect, not proof of a guard pass. No real Gemma or GPU was involved in either CPU diagnostic.

This explicitly covers the reproduced faults and declared dependency patterns, not all possible environment faults. Optional/unknown imports can reflect the requested software defect; broad automatic classification would wrongly stop legitimate repair work. New fault classes require evidence and regression cases. The prior pilot remains inconclusive; a CPU infrastructure pass cannot promote A, create R3 or establish hidden-task performance.
