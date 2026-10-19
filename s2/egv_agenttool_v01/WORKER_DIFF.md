# S2 worker diff from frozen S1

```diff
--- s1/worker.py
+++ s2/egv_agenttool_v01/worker.py
@@ -1,4 +1,4 @@
-"""S1 independent worker derived from frozen r12; see worker-r12.diff."""
+"""Independent S2 research worker; official compiler, tools, evaluator and budgets unchanged."""
 import argparse
 import asyncio
 import hashlib
@@ -8,11 +8,12 @@
 from pathlib import Path
 import traceback
 
-from .config import Config, validate_compiled
+from s1.config import Config
+from s2.egv_agenttool_v01.validation import validate_candidate
 from harness_v2.context_budget import VllmCounter
-from .guard import Guard
+from s1.guard import Guard
 from harness_v2.evidence import Journal,atomic_json,atomic_bytes
-from . import VERSION
+VERSION='s2-egv-agenttool-research-0.1'
 
 
 async def evaluate(spec,directory):
@@ -60,8 +61,7 @@
         graph_dir=cfg.graph_dir,embeddings_dir=cfg.embeddings_dir)
     manager.context=ctx
     compiled=compile_submission(agent_dir,ctx.create_tools(),models,limits=limits,generation_constraints=constraints)
-    assert len(compiled.tools)==6 and not compiled.sub_agents
-    validate_compiled(compiled,budget)
+    validate_candidate(compiled,budget)
     atomic_json(directory/'runtime_config.json',dict(harness_version=VERSION,budget=budget.snapshot(),
         compaction=dict(interval=5,overlap=1,token_threshold=8192,event_retention_size=4),
         operational_limits=dict(max_stdout_chars=2000,max_file_chars=4000,max_file_lines=120),
@@ -75,7 +75,9 @@
     for name in ('swegemma','adk_submission'):
         logger=logging.getLogger(name); logger.setLevel(logging.INFO); logger.addHandler(handler)
     try:
-        result=await evaluator.evaluate_task(task=task,context=ctx)
+        from s2.egv_agenttool_v01.runner_observer import observe_nested
+        with observe_nested(manager,ctx,j):
+            result=await evaluator.evaluate_task(task=task,context=ctx)
         j.stage('persist')
         # Native scalar fields remain untouched. The trace object is exported separately.
         raw=result.model_dump(mode='json',exclude={'trace'})
```
