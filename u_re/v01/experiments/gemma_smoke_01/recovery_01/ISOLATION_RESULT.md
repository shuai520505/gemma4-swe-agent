# Kernel boundary: FAIL CLOSED

Kaggle CPU02 returned OSError errno38 (ENOSYS) to Linux x86_64 landlock_create_ruleset(version query). See cpu02/derived_results/kernel_isolation_error.json. This demonstrates that the registered Landlock implementation is unavailable on this actual deployment. It does not distinguish a missing kernel feature from syscall filtering/emulation. No unsupported-kernel fallback was used.

The actual canary, symlink/traversal, descendant, memory, networking and positive tool tests were NOT_RUN: capability probing intentionally stopped first. Local7tests validate source/ABI/failure paths only; they do not prove an access-denial boundary. No isolation_verified=true is accepted. Code is retained but not promoted as passing execution code.

Design: unchanged official tool commands are launched through a clean helper,UID65534/no capabilities,Landlock RO runtime + RWworkspace/tmp,write-only audit sinks,closed fds,sanitized env and seccomp. Trusted Verifier and model host stay separate. This is intended data-access isolation, not a VM/kernel exploit defense. All restrictions must be exercised before any real Gemma on this research deployment.

Minimal recovery condition: a deployment exposing Landlock ABI>=3 with the required UID separation, or a separately reviewed supported container/mount filesystem boundary. The latter must pass actual canary read/write/path traversal/child/fd/process and ordinary six-tool/submit tests; no boolean substitution or fake provider. Do not launch another GPU merely to probe it. GPU Smoke remains blocked by integrity until a supported boundary is demonstrated. Official competition submission is a declarative three-file Agent ZIP using organizer tools/sandbox; this research-only adapter is not in that ZIP.

Primary API reference: https://docs.kernel.org/userspace-api/landlock.html and https://docs.kernel.org/userspace-api/seccomp_filter.html .
