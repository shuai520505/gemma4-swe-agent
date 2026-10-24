# EGRD V0.1: historical repair-decision autopsy

Status: **EGRD_RESEARCH_COMPLETE_MORE_EVIDENCE_REQUIRED**.

This is research, not a new Agent. It examines 26 real-model sessions / 784 tool actions from 11 accessible archives. There are 26 raw native booleans, but only 25 interpretable repair outcomes: 13 true, 12 false; one fixture-confounded outcome remains null. Three successes are repeated owned synthetic cases. These heterogeneous development runs must not be pooled into a benchmark treatment effect.

Start with [FAILURE_AUTOPSY.md](FAILURE_AUTOPSY.md), [CASE_STUDIES.md](CASE_STUDIES.md), and [ARCHITECTURE_DECISION.md](ARCHITECTURE_DECISION.md). No production candidate, GPU experiment, Notebook or competition submission was created. S0 and MEER remain unchanged.

Reproduction from repository root, with the privately retained inputs listed in EVIDENCE_MANIFEST.json:

```powershell
python egrd/v01/audit.py --private-output '../private-evidence/egrd_v01_autopsy/actions'
python egrd/v01/review.py
python egrd/v01/verify_sources.py
python -m unittest discover -s egrd/v01 -p 'test_*.py' -v
```

`audit.py` never executes archived code/commands. It verifies archive SHA/CRC and original manifest entries where available. `review.py` contains explicit human-reviewed labels bound to actual event indices; it is not an automatic causal inference engine. Raw action review stays outside Git. Public outputs contain source hashes, timing, bounded derived observations and limitations. Without private inputs the analysis cannot honestly be regenerated; no fabricated substitute is supplied.

Base: actual open/unmerged Draft PR31, `f8b63e9db3d97760d1798fe12dfd5139871dcdc0`. New isolated branch `feat/egrd-v01-failure-autopsy` changes only this directory.
