"""Single-file packaged Skill entry; no model calls, callbacks or custom tools."""
import argparse,json,os,sys
from pathlib import Path
from core import RepairState
def main():
    if '--child' in sys.argv:
        return meer_main()  # supplied by the bundled, unchanged MEER implementation
    parser=argparse.ArgumentParser();parser.add_argument('--request',required=True);parser.add_argument('--state',default='/tmp/egrd-v01/state.json');parser.add_argument('--workspace',default='/workspace')
    args=parser.parse_args();request=json.loads(args.request);path=Path(args.state)
    if len(args.request)>100000:raise ValueError('Bounded request required')
    if path.is_symlink() or path.parent.is_symlink() or path.resolve().is_relative_to(Path(args.workspace).resolve()):raise ValueError('Scratch state required')
    path.parent.mkdir(parents=True,exist_ok=True);lock=path.parent/'session.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        os.close(fd);op=request.pop('op')
        if op=='init':
            if path.exists():raise ValueError('Cannot silently replace an existing Issue session')
            s=RepairState.create(request['issue_id'],request['original'],args.workspace,request['model_id'])
            for key in ['requirements','expected_behavior','actual_behavior','inputs_outputs','boundaries','acceptance_criteria','unresolved_questions']:
                if key in request:s.contract[key]=request[key]
            s.validate_contract();result=dict(issue_sha256=s.contract['original_sha256'])
        else:
            s=RepairState.load(path)
            if Path(s.root)!=Path(args.workspace).resolve():raise ValueError('Wrong workspace')
            if op=='source':result=s.observe_source(**request)
            elif op=='hypothesis':s.hypothesis(request);result=s.cause
            elif op=='intent':s.intent(request);result=s.patch_intent
            elif op=='record_patch':result=s.record_patch()
            elif op=='check':result=s.check(**request)
            elif op=='review':result=s.review_diff()
            elif op=='accept':result=s.accept()
            elif op=='revise':s.revise();result=dict(revisions=s.revisions)
            elif op=='rollback':s.rollback();result=dict(rollback='SCOPED_INTENT_SNAPSHOT')
            elif op=='action':s.action(**request);result=dict(recorded=True)
            elif op=='next':result=s.next_action()
            else:raise ValueError('Unknown operation')
        s.save(path)
        print(json.dumps(dict(schema='EGRD_V01',result=result,phase=s.phase,next_action=s.next_action(),budget=s.budget,helper_remaining_seconds=s.remaining(),global_tool_gate=False,global_submit_gate=False,native_resolved=None),sort_keys=True))
        return 0
    finally:lock.unlink(missing_ok=True)
if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,KeyError) as exc:
        print(json.dumps(dict(schema='EGRD_V01',status='UNKNOWN_OR_REFUSED',error_type=type(exc).__name__,reason=str(exc),native_resolved=None)));raise SystemExit(1)
