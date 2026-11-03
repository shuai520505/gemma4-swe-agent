"""Bounded, opt-in verification of an Agent-owned Python assertion reproducer.

Runs only through the organizer's sandbox skill executor. A SUPPORTED verdict
means an unchanged source tree passed this particular executed assertion script,
never semantic correctness, Issue coverage, or Native Resolved. No host callback,
tool wrapping, hidden tests, model calls, package installs, or submit hook.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

MAX_FILES = 30000
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_CHECK_BYTES = 64 * 1024
REPORT_PREFIX = "MEER_CHILD_REPORT="


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                       timeout=5, check=True)
    return p.stdout


def tree_identity(root):
    """Hash tracked regular files, not just the files the model says it edited.

    Untracked files (including diagnostics) also invalidate evidence. Excludes
    only Git/cache/build artifacts; protected tests are read as normal public
    workspace data, never overlaid evaluator tests. Symlinks fail closed.
    """
    names = set(git(root, "ls-files", "-z").decode().split("\0"))
    names.update(git(root, "ls-files", "--others", "--exclude-standard", "-z").decode().split("\0"))
    names.discard("")
    # Official skill executor creates a fresh .adk_exec_<id>.py each call.
    names = {n for n in names if not (n.startswith(".adk_exec_") and n.endswith(".py"))
             and not set(Path(n).parts).intersection({'__pycache__', '.pytest_cache'})}
    if len(names) > MAX_FILES:
        raise ValueError("Source file budget exceeded")
    rows = {}; size = 0
    for name in sorted(names):
        p = root / name
        if p.is_symlink() or not p.resolve().is_relative_to(root):
            raise ValueError("Source symlink or path escape")
        # Deleted tracked source files are still part of the identity.
        if not p.exists():
            rows[name] = None
            continue
        if not p.is_file():
            raise ValueError("Non-regular source file")
        size += p.stat().st_size
        if size > MAX_SOURCE_BYTES:
            raise ValueError("Source byte budget exceeded")
        rows[name] = sha(p.read_bytes())
    return sha(json.dumps(rows, sort_keys=True).encode()), len(rows), size


class InstrumentAssertions(ast.NodeTransformer):
    """Count evaluated, non-constant asserts; never alter a file on disk."""
    def visit_Assert(self, node):
        self.generic_visit(node)
        dynamic = any(isinstance(n, (ast.Name, ast.Call, ast.Attribute, ast.Subscript))
                      for n in ast.walk(node.test))
        node.test = ast.copy_location(ast.Call(
            func=ast.Name(id="__meer_observe_assert__", ctx=ast.Load()),
            args=[node.test, ast.Constant(node.lineno), ast.Constant(dynamic)],
            keywords=[]), node.test)
        return node


def child(check, workspace):
    counts = dict(executed_assertions=0, nonconstant_assertions=0,
                  failed_assertions=0, exception_type=None)
    def observe(value, line, nonconstant):
        counts['executed_assertions'] += 1
        counts['nonconstant_assertions'] += int(nonconstant)
        passed = bool(value)
        counts['failed_assertions'] += int(not passed)
        return passed
    exit_code = 0
    try:
        os.chdir(workspace)
        sys.path.insert(0, str(workspace))
        source = check.read_text(encoding='utf-8')
        code = compile(ast.fix_missing_locations(InstrumentAssertions().visit(ast.parse(source))),
                       str(check), 'exec', optimize=0)
        exec(code, dict(__name__='__main__', __file__=str(check),
                        __meer_observe_assert__=observe))
    except BaseException as exc:
        counts['exception_type'] = type(exc).__name__
        exit_code = 1
    print(REPORT_PREFIX + json.dumps(counts), flush=True)
    return exit_code


def kill_group(process):
    if os.name == 'posix':
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        process.kill()
    process.wait(timeout=5)


def verify(workspace, check, seconds=10, state_dir=None):
    begin = time.perf_counter()
    report = dict(schema='MEER_EVIDENCE_V1', verdict='UNKNOWN',
                  semantic_correctness='UNKNOWN', native_resolved=None,
                  new_evidence=False, subprocess_invocations=0,
                  executed_assertions=None, nonconstant_assertions=None,
                  failed_assertions=None, timed_out=False,
                  source_unchanged_during_check=None,
                  scope='OPT_IN_ASSERTION_REPRODUCER_ONLY',
                  global_submit_gate=False, global_tool_gate=False)
    try:
        workspace = Path(workspace).resolve(strict=True)
        requested = Path(check)
        if requested.is_symlink():
            raise ValueError('Symlink reproducer refused')
        check = requested.resolve(strict=True)
        # Reproducer must be Agent-owned scratch outside the repository. This
        # helper never rewrites repository tests/config or trusted evaluator files.
        if check.is_relative_to(workspace) or not check.is_file():
            raise ValueError('Use an Agent-owned scratch reproducer outside the repository')
        if check.stat().st_size > MAX_CHECK_BYTES or check.suffix != '.py':
            raise ValueError('Invalid reproducer size or extension')
        if not 0 < seconds <= 15:
            raise ValueError('Per-check time must be in (0, 15] seconds')
        before, count, size = tree_identity(workspace)
        check_sha = sha(check.read_bytes())
        report.update(source_sha256=before, source_files=count, source_bytes=size,
                      check_sha256=check_sha, check_timeout_seconds=seconds)
        key = sha((before + check_sha).encode())
        if state_dir is None:
            state_dir = Path(tempfile.gettempdir()) / ('meer-' + sha(str(workspace).encode())[:16])
        state_dir = Path(state_dir)
        if state_dir.is_symlink():
            raise ValueError('Symlink state directory refused')
        state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        receipt = state_dir / 'receipt.json'
        if receipt.is_symlink():
            raise ValueError('Symlink receipt refused')
        if receipt.exists():
            prior = json.loads(receipt.read_bytes())
            if prior.get('key') == key:
                report.update(verdict='OBSERVED', reason='REPEATED_UNCHANGED_CHECK_NOT_EXECUTED',
                              prior_verdict=prior.get('verdict'), evidence_fresh=False)
                return report
        with tempfile.TemporaryFile() as log:
            p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                  '--child', '--workspace', str(workspace), '--check', str(check)],
                                 cwd=workspace, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=os.name == 'posix')
            report['subprocess_invocations'] = 1
            try:
                p.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                report.update(timed_out=True, reason='LOCAL_VERIFICATION_TIMEOUT')
            finally:
                kill_group(p)
            log.seek(0, os.SEEK_END)
            output_size = log.tell()
            log.seek(max(0, output_size - 65536))
            output = log.read().decode('utf-8', errors='replace')
        after, _, _ = tree_identity(workspace)
        unchanged = before == after and check_sha == sha(check.read_bytes())
        report.update(source_unchanged_during_check=unchanged,
                      new_evidence=True, child_exit_code=p.returncode,
                      captured_output_bytes=output_size)
        # Last line must be our own report; a model-written log is not accepted as
        # an input receipt. Agent-owned code is still untrusted (see limitations).
        rows = [x[len(REPORT_PREFIX):] for x in output.splitlines() if x.startswith(REPORT_PREFIX)]
        stats = json.loads(rows[-1]) if rows else {}
        for name in ('executed_assertions', 'nonconstant_assertions', 'failed_assertions', 'exception_type'):
            report[name] = stats.get(name)
        if report['timed_out']:
            pass
        elif not unchanged:
            report['reason'] = 'SOURCE_OR_CHECK_CHANGED_DURING_VERIFICATION'
        elif p.returncode != 0 or stats.get('failed_assertions', 0) > 0:
            report.update(verdict='CONTRADICTED', reason='LOCAL_CHECK_FAILED')
        elif stats.get('nonconstant_assertions', 0) <= 0:
            report['reason'] = 'NO_EXECUTED_NONCONSTANT_ASSERTION'
        else:
            report.update(verdict='SUPPORTED', reason='THIS_ASSERTION_CHECK_PASSED', evidence_fresh=True)
        # Scratch receipt is a convenience cache, not a security attestation.
        data=json.dumps(dict(key=key, verdict=report['verdict']))
        fd, temporary = tempfile.mkstemp(dir=state_dir)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(data)
            os.replace(temporary, receipt)
        finally:
            Path(temporary).unlink(missing_ok=True)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report.update(verdict='UNKNOWN', reason='EVIDENCE_UNAVAILABLE', error_type=type(exc).__name__)
    finally:
        report['wall_seconds'] = time.perf_counter() - begin
    return report


def meer_main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', default='/workspace')
    p.add_argument('--check', required=True)
    p.add_argument('--seconds', type=float, default=10)
    p.add_argument('--child', action='store_true', help=argparse.SUPPRESS)
    args = p.parse_args()
    if args.child:
        return child(Path(args.check), Path(args.workspace))
    print(json.dumps(verify(args.workspace, args.check, args.seconds), sort_keys=True))
    return 0



"""Sandbox-local EGRD state and bounded decisions. Not a global ADK gate."""
import hashlib,json,os,subprocess,time
from pathlib import Path


def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(root,*args):return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True,timeout=5).stdout
def utc():return time.time()

class RepairState:
    @classmethod
    def create(cls,issue_id,original,root,model_id):
        s=cls();s.root=str(Path(root).resolve(strict=True));s.model_id=model_id
        s.contract=dict(issue_id=issue_id,original=original,original_sha256=sha(original.encode()),requirements=[],expected_behavior=[],actual_behavior=[],inputs_outputs=[],boundaries=[],acceptance_criteria=[],unresolved_questions=[],input_authenticity='UNVERIFIED_AGENT_RELAY_UNLESS_HOST_SUPPLIED')
        s.evidence=[];s.cause=None;s.patch_intent=None;s.actions=[];s.flags={};s.phase='HYPOTHESIS';s.revisions=0;s.max_revisions=2;s.native_resolved=None
        s.budget=dict(start_monotonic=time.monotonic(),limit_seconds=300,reserve_seconds=25,tool_calls=None,tokens=None,context_tokens=None,context_capacity=32768,scope='HELPER_CLOCK_ONLY; host elapsed may precede initialization',categories={})
        s.baseline={n:sha(Path(s.root,n).read_bytes()) for n in git(s.root,'ls-files','-z').decode().split('\0') if n and Path(s.root,n).is_file() and not Path(s.root,n).is_symlink()}
        s.rollback_files={};s.baseline_revision=git(s.root,'rev-parse','HEAD').decode().strip()
        s.source_hash=tree_identity(Path(s.root))[0];s.diff_review_hash=None;s.intent_source=None;s.recorded_patch_hash=None;s.revision_ticket=False
        return s
    def validate_contract(self):
        c=self.contract
        if sha(c['original'].encode())!=c['original_sha256']:raise ValueError('Original Issue changed')
        ids=[r['id'] for r in c['requirements']]
        if len(set(ids))!=len(ids):raise ValueError('Duplicate requirement ID')
        for rows in [c['requirements']]+[c[k] for k in ['expected_behavior','actual_behavior','inputs_outputs','boundaries','acceptance_criteria','unresolved_questions']]:
            for r in rows:
                if r.get('status') not in ('OBSERVED','INFERRED','UNVERIFIED'):raise ValueError('Statement provenance required')
                if r['status']=='OBSERVED' and r['text'] not in c['original']:raise ValueError('Observed contract statement must quote original Issue')
    def links(self,ids):
        self.validate_contract()
        if not ids or not set(ids)<=set(r['id'] for r in self.contract['requirements']):raise ValueError('Unknown/empty Issue link')
    def safe_path(self,name):
        p=Path(self.root)/name
        if Path(name).is_absolute() or p.is_symlink() or not p.resolve().is_relative_to(Path(self.root)):raise ValueError('Path escape or symlink')
        return p
    def refresh(self):
        self.validate_contract();current=tree_identity(Path(self.root))[0]
        for e in self.evidence:
            e['stale']=e['source_hash']!=current
            if e.get('check_path'):
                p=Path(e['check_path']);e['stale']|=not p.is_file() or p.is_symlink() or sha(p.read_bytes())!=e['check_hash']
        if self.phase=='PATCH_ACCEPTED' and any(e['type']=='TEST_RESULT' and e['stale'] for e in self.evidence):self.phase='PATCH_REVISED'
        if current!=self.source_hash:
            self.diff_review_hash=None
            if self.phase in ('PATCH_TESTED','PATCH_ACCEPTED'):self.phase='PATCH_REVISED'
        self.source_hash=current;return current
    def add(self,kind,source,observation,requirements,verification='OBSERVED',**extra):
        self.links(requirements);self.refresh()
        row=dict(id='E'+str(len(self.evidence)+1),type=kind,source=source,line_range=None,revision=git(self.root,'rev-parse','HEAD').decode().strip(),source_hash=self.source_hash,observation=observation,requirements=requirements,timestamp=utc(),verification=verification,stale=False,**extra)
        self.evidence.append(row);return row
    def observe_source(self,name,start,end,requirements):
        p=self.safe_path(name);lines=p.read_text(encoding='utf8').splitlines()
        if not 1<=start<=end<=len(lines) or end-start>=150:raise ValueError('Bounded line range required')
        e=self.add('SOURCE_CODE',name,'\n'.join(lines[start-1:end]),requirements);e['line_range']=[start,end];e['file_hash']=sha(p.read_bytes());return e
    def hypothesis(self,h):
        self.links(h['requirements']);self.refresh()
        if not all(h.get(k) for k in ['location','mechanism','prediction','next_experiment','support']):raise ValueError('Incomplete causal hypothesis')
        if not 0<=h.get('confidence',-1)<=1:raise ValueError('Invalid reported confidence')
        supported={e['id'] for e in self.evidence if not e['stale'] and e['verification'] in ('OBSERVED','PASS','FAIL')}
        if not set(h['support'])<=supported:raise ValueError('Hypothesis needs current evidence')
        if not set(h.get('contradictions',[]))<=set(e['id'] for e in self.evidence):raise ValueError('Unknown contradiction')
        self.cause=dict(h,semantic_status='UNVERIFIED',confidence_status='MODEL_REPORTED_NOT_CALIBRATED');self.phase='HYPOTHESIS'
    def intent(self,p):
        self.links(p['requirements'])
        if not self.cause:raise ValueError('Hypothesis required')
        for key in ['files','regions','behavior','support','preserve','discriminating_test']:
            if not p.get(key):raise ValueError('Incomplete Patch Intent: '+key)
        self.refresh();known={e['id'] for e in self.evidence if not e['stale']}
        if not set(p['support'])<=known:raise ValueError('Stale/missing intent evidence')
        snapshot={}
        for n in p['files']:
            file=self.safe_path(n)
            if file.is_file() and file.stat().st_size>1024*1024:raise ValueError('Rollback file exceeds bound')
            snapshot[n]=file.read_bytes().hex() if file.is_file() else None
        if sum(len(v or '') for v in snapshot.values())>4*1024*1024:raise ValueError('Rollback byte bound')
        self.rollback_files=snapshot
        self.patch_intent=dict(p,semantic_relevance='UNVERIFIED_MODEL_CLAIM',timestamp=utc());self.intent_source=self.source_hash;self.phase='PATCH_INTENT'
    def changes(self):
        current=set(git(self.root,'ls-files','-z').decode().split('\0'))|set(git(self.root,'ls-files','--others','--exclude-standard','-z').decode().split('\0'))
        return sorted(n for n in current|set(self.baseline) if n and not set(Path(n).parts).intersection({'__pycache__','.pytest_cache'}) and not (n.startswith('.adk_exec_') and n.endswith('.py')) and ((sha(self.safe_path(n).read_bytes()) if self.safe_path(n).is_file() else None)!=self.baseline.get(n)))
    def record_patch(self):
        if not self.patch_intent:raise ValueError('No Patch Intent')
        self.refresh();changed=self.changes();self.flags['outside_intent']=sorted(set(changed)-set(self.patch_intent['files']))
        if not changed:raise ValueError('Empty patch')
        if self.recorded_patch_hash is not None and self.recorded_patch_hash!=self.source_hash:
            if not self.revision_ticket:
                if self.revisions>=self.max_revisions:raise ValueError('Revision budget exhausted')
                self.revisions+=1
            self.revision_ticket=False
        self.recorded_patch_hash=self.source_hash
        if self.phase=='PATCH_ACCEPTED':self.phase='PATCH_REVISED'
        else:self.phase='PATCH_CREATED'
        return self.add('PATCH_DIFF','git diff',git(self.root,'diff','--binary',self.baseline_revision).decode(errors='replace'),self.patch_intent['requirements'])
    def remaining(self):return max(0,self.budget['limit_seconds']-(time.monotonic()-self.budget['start_monotonic']))
    def action(self,kind,signature,justification=None,duration=None):
        self.refresh();self.actions.append(dict(kind=kind,signature=signature,source_hash=self.source_hash,justification=justification,timestamp=utc(),duration_seconds=duration))
        if duration is not None:self.budget['categories'][kind]=self.budget['categories'].get(kind,0)+duration
    def check(self,path,requirements,purpose,seconds=10):
        self.links(requirements);self.refresh()
        if purpose not in ('TARGET','REGRESSION'):raise ValueError('Check purpose required')
        if seconds<=0 or seconds>15 or seconds+self.budget['reserve_seconds']>self.remaining():raise ValueError('Insufficient helper reserve')
        path=Path(path).resolve(strict=True);h=sha(path.read_bytes())
        prior=next((e for e in reversed(self.evidence) if e.get('check_hash')==h and e.get('purpose')==purpose and not e['stale']),None)
        if prior:return prior
        start=time.monotonic();r=verify(self.root,path,seconds,Path(self.state_directory)/'meer' if hasattr(self,'state_directory') else None)
        self.action('RUN_'+purpose+'_TEST',h,duration=time.monotonic()-start)
        environment=r.get('exception_type') in ('ModuleNotFoundError','ImportError','FileNotFoundError')
        status='PASS' if r['verdict']=='SUPPORTED' and r.get('source_unchanged_during_check') else 'FAIL' if r['verdict']=='CONTRADICTED' and not environment else 'UNKNOWN'
        # MEER caches by source/check, not semantic purpose. Reuse only our own
        # source-bound executed receipt; never promote a cache-only response.
        if r['verdict']=='OBSERVED':
            same=next((e for e in reversed(self.evidence) if e.get('check_hash')==h and not e['stale'] and e.get('verification')=='PASS'),None)
            if same:status='PASS';r['egrd_reused_executed_evidence']=same['id']
        e=self.add('ENVIRONMENT_RESULT' if environment else 'TEST_RESULT',str(path),r,requirements,status,check_path=str(path),check_hash=h,purpose=purpose)
        self.phase='PATCH_TESTED' if self.patch_intent else self.phase;return e
    def review_diff(self):
        self.refresh();self.diff_review_hash=self.source_hash
        return dict(source_hash=self.source_hash,changed_files=self.changes(),untracked_not_in_diff=sorted(set(git(self.root,'ls-files','--others','--exclude-standard','-z').decode().split('\0'))&set(self.changes())),diff=git(self.root,'diff','--binary',self.baseline_revision).decode(errors='replace'),semantic_review='UNVERIFIED_REQUIRES_MAIN_AGENT')
    def accept(self):
        self.refresh()
        if self.patch_intent:self.flags['outside_intent']=sorted(set(self.changes())-set(self.patch_intent['files']))
        if not self.patch_intent or self.flags.get('outside_intent') or not self.changes():raise ValueError('Unlinked/empty patch')
        if set(git(self.root,'ls-files','--others','--exclude-standard','-z').decode().split('\0'))&set(self.changes()):raise ValueError('Untracked patch files lack reviewed Git diff; include in index intent then review again')
        if self.recorded_patch_hash!=self.source_hash:raise ValueError('Patch change has not been recorded')
        if self.diff_review_hash!=self.source_hash:raise ValueError('No current diff review')
        checks=[e for e in self.evidence if e['type']=='TEST_RESULT' and not e['stale']]
        if any(e['verification']=='FAIL' for e in checks):raise ValueError('Current counterexample contradicts patch')
        for purpose in ('TARGET','REGRESSION'):
            covered={r for e in checks if e['verification']=='PASS' and e['purpose']==purpose for r in e['requirements']}
            if not set(self.patch_intent['requirements'])<=covered:raise ValueError('Current targeted/regression evidence incomplete')
        self.phase='PATCH_ACCEPTED'
        return dict(verdict='LOCAL_CHECKS_SUPPORTED',semantic_correctness='UNKNOWN',native_resolved=None,global_submit_gate=False)
    def revise(self):
        if self.revisions>=self.max_revisions:raise ValueError('Revision budget exhausted')
        self.revisions+=1;self.revision_ticket=True;self.phase='PATCH_REVISED';self.diff_review_hash=None
    def rollback(self):
        if not self.patch_intent:raise ValueError('No scoped intent to roll back')
        for name in self.patch_intent['files']:
            p=self.safe_path(name)
            if self.rollback_files.get(name) is not None:p.write_bytes(bytes.fromhex(self.rollback_files[name]))
            elif p.is_file():p.unlink()
        self.refresh();self.phase='PATCH_REVISED'
    def next_action(self):
        self.refresh()
        if self.remaining()<=self.budget['reserve_seconds']:return dict(action='SUBMIT',reason='RESERVE_WINDOW',supported_patch=self.phase=='PATCH_ACCEPTED',scope='ADVISORY_OFFICIAL_SUBMIT_NOT_INTERCEPTED')
        if len(self.actions)>1 and all(self.actions[-1][k]==self.actions[-2][k] for k in ('kind','signature','source_hash')) and not self.actions[-1]['justification']:
            return dict(action='FORM_HYPOTHESIS',reason='REPEATED_UNCHANGED_ACTION')
        if self.patch_intent and self.changes():
            checks=[e for e in self.evidence if e['type']=='TEST_RESULT' and not e['stale']]
            if set(self.changes())-set(self.patch_intent['files']) or any(e['verification']=='FAIL' for e in checks):
                return dict(action='REVISE_PATCH',reason='OUTSIDE_INTENT_OR_FRESH_COUNTEREXAMPLE')
            required=set(self.patch_intent['requirements'])
            for purpose,action in [('TARGET','RUN_TARGETED_TEST'),('REGRESSION','RUN_REGRESSION_TEST')]:
                covered={r for e in checks if e['verification']=='PASS' and e.get('purpose')==purpose for r in e['requirements']}
                if not required<=covered:return dict(action=action,reason='PATCH_NEEDS_FRESH_'+purpose+'_CHECK')
            if self.diff_review_hash!=self.source_hash:return dict(action='INSPECT',reason='CURRENT_DIFF_REVIEW_REQUIRED')
            return dict(action='SUBMIT',reason='LOCAL_EVIDENCE_COMPLETE' if self.phase=='PATCH_ACCEPTED' else 'LOCAL_ACCEPT_REQUIRED_THEN_OFFICIAL_SUBMIT',supported_patch=self.phase=='PATCH_ACCEPTED')
        current_evidence={e['id'] for e in self.evidence if not e['stale']}
        if self.cause and set(self.cause['support'])<=current_evidence and not self.cause.get('contradictions'):return dict(action='EDIT',reason='MODEL_HYPOTHESIS_HAS_CURRENT_EVIDENCE; semantic sufficiency unverified')
        return dict(action='INSPECT' if not self.evidence else 'FORM_HYPOTHESIS',reason='MISSING_DISCRIMINATING_EVIDENCE')
    def save(self,path):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        if path.is_symlink() or path.parent.is_symlink() or path.resolve().is_relative_to(Path(self.root)):raise ValueError('State must be scratch outside workspace')
        self.state_directory=str(path.parent);data=json.dumps(self.__dict__,sort_keys=True)
        if len(data)>8*1024*1024:raise ValueError('State byte bound exceeded')
        tmp=path.with_suffix('.tmp');tmp.write_text(data,encoding='utf8');os.replace(tmp,path)
    @classmethod
    def load(cls,path):
        p=Path(path)
        if p.is_symlink() or p.parent.is_symlink():raise ValueError('Symlink state refused')
        s=cls();s.__dict__.update(json.loads(p.read_bytes()));s.refresh();return s

"""Single-file packaged Skill entry; no model calls, callbacks or custom tools."""
import argparse,json,os,sys
from pathlib import Path

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
