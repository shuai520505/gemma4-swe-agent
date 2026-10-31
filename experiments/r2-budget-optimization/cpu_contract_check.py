"""Toy execution of genuine official tools. Not a model or repair-capability test."""
import json,hashlib,importlib.metadata as md
from pathlib import Path
from types import SimpleNamespace
from swegemma.context import SwegemmaContext
from swegemma.budget import EvaluationBudget,HarnessLimits

OUT=Path(__file__).resolve().parent
class OwnedFakeManager:
 def __init__(self,patch):self.patch=patch;self.commands=[]
 def exec(self,sid,command,**kwargs):
  self.commands.append(dict(command=command,kwargs=kwargs))
  return SimpleNamespace(stdout=self.patch if 'git diff --binary' in command else '',stderr='',exit_code=0,timed_out=False)

ctx=SwegemmaContext(budget=EvaluationBudget(time_minutes=8,tool_calls=28,turns=80),harness=HarnessLimits(command_timeout_seconds=240))
status=ctx.create_tools()['get_status']();assert ctx.tool_calls_used==0 and status['time_seconds_remaining']==480.0
assert not any('global' in k for k in status)
examples=[]
for patch in ['diff --git a/owned.py b/owned.py\n--- a/owned.py\n+++ b/owned.py\n@@ -1 +1 @@\n-old\n+new\n','']:
 fake=OwnedFakeManager(patch);ctx.docker=fake;ctx._container_id='owned';ctx.repo='test/mock_repo_owned'
 result=ctx.create_tools()['submit_patch']()
 assert result['status']=='ok' and ctx.patch_submitted and ctx.submitted_patch==patch and ctx.tool_calls_used==0
 assert any('git add -N' in r['command'] for r in fake.commands) and any('git diff --binary' in r['command'] for r in fake.commands)
 assert 'diff' not in result
 examples.append(dict(patch_empty=not bool(patch),result=result,commands=fake.commands,patch_submitted_flag=ctx.patch_submitted))
result=dict(evidence='CPU_CONTRACT_FIXTURE_ONLY',real_official_tools=True,source_unchanged=True,model_requests=0,sandbox_created=False,repair_capability_evidence=False,versions={k:md.version(k) for k in ['swegemma','adk-submission','google-adk']},get_status_result=status,submissions=examples,
 interpretation='submit_patch collects a diff but returns only size/file metadata; it does not itself validate a repair or display full diff text. Empty patch still returns status ok and patch_submitted true. get_status is current-session-only and uncharged, but obtaining another model response after it can still consume wall time.')
(OUT/'CPU_TOOL_CONTRACT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print('PASS: current-session status, internal diff collection, uncharged and empty-patch semantics; no model inference.')
