# Partial actual isolation evidence; two-arm gate not passed

The private Dataset is mounted only on the trusted Notebook host. Agent commands
run through the accepted helper's non-root UID, chroot, dropped capabilities,
no-new-privileges, seccomp and closed inherited descriptors. No dataset, host
filesystem or proc mount is introduced. Only the original base source and three
exact task dependency wheels are staged inside its filesystem. Neither arm gets
a receipt/probe file in its workspace. B's intended supplement is task context only.

Actual V2 A events show:

- Official read_file and write_file calls targeting the real host probe path are
  rejected with path-traversal errors.
- A real run_command asserts /kaggle/input, /kaggle/working, /proc, /evaluation and
  a trusted-evidence path are absent, and tests a dangling workspace symlink to
  the host input. Its stdout contains AGENT_FILESYSTEM_ISOLATION_PASS.
- The trusted original probe bytes remain unchanged. A root/file-cleanup audit
  confirms the Agent and trusted baseline UID roots were removed after V2.

The trusted baseline uses a different chroot with no active Agent. Its evaluation
directory is root-owned/readonly; an actual write attempt under the execution UID
raises PermissionError. Original probe/common/regression hashes stay intact.
Native Runner/tool code is unchanged; no new tool or global callback is registered.

Limits: B never runs, post-edit trusted evaluation never starts, and the required
full model-boundary input capture is missing. The overall isolation acceptance
is **PARTIAL**, not PASS for both arms. Root confinement is not proof that every
malicious Python implementation cannot influence its own test process.

Native Runner preparation also creates/updates its ordinary root pytest.ini and
conftest.py before its clean baseline commit. This shared behavior is from the
pinned Runner, not an Agent repair or a rewritten trusted diagnostic. The trusted
base probe is run on the original full source hash, outside those artifacts.
Its source hash matches PR38 exactly. Synthetic Git metadata needed for Runner
diffs changes Django's displayed development version; it does not change source
file bytes. Both differences remain explicit research-adapter fidelity limits.
