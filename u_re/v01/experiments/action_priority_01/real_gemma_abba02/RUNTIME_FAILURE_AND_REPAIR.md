# Runtime failure and targeted repair

GPU02 140233779/v1 allocated four L4 devices. The declared source-pin closure was complete and all registered bytes were later verified against the archived executed source. The failure was a different closure: the transitive repository imports reachable from the actual runtime entrypoint.

`real_gemma_abba01/session.py:37`, inside `native_baseline`, lazily imports `fastapi_pilot_01.screen.source_hashes/provenance`. That module was not in the payload. Its import occurs before baseline workspace creation, before vLLM startup, and before all Agent runs. The captured ModuleNotFoundError and zero completed runs therefore describe an environment packaging failure. They provide no evidence against either candidate.

The prior CPU acceptance ran declared pin checks, Compiler checks and a boundary canary. It did not enter `native_baseline` or the production worker. Reusing that test as sufficient GPU startup coverage was a validation gap.

The repair traverses Import/ImportFrom statements throughout each entrypoint AST, including function bodies and relative imports, and records every local dependency edge and file hash. It adds the missing screen helper and its local experiments.prepare dependency with package initialization files. This is not a claim to statically resolve arbitrary dynamic imports; actual CPU entrypoint execution complements it.

The independent CPU repair is broader than a single-file presence assertion: two exact frozen native baseline entrypoints plus the unchanged production worker on an owned synthetic task. Only its local HTTP model boundary is scripted. Its output must establish source edit, patch, native TaskResult/JUnit, terminal HTTP lifecycle and cleanup before declaring that CPU path passed. It cannot establish Gemma behavior, vLLM startup, GPU usage, or algorithm performance.

No historical candidate, Runner/Verifier implementation, task selection or budget is changed. GPU01 and GPU02 executed Notebook bytes and failure/UNKNOWN events remain intact. The repaired CPU payload is not a substitute GPU retry: a further GPU attempt requires a separate explicit authorization and a fresh frozen build.
