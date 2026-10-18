"""Offline CPU reproduction against retained output; never patches the frozen runner."""
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
phase2=json.loads((root/'results/gpu/runs/01-rich_3278-control/phase2_execution.json').read_text())
text=phase2['stdout']+'\n'+phase2['stderr']
pattern=r'\bERROR\b|\b\d+ errors?\b|INTERNALERROR|ModuleNotFoundError'
matches=[m.group() for m in re.finditer(pattern,text)]
assert matches and set(matches)=={'4 errors'}
summary=text.strip().splitlines()[-1]
assert summary=='4 failed, 19 passed in 0.11s'
assert 'ERROR collecting' not in text and 'ERROR at setup' not in text
print(json.dumps(dict(reproduced=True,frozen_predicate_fires=True,
    matched_test_payload=matches[0],match_count=len(matches),actual_summary=summary,
    conclusion='Ordinary assertion regressions incorrectly classified as verifier environment',
    frozen_runtime_or_STOP_modified=False,additional_GPU_runs=0),indent=2))
