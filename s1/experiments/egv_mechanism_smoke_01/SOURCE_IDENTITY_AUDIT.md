# Supplemental source/base audit

The preselected snapshot SHA is `39db9ef995f8066b5f3cc70a7d8c54325e7bdc4faa9599e76099b533a4e034c0`; the metadata base is `f1d750fddad90e2faad6c3cc5c85c7687b787e89`. Both remained fixed and were checked by the original CPU/GPU execution path.

A local read-only inspection of archived Git metadata found HEAD on main at b51861d3f9fafa4d49ddb6aa30429f37b8d24221, and no object for f1d750fd…. This cannot by itself establish whether working-tree bytes match the requested base: task archives can have different Git index/object history and working-tree content. The finding and missing-object evidence are preserved in snapshot_git_identity.json / snapshot_git_structure.json. No archive or Agent workspace was changed.

GitHub Tree API returned403 (rate limit); status and response digest are preserved in snapshot_base_source_audit.json. The three critical files (__init__, applications, routing) were compared against raw.githubusercontent.com at the **exact registered base**, all matching. A subsequent package sweep compared all48 snapshot `fastapi/**/*.py` files plus pyproject.toml. Round01 matched47 of49, with two transport errors, not mismatches. Round02 retried only those two read-only downloads; both matched. Together: **49/49 exact-base source/config SHA matches**.

These are pre-repair upstream files, not a reference repair or evaluator solution. The requests happened on the local audit host, not inside either Kaggle Agent environment, and no downloaded content was supplied to either Agent. The current and baseline critical source hashes are also captured by original Linux import/JUnit audits.

Limits: this does not prove that every docs/test/script file or Git history matches the metadata base, nor repair the absent Git object. Task input identity is the registered full archive SHA. Package/config byte consistency is independently established; no production-package drift was found. Historical Git labels and failed retrievals are retained rather than rewritten to imply a cleaner provenance record.
