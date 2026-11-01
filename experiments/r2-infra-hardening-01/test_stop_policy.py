"""Regression cases use original tool returns, not repair outcome fixtures."""
import ast,copy,importlib,json,os,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
OLD=D.parent/'r2-early-decision-01'
def legacy_decision(response):
    tree=ast.parse((OLD/'r2a_coordinator.py').read_bytes());ns={}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admission'],type_ignores=[]),'frozen-old-admission','exec'),ns)
    row=dict(cleanup=True,evidence_complete=True,agent_error=None,tool_responses=[response],evaluation=dict(sdk_native=dict(test_exit_code=0,error=None,observed_junit=dict(errors=0,positive_controls_passed=True),verification_source_guard=dict(unchanged=True))))
    return ns['admission'](row,dict(allow_next_run=True))
class Regression(unittest.TestCase):
    def check_original(self,needle):
        actions=json.loads(next((OLD/'results').glob('06_*/TOOL_ACTIONS.json')).read_bytes())
        response=next(c['response'] for c in actions if needle in str((c.get('response') or {}).get('response',{})))
        if os.environ.get('TEST_LEGACY')=='1':actual=legacy_decision(response)
        else:
            from stop_policy import classify_response
            actual='STOP' if classify_response(response) else 'CONTINUE'
        self.assertEqual(actual,'STOP')
    def test_original_missing_sphinx_entrypoint(self):self.check_original('sphinx-build: command not found')
    def test_original_unsupported_locale(self):self.check_original('unsupported locale setting')
    def test_ordinary_errors_continue(self):
        from stop_policy import classify_response
        for stderr in ['AssertionError: original bug','SyntaxError: broken agent patch','/bin/bash: line 1: write_file: command not found',"ModuleNotFoundError: No module named 'agent_new_module'",'']:
            self.assertIsNone(classify_response(dict(name='run_command',response=dict(status='error',details=dict(exit_code=1,stderr=stderr)))))
    def test_successful_or_read_output_is_not_infra(self):
        from stop_policy import classify_response
        for name,status in [('read_file','error'),('run_command','ok')]:
            self.assertIsNone(classify_response(dict(name=name,response=dict(status=status,details=dict(exit_code=1,stderr='locale.Error: unsupported locale setting')))))
    def test_pinned_dependency_and_persistent_latch(self):
        from stop_policy import StopLatch,InfrastructureStop
        latch=StopLatch();response=dict(name='run_command',response=dict(status='error',details=dict(exit_code=1,stderr="ModuleNotFoundError: No module named 'docutils'")))
        self.assertEqual(latch.observe(response)['reason'],'PINNED_DEPENDENCY_MISSING')
        latch.observe(dict(name='run_command',response=dict(status='ok')))
        with self.assertRaises(InfrastructureStop):latch.require_running()
    def test_coordinator_never_waives_or_missing_receipt(self):
        from stop_policy import admission
        for receipt in [None,dict(coverage='LIVE_ADK_TOOL_RESPONSES_V1',stopped=True),dict(coverage='LIVE_ADK_TOOL_RESPONSES_V1')]:
            self.assertEqual(admission(dict(infrastructure_stop=receipt),{},lambda r,o:'CONTINUE'),'STOP')
        self.assertEqual(admission(dict(infrastructure_stop=dict(coverage='LIVE_ADK_TOOL_RESPONSES_V1',stopped=False)),{},lambda r,o:'CONTINUE'),'CONTINUE')
if __name__=='__main__':unittest.main()
