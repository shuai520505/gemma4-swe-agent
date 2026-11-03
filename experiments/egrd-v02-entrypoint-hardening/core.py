"""Sandbox-local EGRD state and bounded decisions. Not a global ADK gate."""
import hashlib,json,os,subprocess,time
from pathlib import Path
from meer_verifier import tree_identity,verify

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
