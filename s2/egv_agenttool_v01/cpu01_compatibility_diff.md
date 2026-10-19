# Compatibility/fixture changes since cpu01; candidate ZIP/Prompts unchanged

```diff
--- cpu01
+++ cpu03
@@ -160,7 +160,7 @@
         actual_exec=manager.exec
         def failing_git(sandbox_id, command, *, timeout=None):
             if 'git diff --binary' in command:
-                return ExecutionResult(exit_code=2,stdout='',stderr='CPU injected git failure')
+                return ExecutionResult(status='error',exit_code=2,stdout='',stderr='CPU injected git failure')
             return actual_exec(sandbox_id,command,timeout=timeout)
         manager.exec=failing_git
     transport=ScriptedTransport(case)
@@ -181,6 +181,12 @@
             from swegemma.models import Task
             base=directory/'snapshot_source';base.mkdir();(base/'app.py').write_text(BAD);(base/'checks.py').write_text(CHECKS)
             subprocess.run(['git','init','-q',str(base)],check=True)
+            # A real task archive has a valid Git baseline. An unborn HEAD
+            # makes the actual submit_patch Git diff fail, independently of
+            # AgentTool correctness. Keep CPU02's failure evidence unchanged.
+            for args in [('config','user.email','cpu@example.invalid'),('config','user.name','CPU'),
+                         ('add','.'),('commit','-qm','synthetic baseline')]:
+                subprocess.run(['git','-C',str(base),*args],check=True)
             archive=directory/'synthetic.tgz'
             with tarfile.open(archive,'w:gz') as tar:tar.add(base,arcname='.')
             task=Task(instance_id='s2_cpu_'+case,repo='test/mock_repo',base_commit='synthetic',problem_statement='Fix boundary without changing negative behavior.')
@@ -191,9 +197,11 @@
             def observed_init(obj,*args,**kwargs):
                 nonlocal plugin
                 if plugin is None: plugin=AuditPlugin(manager.sandboxes[manager.agent_id]['workspace'],context,journal)
-                plugins=list(kwargs.get('plugins') or [])
+                app=kwargs.get('app')
+                plugins=list((app.plugins if app is not None else kwargs.get('plugins')) or [])
                 if not any(p.name==plugin.name for p in plugins):plugins.append(plugin)
-                kwargs['plugins']=plugins
+                if app is not None: app.plugins=plugins
+                else: kwargs['plugins']=plugins
                 original_init(obj,*args,**kwargs)
             with patch('httpx.AsyncClient.send',transport.send),observe_http(directory),patch.object(Runner,'__init__',observed_init):
                 submitted,error,trace=await run_agent_sandbox(manager,config,task,archive,context=context)
```
