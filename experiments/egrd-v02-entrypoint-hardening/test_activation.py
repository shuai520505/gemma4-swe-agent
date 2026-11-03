import hashlib,json,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
ISSUE='Accept zero.';H=hashlib.sha256(ISSUE.encode()).hexdigest()
def call(n,id,args,t):return dict(recorded_monotonic=t,event=dict(content=dict(parts=[dict(function_call=dict(name=n,id=id,args=args))])))
def response(n,id,r,t):return dict(recorded_monotonic=t,event=dict(content=dict(parts=[dict(function_response=dict(name=n,id=id,response=r))])))
def good():
 init=dict(op='init',issue_id='t',original=ISSUE,model_id='UNVERIFIED',requirements=[dict(id='R1',text=ISSUE,status='OBSERVED')])
 return [call('load_skill','a',dict(skill_name='egrd-repair'),0),response('load_skill','a',dict(skill_name='egrd-repair',instructions='ok'),1),call('run_skill_script','b',dict(skill_name='egrd-repair',file_path='scripts/egrd.py',args=dict(request=json.dumps(init))),2),response('run_skill_script','b',dict(stdout=json.dumps(dict(schema='EGRD_V01',phase='HYPOTHESIS',result=dict(issue_sha256=H)))),3)]
class ActivationTests(unittest.TestCase):
 def audit(self,events,tools=('load_skill','run_skill_script'),state=None):
  self.assertTrue((D/'activation.py').exists(),'Actual tool trace audit is missing')
  from activation import audit
  return audit(events,list(tools),H,state)
 def test_tool_not_available(self):self.assertEqual(self.audit([],[])['load_skill']['status'],'TOOL_NOT_AVAILABLE')
 def test_model_did_not_call(self):self.assertEqual(self.audit([])['load_skill']['status'],'MODEL_DID_NOT_CALL')
 def test_prose_is_not_tool_execution(self):
  es=[dict(recorded_monotonic=0,event=dict(content=dict(parts=[dict(text='I loaded the skill and initialized')])))];self.assertFalse(self.audit(es)['activated'])
 def test_valid_order_and_initialization(self):self.assertTrue(self.audit(good())['activated'])
 def test_failed_init_not_activation(self):
  es=good();es[-1]['event']['content']['parts'][0]['function_response']['response']=dict(error='NO_CODE_EXECUTOR');r=self.audit(es);self.assertFalse(r['activated']);self.assertEqual(r['run_skill_script']['status'],'TOOL_CALL_FAILED')
 def test_wrong_original_hash_not_activation(self):
  es=good();es[-1]['event']['content']['parts'][0]['function_response']['response']['stdout']=json.dumps(dict(schema='EGRD_V01',phase='HYPOTHESIS',result=dict(issue_sha256='bad')));self.assertFalse(self.audit(es)['activated'])
 def test_exploration_before_initialization(self):
  es=[call('read_file','before',dict(filepath='x'),-.5)]+good();self.assertFalse(self.audit(es)['first_action_order_passed'])
 def test_initialization_before_load_response_is_not_ordered(self):
  es=good();es[2]['recorded_monotonic']=.5;self.assertFalse(self.audit(es)['first_action_order_passed'])
 def test_advisory_control_is_not_initialization(self):
  es=good();es[-1]['event']['content']['parts'][0]['function_response']['response']['stdout']=json.dumps(dict(schema='EGRD_V01',status='ADVISORY_CONTROL'));self.assertFalse(self.audit(es)['activated'])
if __name__=='__main__':unittest.main()
