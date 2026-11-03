"""Owned CPU process protocol fixture, NOT a real Agent/native evaluation."""
import sys
from pathlib import Path
from result_contract import dump,seal,sha
root=Path(sys.argv[1]);mode=sys.argv[2]
if mode=='crash':raise SystemExit(7)
if mode=='missing':raise SystemExit(0)
sid='owned-process'
cleanup=dict(schema='EGRD_CLEANUP_V2',session_id=sid,complete=mode!='cleanup_failure',records=[dict(scope='owned protocol fixture only, no sandbox/native execution')])
if mode=='aggregate':
 child=root/'child/SUPERVISOR_RESULT.json';dump(child,dict(allow_next_run=True,cleanup_complete=True,fixture_only=True))
 row=dict(schema='EGRD_AGGREGATE_V2',session_id=sid,complete=True,children_trusted=True,planned_sessions=1,children=[dict(receipt='child/SUPERVISOR_RESULT.json',sha256=sha(child))])
 seal(root,row,cleanup,0,role='aggregate')
else:
 dump(root/'NATIVE_RESULT.json',dict(status='ERROR' if mode=='native_failure' else 'SUCCESS',resolved=False,test_exit_code=1,fixture_only=True))
 (root/'native-junit-0.xml').write_text('<testsuites><testsuite><testcase name="owned"><failure/></testcase></testsuite></testsuites>')
 row=dict(schema='EGRD_SESSION_V2',session_id=sid,failure_classification='AGENT_TIMEOUT' if mode=='agent_timeout' else 'AGENT_COMPLETED',native_result_path='NATIVE_RESULT.json',native_result_sha256=sha(root/'NATIVE_RESULT.json'))
 seal(root,row,cleanup,0)
