"""Reuse existing process/job cleanup supervision, adapt only the result contract."""
import shutil
from pathlib import Path
from result_contract import assess,dump

def supervise(command,directory,*,role='session',**kwargs):
 from harness_v2.supervisor import supervise as legacy_supervise
 root=Path(directory);raw=legacy_supervise(command,root,**kwargs)
 if (root/'audit_result.json').exists():shutil.copyfile(root/'audit_result.json',root/'LEGACY_SUPERVISOR_RESULT.json')
 result=assess(root,raw,role=role);dump(root/'SUPERVISOR_RESULT.json',result)
 return result
