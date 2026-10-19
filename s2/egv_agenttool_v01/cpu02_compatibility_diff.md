# Compatibility/fixture changes since cpu02; candidate ZIP/Prompts unchanged

```diff
--- cpu02
+++ cpu03
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
```
