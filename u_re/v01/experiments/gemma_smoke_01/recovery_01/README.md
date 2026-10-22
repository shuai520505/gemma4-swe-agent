# Corrected CPU acceptance and kernel tool boundary

This additive recovery preserves PR17 CPU01 ERROR and UNKNOWN_STOP. CPU02 repeats the corrected official Compiler/ADK acceptance and independently probes real tool filesystem confinement using owned synthetic canaries. It runs no competition task, real model or GPU.

The boundary uses Linux Landlock ABI >=3, a separate unprivileged UID, no capabilities, seccomp restrictions, closed inherited descriptors and a restricted environment. It is applied at native tool process creation, including native diff/submit/fallback commands. The official commands, tools and candidate remain unchanged. Trusted evaluator/model processes remain outside the tool boundary. It is not a VM or a defense against kernel exploits. Unsupported kernels or failed setup are blockers, never a boolean override.

CPU02 permits one durable SaveKernel dispatch to wudangdexiaodoashi/gemma4-u-re-smoke01-cpu02, CPU only, Internet/GPU/TPU false. Uncertain response stops without retry. Raw results remain outside the public checkout. Local tests are not official CPU results.

The first undispatched build contained an invalid nested Python string; retained under preparation_failures/unexecuted_build_v00. It was corrected before any request. No previous execution evidence was altered.

GPU remains NOT_AUTHORIZED. The subsequent user request also authorizes pursuing one formal score, conditional on acceptance, candidate/rule and whole-run budget gates; it does not turn CPU results into GPU algorithm evidence.
