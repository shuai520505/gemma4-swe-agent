# Reproduction and artifact scopes

## Local deterministic tests

Python3.12 plus Git are sufficient for `python -m unittest discover -s experiments/egrd-v01-12b -p "test_*.py"`. Tests create only owned temporary repositories/assertion scripts. No test dispatches a Notebook or requests a model. Run inherited infrastructure checks separately with `python experiments/r2-infra-hardening-01/test_stop_policy.py`.

`python experiments/egrd-v01-12b/build.py` deterministically reconstructs four small ZIPs from the copied immutable S0 prompt in inputs/s0/system.md, current module source and unchanged MEER. Fixed ZIP timestamps/modes make hashes reproducible. Existing historical S0 is never overwritten. Validate with test_packages.py and the official Compiler using pinned organizer wheels; SDK versions are in the actual CPU receipt.

## Official sandbox integration

CPU/GPU Notebook builders deliberately reuse the prior research bootstrap, Linux interpreter/wheels, source snapshots, supervisor, non-root manager, HTTP observer, native evaluator and cleanup. They are not self-contained installers from an arbitrary clean machine. Required authenticated inputs are pinned by CPU_BUILD, gpu-notebook/BUILD, MODEL_CONFIGURATIONS and TASK_IDENTITY_MANIFEST; the CPU integration input archive has SHA256 c8d306b82cb798a59e01dbade70ac2e9c5942a2fbf9105464b04c3ac1f78c875. Prior source materialization uses the original accepted Notebook in work/gemma-r12-01/authorized-gpu-02/study.ipynb and the CPU ready archive from wudangdexiaodoashi/r2a-final-cpu-overlay-01 version3. Account access and accepted competition/model terms are prerequisites. No credential is embedded.

The exact dispatched Notebook is the accepted private Kaggle version1 of wudangdexiaodoashi/egrd-v01-12b-pilot01. Its SHA256 is preserved in gpu-notebook/BUILD and its input code in the recovered execution archive. CPU attempts are retained individually, including failures. They are scripted engineering fixtures, never Gemma repair evidence.

## Version boundary

pilot-frozen preserves the dispatch-time packages/core/manifest and CPU proof identity. Subsequent current-source fixes address reproduced consistency defects and are independently CPU-tested. Do not rebuild current packages and then attribute the original GPU results to those bytes. Join results using the dispatched package/script hashes, never directory names alone.

## Authorized execution boundary

The separate dispatch script checks an authorization receipt, fresh total_seconds quota, exact config/Notebook hashes and creates a durable exclusive one-shot claim before SaveKernel. The completed dispatch must never be repeated. collect.py only observes/downloads that accepted run; analyze.py only reads its archive. No official competition Submission is included. A future experiment needs a new protocol and independent dispatch directory/authorization scope; deleting the claim to retry is forbidden.

## Missing measurements

No architectural control beyond the available official SDK interface is assumed. No absent token count is filled with zero; cancelled requests may have unknown usage. HTTP latency includes multiple backend phases, not isolated thinking. Public development SDK resolved, semantic repair review, canonical SWE-bench resolved and hidden Kaggle score are separate endpoints.
