# V02b observed dependency recovery

Base: open/unmerged PR25, `6f6b7500baa007ee317466b93329ce99cf58950e`.
This is a new prospective study. PR25's mixed-error STOP and all older evidence
remain unchanged. No reference/gold patch was read.

## What was missing

The approved 41 official and 124 task wheels did not contain inline-snapshot.
The research subprocess prepares a limited offline environment rather than
installing the complete upstream test dependency set. Actual original sandbox
interpreter metadata and tracebacks in recovery01 confirm missing
`inline_snapshot`; this is independent of the feature under repair.

The current instruction permits verified fixed public wheels for CPU research.
Three universal wheels are fixed in NEW_DEPENDENCIES.json: inline-snapshot0.21.1,
asttokens3.0.0 and executing2.2.0. Existing pytest8.4.2 and rich13.9.4 satisfy the
mandatory requirements; no optional extras are selected. Actual recursive
mandatory dependency/version/code-file fingerprints cover 21 distributions.
Python3.12.13, Pydantic2.12.3 and the official dependency versions remain fixed.
The trusted Notebook installs only those three SHA-verified files using
`pip --no-index --no-deps --force-reinstall`; no task-specific dependency changes
are made during screening. Wheels and original licenses come from fixed PyPI
releases. This research extension does not prove that extra wheels are present
or permitted to alter the official Competition scoring environment.

## Actual original/recovered comparison

Recovery01 `140344081/v1 ERROR` preserved the original failures, installed the
three packages and executed the first recovered baseline. Its research parser
then rejected pytest's duplicate snapshot teardown records. Recovery02
`140348261/v1 COMPLETE` reused the explicitly identified original observations,
repeated the fixed install and owned positive/negative snapshot controls, and
completed the recovered baselines. Neither original tests nor native Verifier
logic changed. ENVIRONMENT_RECOVERY.json binds both raw archives and identities.

Actual original sandbox metadata also records asttokens3.0.1 and missing
executing. Recovery deliberately pins asttokens3.0.0 (a version change, not a
claim that asttokens was originally absent), executing2.2.0 and inline0.21.1.
Both asttokens versions satisfy inline's >=2.0.5 constraint; all subsequent
checks use the same newly frozen3.0.0 environment. Original asttokens metadata
remains in the private INTERPRETER.json records.

* fastapi_14246: original two inline_snapshot collection errors disappear.
  Recovered native result is still negative: 15 unique tests, 2 call failures,
  2 paired snapshot-finalizer errors, 17 XML testcase records. All raw errors
  remain recorded. The newly frozen research reader recognizes only exact
  assertion/finalizer pairs with verified plugin code and matching aggregates.
  It cannot hide unrelated fixtures or malformed XML. This diagnostic task is
  not selected as a new prospective sample.
* fastapi_14609: original missing-inline error disappears; an import of
  `PydanticV1NotSupportedError` from the original workspace still fails.
  The original exceptions module lacks that definition, and its SHA is the
  same before/after dependency recovery. Pydantic remains2.12.3. The Issue asks
  for rejection of pydantic.v1 with an error, but does not spell this exact
  exception API. The test/API relationship supports a target-related failure,
  not a missing external Pydantic distribution; classification remains
  CONDITIONAL_TARGET_FAILURE, never formal admission in this study.
* fastapi_5077: recovered native baseline still has one discriminating behavior
  failure and zero errors. It is the predeclared carry, not a new discovery.

There is no evidence that adding dependencies repairs production code. New
qualification is based on original negative native baselines, source provenance,
TaskResult/JUnit consistency and complete cleanup. GPU03 algorithm results are
separate; this round supplies no new Gemma repair or leaderboard evidence.

## Sources and limits

* [PyPI inline-snapshot0.21.1](https://pypi.org/project/inline-snapshot/0.21.1/)
* [Competition rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules)
* NEW_DEPENDENCIES.json: exact public artifact URLs, SHA, METADATA, tags, licenses.
* ENVIRONMENT_RECOVERY.json and V02B_ENVIRONMENT_LOCK.json: actual installation,
  original/recovered counts, source hashes, mandatory closure and versions.

Compatibility is observed for these controls and selected baselines. It is not
a claim that every upstream extra, every untested task, or the official scoring
image has the same complete environment.
