# Trusted development evaluation boundary

development_evaluator.py is a research adapter, not a replacement for the official
Native Verifier. Both official_native_resolved and canonical_swebench_resolved
remain null. A passing scoped check is not full repair correctness.

It restores the same byte-verified Django base, checks the original full source
identity (excluding only synthetic .git metadata), applies a submitted patch with
git apply --check/apply inside a separate unprivileged chroot and records the
tested source identity. The original PR38 probe and common.py are copied with
their exact bytes into a root-owned readonly evaluation directory. The Dataset
and host paths are not mounted. The current Agent session is already terminated.

The original probe records form validity, ordinary ModelForm persistence and the
creation-form relation discrepancy. A separate owned bounded regression checks
ordinary user persistence and password verification/rejection. This regression is
not a canonical benchmark test and does not cover the full custom-user/model/input
matrix. Neither check was derived from a reference repair or hidden evaluator.

After checks, the adapter records actual return codes, structured target receipt,
regression output, exceptions, source freshness, probe byte integrity and cleanup.
A confined write attempt must fail against the readonly trusted probe. All roots
and owned processes are cleaned up through the accepted UID-lease manager.
No post-evaluation source/test content is returned to the running Agent.

For the CPU fixture only, both Agents submit an inert comment in a production
file. Its Python AST is unchanged. Patch applicability and relevant execution are
tested, while the original defect is expected to remain. This is deliberately
not a scripted repair or an algorithmic positive result. Production behavior is
recorded false for this reviewed fixture; arbitrary future patches require review.

The evaluator cannot infer semantic correctness from assert counts or a green
result. Issue relevance, causal hypotheses, production behavioral changes and
complete correctness require independent review. It does not automatically call
a patch correct, select revisions, overwrite tests, or supply repair advice.
As with any Python test process, code under test can affect process state; readonly
files and separate confinement prevent host/active-Agent access but do not prove
resistance to every deliberately test-cheating implementation. Patch review and
trusted test-integrity checks remain necessary.
