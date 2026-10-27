# Both-arm isolation and owned cleanup: PASS

All evidence here comes from 141087018/v1, not PR39's partial run.

A and B each initialize independent native Runner contexts, clean extracted source
trees, journals, UID leases, chroot roots, loopback servers and patches. The raw
registry has distinct session/root identities. Sequential UID reuse is possible
only after prior owned processes and leases are removed; it is not reused state.
Initial B history contains no A tool results or edits.

Agent confinement is inherited unchanged: non-root UID/GID, chroot, dropped
capabilities, no-new-privileges, seccomp, closed inherited descriptors, no host
dataset/proc mounts. Both actual official read/write attempts targeting the host
probe are rejected. Both child commands assert host/data/evaluation paths absent
and test a dangling workspace symlink to the host input. These are actual negative
access tests, not instruction-based isolation claims.

Trusted baseline and each post-edit evaluation run in separate chroots after the
Agent has stopped. Original probe/common/regression bytes are root-owned readonly;
actual write attempts under the child UID fail. Dataset/probe hashes match the
original frozen identities. Source before/after tests is version-bound and stable.
No evaluation observations are fed back to the terminated Agent.

Native process wrappers wait/reap and `kill_owned` verifies no live process under
the reserved UID remains. Actual cleanup records remove the owned roots. The new
recovery wrapper removes token-matched UID leases after process cleanup, including
partial initialization paths. All Agent and trusted roots/leases, device-gate
root and HTTP threads are cleaned in the new run. Evidence files, flat snapshot
and journals are intentionally archived rather than treated as runtime residues.

Offline failure tests verify that foreign/escaping roots cannot be removed, a
failed process cleanup does not falsely delete the lease, and transport shutdown
still happens if manager cleanup raises. These fault-injection cases are local
fixtures; the successful live CPU run did not deliberately fail its cleanup.

Limits: readonly files/chroot do not prove resistance to all malicious in-process
Python test cheating. The comment-only fixture is AST-reviewed. Arbitrary future
repairs need review. This is a development evaluator, not a canonical benchmark
or replacement Native Verifier. PR39's old incomplete cleanup evidence is retained
as incomplete; it is not retroactively relabeled by this new success.
