import os,subprocess,sys,tempfile,unittest
from pathlib import Path
from source_binding import source_paths,bind_command

class SourceBindingTests(unittest.TestCase):
 def test_src_layout_source_wins_over_approved_dependency(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for directory,value in [('workspace/src','LOCKED_SOURCE'),('opt/approved','DEPENDENCY_COPY')]:
    p=root/directory/'owned_requests_probe';p.mkdir(parents=True)
    (p/'__init__.py').write_text('IDENTITY='+repr(value))
   env=dict(os.environ,PYTHONPATH=os.pathsep.join(str(root/p.lstrip('/')) for p in source_paths('psf/requests')))
   old=dict(env,PYTHONPATH=os.pathsep.join([str(root/'workspace'),str(root/'opt/approved')]))
   control=subprocess.run([sys.executable,'-c','import owned_requests_probe;print(owned_requests_probe.IDENTITY)'],cwd=root,env=old,capture_output=True,text=True)
   self.assertEqual(control.returncode,0,control.stderr);self.assertEqual(control.stdout.strip(),'DEPENDENCY_COPY')
   r=subprocess.run([sys.executable,'-c','import owned_requests_probe;print(owned_requests_probe.IDENTITY)'],cwd=root,env=env,capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),'LOCKED_SOURCE')
 def test_non_requests_binding_unchanged(self):
  self.assertEqual(bind_command('owned/fixture','python3 -m pytest'),'python3 -m pytest')
 def test_requests_shell_binding_preserves_command(self):
  self.assertEqual(bind_command('psf/requests','python3 -m pytest'), 'export PYTHONPATH=/workspace/src:/workspace:/opt/approved; python3 -m pytest')
 def test_manager_applies_binding_to_agent_and_native_commands(self):
  import ast
  module=ast.parse((Path(__file__).parent/'hardened_runtime.py').read_text(encoding='utf8'))
  manager=next(n for n in module.body if isinstance(n,ast.ClassDef) and n.name=='SubprocessManager')
  method=next((n for n in manager.body if isinstance(n,ast.FunctionDef) and n.name=='exec'),None)
  self.assertIsNotNone(method,'Source binding is not wired into shared Agent/Native manager')
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='bind_command' for n in ast.walk(method)))
  worker=ast.parse((Path(__file__).parent/'pilot_worker.py').read_text(encoding='utf8'))
  native=next(n for n in worker.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='native_evaluate')
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='SubprocessManager' and any(k.arg=='task_repo' for k in n.keywords) for n in ast.walk(native)),'Native evaluator has no Agent Context, so it must receive explicit task repo binding')
if __name__=='__main__':unittest.main()
