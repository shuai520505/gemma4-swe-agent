# Actual Kaggle device gate: PASS

New execution: **141087018/v1 COMPLETE**, private, CPU-only. Before SDK installation
or S0 initialization, `device_gate.run` calls the unchanged PR39
`egrd.v031.device_runtime.install_null_device` in an isolated temporary root.
`DEVICE_RESULT.json` is the safe direct result; its original bytes and the exact
implementation are preserved in the verified private archive.

Observed using the real Kaggle kernel:

| Check | Result |
|---|---|
| `os.mknod` | Succeeded |
| `lstat` node type | Character device, not regular and not symlink |
| Device number | Major 1, minor 3 |
| Mode | 0666 |
| Host writes / reads | Write accepted, subsequent read EOF |
| Non-root child | UID/GID dropped; reads/writes succeed, exit 0 |
| Temporary device/root | Removed |
| Fallback | None |

Every subsequently initialized Agent/trusted chroot also checks its actual node
and `GIT_CONFIG_GLOBAL=/dev/null` under the confined execution UID. It writes an
invalid-config sentinel into the genuine device and observes no retained bytes;
ordinary `git config --global --list` succeeds. It does not replace Git commands,
edit their environment, introduce an empty-file fallback or relax confinement.

Offline negative tests cover denied mknod, unexpected regular results, symlinks,
wrong device number, missing parent, partial initialization and cleanup failure.
Those OS fixtures remain explicitly **simulated**; they did not establish Kaggle
capability. The observed new run establishes this environment's capability only,
not a guarantee for every future Kaggle image, UID policy or container profile.

PR39's specific contaminating write was not captured and remains unknown. The
verified source defect was a regular null file plus Git's null-config path. A
new local synthetic Git test independently confirms that malformed regular-file
config is rejected. This is not an explanation of historical leaderboard scores.
