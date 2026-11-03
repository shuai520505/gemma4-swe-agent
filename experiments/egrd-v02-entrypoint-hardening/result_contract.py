"""Explicit v2 worker/aggregate receipts, independent of legacy native-result filenames."""
import hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())

def native_execution_check(native_path):
 """Trust gate over original Native/JUnit artifacts; never changes resolved."""
 import xml.etree.ElementTree as ET
 path=Path(native_path);native=load(path)
 result=dict(passed=False,reason=None,tests=None,errors=None,native_sha256=sha(path),junit=[])
 if type(native.get('test_exit_code')) is not int or native['test_exit_code'] not in [0,1]:
  result['reason']='Native test execution did not finish normally';return result
 reports=sorted(path.parent.glob('native-junit-*.xml'))
 if not reports:result['reason']='Missing actual Native JUnit';return result
 try:
  cases=[]
  for report in reports:
   cases+=ET.fromstring(report.read_bytes()).findall('.//testcase')
   result['junit'].append(dict(path=report.name,sha256=sha(report)))
  result.update(tests=len(cases),executed=sum(c.find('skipped') is None for c in cases),errors=sum(c.find('error') is not None for c in cases))
  result.update(passed=result['executed']>0 and result['errors']==0,reason='JUnit setup/runtime errors or zero executed cases' if not result['executed'] or result['errors'] else None)
 except (ET.ParseError,OSError) as exc:result['reason']=type(exc).__name__
 return result

def assess(directory,process,role='session'):
 root=Path(directory)
 result=dict(schema='EGRD_SUPERVISOR_V2',role=role,classification=None,allow_next_run=False,cleanup_complete=False,native_resolved=None,process=process)
 def stop(kind,detail=None):result.update(classification=kind,reason=detail);return result
 code=process.get('process_exit_code');error=process.get('controller_error')
 if error in ('outer_timeout','stage_timeout'):return stop('WORKER_TIMEOUT',error)
 if type(code) is not int:return stop('RESULT_MISSING','OS exit code unavailable')
 # Preserve concrete cleanup failure even when the child exits nonzero.
 if process.get('process_tree_stopped') is not True:return stop('CLEANUP_FAILED','process tree remains')
 filename='SESSION_RESULT.json' if role=='session' else 'AGGREGATE_RESULT.json'
 paths=[root/filename,root/'CLEANUP.json',root/'worker_done.json']
 if not all(p.is_file() for p in paths):return stop('WORKER_ABNORMAL_EXIT' if code!=0 else 'RESULT_MISSING')
 try:
  row,cleanup,done=map(load,paths)
  expected='EGRD_SESSION_V2' if role=='session' else 'EGRD_AGGREGATE_V2'
  if [row.get('schema'),cleanup.get('schema'),done.get('schema')]!=[expected,'EGRD_CLEANUP_V2','EGRD_DONE_V2']:return stop('RESULT_CONTRACT_INVALID','schema')
  sid=row.get('session_id')
  if not sid or cleanup.get('session_id')!=sid or done.get('session_id')!=sid:return stop('RESULT_CONTRACT_INVALID','identity')
  if done.get('session_result_sha256')!=sha(paths[0]) or done.get('cleanup_sha256')!=sha(paths[1]):return stop('RESULT_CONTRACT_INVALID','receipt hash')
  if cleanup.get('complete') is not True or done.get('cleanup_complete') is not True:return stop('CLEANUP_FAILED')
  result['cleanup_complete']=True
  if code!=0:return stop('WORKER_ABNORMAL_EXIT')
  if type(done.get('exit_code')) is not int or done['exit_code']!=code:return stop('RESULT_CONTRACT_INVALID','exit code')
  if error:return stop('INFRASTRUCTURE_FAILURE',error)
  if role=='aggregate':
   if row.get('complete') is not True or row.get('children_trusted') is not True:return stop('AGGREGATE_STOPPED',row.get('stop_reason'))
   children=row.get('children');planned=row.get('planned_sessions')
   if type(planned) is not int or planned<=0 or not isinstance(children,list) or len(children)!=planned:return stop('RESULT_CONTRACT_INVALID','aggregate child count')
   for child in children:
    rel=Path(child['receipt'])
    if rel.is_absolute() or '..' in rel.parts:return stop('RESULT_CONTRACT_INVALID','child path')
    path=root/rel
    if not path.is_file() or sha(path)!=child['sha256'] or load(path).get('allow_next_run') is not True:return stop('AGGREGATE_STOPPED','child receipt not trusted')
   result.update(classification='AGGREGATE_COMPLETED',allow_next_run=row.get('complete') is True);return result
  label=row.get('failure_classification')
  if label not in ['AGENT_COMPLETED','AGENT_TIMEOUT','NO_PATCH']:
   return stop(label if label in ['MODEL_BACKEND_ERROR','INFRASTRUCTURE_FAILURE','EVIDENCE_INCOMPLETE','NATIVE_EVALUATION_FAILED'] else 'RESULT_CONTRACT_INVALID')
  rel=Path(row.get('native_result_path') or '')
  if rel.is_absolute() or '..' in rel.parts:return stop('RESULT_CONTRACT_INVALID','native path')
  native_path=root/rel
  if not native_path.is_file():return stop('NATIVE_EVALUATION_FAILED','missing native result')
  if row.get('native_result_sha256')!=sha(native_path) or done.get('native_result_sha256')!=sha(native_path):return stop('RESULT_CONTRACT_INVALID','native hash')
  native=load(native_path)
  if native.get('status')!='SUCCESS' or type(native.get('resolved')) is not bool or native.get('test_exit_code') in [-1,124,137]:return stop('NATIVE_EVALUATION_FAILED','native execution did not complete')
  integrity=native_execution_check(native_path);result['native_execution_integrity']=integrity
  if not integrity['passed']:return stop('NATIVE_EVALUATION_FAILED',integrity['reason'])
  result.update(classification=label,allow_next_run=True,native_resolved=native['resolved']);return result
 except (KeyError,TypeError,ValueError,OSError) as exc:return stop('RESULT_CONTRACT_INVALID',type(exc).__name__)


def dump(path,value):
 import os
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp')
 with tmp.open('w',encoding='utf8',newline='\n') as f:
  json.dump(value,f,indent=2);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)

def seal(directory,row,cleanup,exit_code,role='session'):
 root=Path(directory);name='SESSION_RESULT.json' if role=='session' else 'AGGREGATE_RESULT.json'
 dump(root/name,row);dump(root/'CLEANUP.json',cleanup)
 done=dict(schema='EGRD_DONE_V2',session_id=row['session_id'],exit_code=exit_code,cleanup_complete=cleanup.get('complete') is True,session_result_sha256=sha(root/name),cleanup_sha256=sha(root/'CLEANUP.json'),native_result_sha256=row.get('native_result_sha256'))
 dump(root/'worker_done.json',done)
