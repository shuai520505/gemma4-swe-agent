# CPU-validated research runtime surface

The sealed paired trial exposed missing python/pytest/pip/which/touch entrypoints.
RED Notebook v1 reproduced eight failures in each of three task dependency groups.
GREEN v2 used the exact same contract: all 24 probes passed, including executable
pytest fixtures, parametrization and writable temporary directories. Original
Issue target failures and positive controls remained unchanged in fresh sandboxes;
trusted-check protection, non-root UID policy and cleanup passed.

`runtime_surface.repair(root)` is for a newly created research chroot. It stages
only an explicit pinned-image pytest/pip dependency closure, skips .pth/bytecode
and external executable paths, preserves existing task distributions and hashes
copied files. It restores static entrypoints and two ordinary system commands.
Packages remain read-only; the existing child confinement and PIP_NO_INDEX policy
are retained. Existing xarray packaging 24.2 is reused rather than upgraded.

For a subsequent research study, call repair immediately after the inherited
manager.start() in a separately named adapter; preserve its required native
SubprocessManager dispatch name and clean up on startup failure. See
issue_regression.py for the CPU-tested adapter pattern. Run contract.run(out,
repair) and issue_regression.run(other_out, repair) with authorized original inputs.

This is not a change to competition tools, the official scorer or the original
six Agent sessions. Full project dependency closure and test suites are not
established. No new model session, algorithm gain or leaderboard score is claimed.
