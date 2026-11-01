"""CPU admission boundaries, independent of model/repair capability."""
import ast,copy,json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
raw=(D/'r2a_coordinator.py').read_bytes();tree=ast.parse(raw)
ns={};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admission'],type_ignores=[]),'actual-admission-function','exec'),ns)
base=dict(cleanup=True,evidence_complete=True,agent_error=None,evaluation=dict(sdk_native=dict(test_exit_code=1,error=None,observed_junit=dict(errors=0,positive_controls_passed=True),verification_source_guard=dict(unchanged=True))))
outcome=dict(allow_next_run=True);rows=[]
def check(name,row,expected,controller=outcome):
    actual=ns['admission'](row,controller);assert actual==expected,(name,actual,expected)
    rows.append(dict(case=name,expected=expected,actual=actual))
check('ordinary incorrect/no patch with intact controls',copy.deepcopy(base),'CONTINUE')
r=copy.deepcopy(base);r['agent_error']='Agent exceeded session timeout (8 min)';check('Agent timeout with retained fallback evidence',r,'CONTINUE')
r=copy.deepcopy(base);r['evaluation']['sdk_native'].update(test_exit_code=2,error='Failed to apply agent patch: malformed hunk');check('inapplicable Agent patch ordinary failure',r,'CONTINUE')
r=copy.deepcopy(base);r['agent_error']='ContextWindowExceededError';check('backend/context error',r,'STOP')
for field in ('cleanup','evidence_complete'):
    r=copy.deepcopy(base);r[field]=False;check(field+' failure',r,'STOP')
r=copy.deepcopy(base);r['evaluation']['sdk_native']['observed_junit']['positive_controls_passed']=False;check('necessary positive control failure',r,'STOP')
r=copy.deepcopy(base);r['evaluation']['sdk_native']['verification_source_guard']['unchanged']=False;check('checks or production changed during verification',r,'STOP')
r=copy.deepcopy(base);r['evaluation']['sdk_native'].update(test_exit_code=0,error='Required test node did not pass: frozen-name',independent_exact=dict(status='INDEPENDENT_TEST_PASS'));check('approved exact-node exception retains raw SDK failure',r,'CONTINUE')
r=copy.deepcopy(base);r['evaluation']['sdk_native'].update(test_exit_code=0,error='Other SDK failure',independent_exact=dict(status='INDEPENDENT_TEST_PASS'));check('no broad SDK-error bypass',r,'STOP')
check('host supervisor/cleanup failed',copy.deepcopy(base),'STOP',dict(allow_next_run=False))
from independent_exact_evaluator import infrastructure_controls,validate
co='xarray/tests/test_computation.py::test_polyval[timedelta-True]'
observed=dict(positive_controls_passed=False,controls={co:['failure'],'unrelated_control':['pass']})
infra=infrastructure_controls(observed,'pydata__xarray-6599')
assert infra['passed'] and infra['raw_positive_controls_passed'] is False and infra['success_criterion_relaxed'] is False
r=copy.deepcopy(base);r['evaluation']['sdk_native']['observed_junit']['positive_controls_passed']=False;r['evaluation']['sdk_native']['infrastructure_controls']=infra
check('known original co-failure is ordinary unresolved repair, not infra drift',r,'CONTINUE')
observed['controls']['unrelated_control']=['failure']
assert not infrastructure_controls(observed,'pydata__xarray-6599')['passed']
rows.append(dict(case='unrelated failed control is never waived',expected=False,actual=False))
observed['controls']={'unknown':None,co:['failure'],'valid':['pass']}
assert not infrastructure_controls(observed,'pydata__xarray-6599')['passed']
rows.append(dict(case='undeclared missing metadata is never waived',expected=False,actual=False))
xml='<testsuite><testcase classname="xarray.tests.test_computation" name="test_polyval[timedelta-True]"><failure/></testcase><testcase classname="xarray.tests.test_computation" name="target"/></testsuite>'
assert validate(xml,1,['xarray/tests/test_computation.py::target'],[co])['status']=='FAIL'
rows.append(dict(case='original co-target must pass for repair success',expected='FAIL',actual='FAIL'))
result=dict(status='CPU_CONTRACT_PASS',cases=len(rows),coordinator_sha256=hashlib.sha256(raw).hexdigest(),independent_evaluator_sha256=hashlib.sha256((D/'independent_exact_evaluator.py').read_bytes()).hexdigest(),repair_capability_evidence=False,rows=rows)
(D/'STOP_RULE_CONTRACT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],cases=len(rows))))
