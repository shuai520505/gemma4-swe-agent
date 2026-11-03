"""Bounded local CPU checks. No packages installed, services, Kaggle calls or GPU."""
import json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent;D=R.parent;ROOT=D.parents[1]
logs=R/'regression-logs';logs.mkdir(exist_ok=False)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=os.pathsep.join([str(D/'.cpu-deps'),str(ROOT/'outputs/r12_redispatch/mount-mirror/source'),str(D),str(R)]))
stages=[('existing47',['-m','unittest','discover','-s',str(D),'-p','test_*.py']),('legacy27',['-m','unittest','discover','-s',str(D/'legacy_tests'),'-p','test_*.py']),('infrastructure6',[str(D.parent/'r2-infra-hardening-01/test_stop_policy.py')]),('fixture_evidence16',['-m','unittest','discover','-s',str(R),'-p','test_*.py']),('Compiler4',[str(R/'compiler_check.py')])]
active=[];done=[]
for name,args in stages:
 argv=[sys.executable,'-X','utf8']+args;stream=(logs/(name+'.log')).open('w',encoding='utf8')
 record=dict(stage=name,argv=argv,started_utc=datetime.now(timezone.utc).isoformat(),scope='Local Windows CPU; no new Linux/Native acceptance',log=str((logs/(name+'.log')).relative_to(D)))
 p=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
 active.append((p,stream,time.monotonic(),record))
while active:
 remaining=[]
 for p,stream,started,record in active:
  if p.poll() is None and time.monotonic()-started<1200:remaining.append((p,stream,started,record));continue
  if p.poll() is None:
   import psutil
   owned=psutil.Process(p.pid);children=owned.children(recursive=True)
   for child in children:child.kill()
   p.kill();p.wait();record['timeout']=True
  stream.close();record.update(exit_code=p.returncode,finished_utc=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-started);done.append(record)
  print(json.dumps(dict(stage=record['stage'],exit_code=p.returncode)),flush=True)
 active=remaining
 (R/'REGRESSION_EXECUTIONS.json').write_text(json.dumps(dict(completed=done,running=[r[3] for r in active]),indent=2),encoding='utf8')
 if active:time.sleep(1)
assert all(x['exit_code']==0 for x in done),'One or more CPU checks failed'
