import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
py=ROOT/'work/r2-audit/env/Scripts/python.exe';rows=[]
for variant in ['base','r2']:
 source=ROOT/'work/r2-audit/quality/django__django-11964'/('selected-'+variant)
 script="import sys;sys.path[:0]=[sys.argv[1],sys.argv[1]+'/tests'];from django.conf import settings;settings.configure(INSTALLED_APPS=[],DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},USE_I18N=False,SECRET_KEY='owned');import django;django.setup();from django.test.runner import DiscoverRunner;raise SystemExit(DiscoverRunner(verbosity=1).run_tests(['model_enums']))"
 commands=[('django_original_model_enums',[str(py),'-c',script,str(source)],None)]
 source=ROOT/'work/r2-audit/quality/pytest-dev__pytest-5631'/('selected-'+variant)
 env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONPATH=str(source/'src')+os.pathsep+str(ROOT/'work/r2-audit/pytest-deps'))
 ini=OUT/'native_pytest.ini';ini.write_text('[pytest]\n')
 commands.append(('pytest_native_collection',[str(py),'-m','pytest','--assert=plain','-p','no:cacheprovider','-c',str(ini),'-q',str(OUT/'native_collection_cases.py')],env))
 for name,cmd,env in commands:
  try:
   p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=90)
   row=dict(name=name,variant=variant,command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,status='PASS' if p.returncode==0 else 'FAILED_OR_BLOCKED')
  except subprocess.TimeoutExpired:row=dict(name=name,variant=variant,status='NOT_RUN',reason='CPU test timed out')
  rows.append(row);print(json.dumps(dict(name=name,variant=variant,status=row['status'])),flush=True)
(OUT/'NATIVE_CPU_RESULTS.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
