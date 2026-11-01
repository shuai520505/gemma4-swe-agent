# R12 GPU RUN_02 — new authorization and accepted dispatch

The human explicitly authorized GPU use after compact CPU readiness. This new receipt authorizes one frozen nine-session R12 batch: exactly four NVIDIA L4, 18000 seconds, no retry, no formal submission. The consumed RUN_01 receipt is not reused.

The CPU-validated template SHA256 is eedaa333b3b2d757903c5628a4d4b7274aee7eaad030646f6f92001dfaab8658. This authorized Notebook changes only the receipt's embedded bytes/digest and cell ID; all other Notebook/runtime/experimental configuration bytes are preserved. Authorized Notebook SHA256: 9ff7c59ce3a98f918ab7ebbaea5d2d880d4ed4f3df3dfd11474633dae843626e. File/code/CLI-source sizes: 47522 / 46983 / 47446 bytes. The dispatcher additionally preserves passthrough for non-SaveKernel reads; one-shot/no-retry behavior is unchanged.

Live quota at admission: available108000 seconds, used=0, reserved=0, frozen floor73200. Exactly one SaveKernel request was accepted (HTTP200), Notebook version1. Acceptance/queueing is not proof of allocation or Session completion. Actual four-L4/CUDA evidence, full model hashes and original trust/resource gates remain required inside the Notebook before inference. No change to candidates, task identities, order, tools, model, sampling or budgets.

This directory preserves this execution's receipt, exact upload source, durable request claim and dispatch evidence independently of the earlier disabled READY package and RUN_01 failure evidence. CPU allocation-validation inputs in AUTHORIZED_PACKAGE_CHECK are unit-only, not real GPU observations. Results will be recovered from this existing Notebook; no second dispatch.
