"""Conservative infrastructure latch; never equate all nonzero tools with infra."""
import re
class InfrastructureStop(RuntimeError):pass
def classify_response(response):
    if response.get('name')!='run_command':return None
    body=response.get('response')
    if not isinstance(body,dict) or body.get('status')!='error':return None
    details=body.get('details') or {}
    if details.get('exit_code') in (None,0):return None
    # Actual stderr only: read_file/source text and successful diagnostic prints
    # must not be mistaken for an infrastructure exception.
    stderr=str(details.get('stderr') or '')
    if re.search(r'^locale\.Error: unsupported locale setting\s*$',stderr,re.M):return 'UNSUPPORTED_LOCALE'
    if re.search(r'(?:^|\n)(?:/bin/)?(?:ba)?sh: line \d+: sphinx-build: command not found(?:\n|$)',stderr):return 'REQUIRED_CLI_MISSING'
    if re.search(r"^ModuleNotFoundError: No module named ['\"](?:sphinx|docutils|numpy|pandas|pytest|mpmath)['\"]\s*$",stderr,re.M):return 'PINNED_DEPENDENCY_MISSING'
    return None
class StopLatch:
    def __init__(self):self.evidence=None
    def observe(self,response):
        reason=classify_response(response)
        if reason and self.evidence is None:self.evidence=dict(reason=reason,tool_response=response)
        return self.evidence
    def require_running(self):
        if self.evidence:raise InfrastructureStop('INFRASTRUCTURE_STOP:'+self.evidence['reason'])
def admission(row,outcome,legacy):
    # Check before ordinary malformed-patch early returns.
    receipt=row.get('infrastructure_stop')
    if not isinstance(receipt,dict) or receipt.get('coverage')!='LIVE_ADK_TOOL_RESPONSES_V1' or type(receipt.get('stopped')) is not bool:return 'STOP'
    if receipt.get('stopped'):return 'STOP'
    return legacy(row,outcome)
