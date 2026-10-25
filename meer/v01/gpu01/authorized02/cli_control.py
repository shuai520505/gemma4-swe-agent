"""Actual Kaggle CLI under the inherited once-only HTTP journal.

Only the trusted outer operator uses this file. No candidate/worker code changes.
Read-only conflict checks concern recent activity, not every historical notebook.
"""
import ast,contextlib,csv,hashlib,importlib.metadata,inspect,io,json,re,sys,types
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit
import requests
from .read_preflight import HERE,GPU,OWNER,save

def sha(raw):return hashlib.sha256(raw).hexdigest()
def location(batch):
    assert batch in (1,2)
    return HERE/f'batch{batch:02d}',f'{OWNER}/meer-v01-gpu-batch{batch:02d}',f'MEER-V01-MATCHED-PILOT-BATCH{batch:02d}'

def cli(args):
    from kaggle.cli import main
    argv=sys.argv;out=io.StringIO();err=io.StringIO();code=0
    try:
        sys.argv=['kaggle','-W',*args]
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            try:main()
            except SystemExit as exc:code=exc.code or 0
    finally:sys.argv=argv
    return dict(command=['kaggle','-W',*args],exit_code=code,stdout=out.getvalue(),stderr=err.getvalue())

def controller(batch):
    from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import GPU_NOTEBOOK as old
    source=inspect.getsource(old.controller_module)
    assert source.count('Agent_runs=4')==1 and source.count("['max_Agent_runs']==4")==1
    source=source.replace('Agent_runs=4','Agent_runs=3').replace("['max_Agent_runs']==4","['max_Agent_runs']==3")
    directory,slug,eid=location(batch)
    ns=dict(old.__dict__,HERE=directory,SLUG=slug,ID=eid)
    exec(compile(source,'<same-once-controller-three-frozen-sessions>','exec'),ns)
    return ns['controller_module']()

def validate(batch):
    directory,slug,eid=location(batch)
    b=json.loads((directory/'BUILD.json').read_bytes())
    raw=(directory/'notebook/study.ipynb').read_bytes();nb=json.loads(raw)
    assert sha(raw)==b['Notebook_sha256'] and sha(json.dumps(nb).encode())==b['wire_sha256']
    assert sha((GPU/'payload.zip').read_bytes())==b['payload_sha256']
    source=nb['cells'][0]['source']
    line=next(l for l in source.splitlines() if l.startswith("payload=__import__('base64').b64decode("))
    import base64
    encoded=ast.literal_eval(line.split('b64decode(',1)[1][:-1])
    assert sha(base64.b64decode(encoded))==b['payload_sha256']
    grant_line=next(l for l in source.splitlines() if l.startswith('AUTHORIZATION='))
    runtime_grant=json.loads((directory/'RUNTIME_AUTHORIZATION.json').read_bytes())
    assert ast.literal_eval(grant_line.split('=',1)[1])==runtime_grant
    assert runtime_grant['authorization_record_sha256']==sha((HERE/'GPU_AUTHORIZATION_RECORD.json').read_bytes())
    spec=dict(b,execution_id=eid,slug=slug,max_dispatches=1,
        selection_protocol_sha256=json.loads((GPU/'EXECUTION_MANIFEST.json').read_bytes())['preregistration_sha256'],
        configuration=dict(GPU=True,TPU=False,internet=False,model_sources=['google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2'],
                           Agent_runs=3,formal_submission=False,machine_shape='NvidiaL4',session_seconds=10000),
        expected_candidates_in_order=[r['arm'] for r in b['order']],
        sdk_versions={n:importlib.metadata.version(n) for n in ('kaggle','kagglesdk')})
    controller(batch).checked_config(spec)
    return spec

def preflight(batch):
    directory,slug,eid=location(batch);spec=validate(batch)
    assert not (directory/'execution/dispatch.claim').exists(),'Existing dispatch: readonly recovery only'
    if batch==2:
        proof=json.loads((HERE/'BATCH_01_COMPLETION.json').read_bytes())
        assert proof['integrity_complete'] and proof['completed_sessions']==3
    dest=directory/'cli-preflight'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');dest.mkdir(parents=True)
    ledger=[];quota={};original=requests.Session.send;recent_raw=[]
    def send(session,request,**kwargs):
        op=urlsplit(request.url).path.rsplit('/',1)[-1]
        assert op in ['IntrospectToken','ListKernels','GetKernelSessionStatus','GetAcceleratorQuotaStatistics','ListModelInstanceVersionFiles'] and len(ledger)<20
        kwargs.update(timeout=45,allow_redirects=False)
        r=original(session,request,**kwargs)
        ledger.append(dict(operation=op,status=r.status_code,utc=datetime.now(timezone.utc).isoformat(),body_sha256=sha(r.content)))
        if op=='GetAcceleratorQuotaStatistics' and r.status_code==200:quota.update(r.json()['gpuQuota'])
        if op=='ListKernels' and r.status_code==200 and len(recent_raw)==0:recent_raw.extend(r.json().get('kernels',[]))
        return r
    requests.Session.send=send;commands=[]
    try:
        from kaggle import api
        assert api.get_config_value('username')==OWNER
        commands.append(cli(['quota']));assert commands[-1]['exit_code']==0
        commands.append(cli(['kernels','list','--mine','--sort-by','dateRun','--page-size','10','--csv']))
        assert commands[-1]['exit_code']==0
        text=commands[-1]['stdout'];text=text[text.index('ref,'):]
        recent=list(csv.DictReader(io.StringIO(text)))
        assert recent and len(recent)<=10
        states=[]
        for row in recent:
            ref=row['ref'];assert ref.startswith(OWNER+'/')
            result=cli(['kernels','status',ref]);commands.append(result)
            match=re.search(r'KernelWorkerStatus\.(\w+)',result['stdout'])
            assert result['exit_code']==0 and match,'Current recent-resource state unreadable'
            state=match[1];states.append(dict(ref=ref,status=state,last_run_time=row['lastRunTime']))
            assert state in ['COMPLETE','ERROR','CANCELLED'],'Current active/queued resource conflict'
        # Search only the exact new experiment identity; historical placeholder is not a new-job collision.
        commands.append(cli(['kernels','list','--mine','--search',slug.split('/')[1],'--page-size','100','--csv']))
        assert commands[-1]['exit_code']==0
        assert slug not in commands[-1]['stdout'],'Selected slug already exists: readonly recovery only'
        remaining=Decimal(quota['totalTimeAllowed'].removesuffix('s'))-Decimal(quota['timeUsed'].removesuffix('s'))-Decimal(quota['timeReserved'].removesuffix('s'))
        assert Decimal(quota['timeReserved'].removesuffix('s'))==0,'Current GPU reservation conflict'
        assert remaining>=(41200 if batch==1 else 20600)
        model=api.model_instance_version_files('google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',page_size=100)
        m=json.loads((GPU/'EXECUTION_MANIFEST.json').read_bytes());assert not model.next_page_token
        assert {f.name for f in model.files}==set(m['model']['files'])
        import subprocess
        value=dict(identity_confirmed=True,slug_conflict=False,current_readonly_GO=True,payload_integrity=True,
          source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),raw_quota=quota,
          remaining_report_seconds=str(remaining),account_recent_sessions=states,HTTP=ledger,
          conflict_check_scope='Current CLI dateRun top10 states + current raw GPU reservation zero + exact new slug unused; excludes irrelevant historical unreadable metadata from current-conflict decisions',
          historical_UNKNOWN='PR27Batch2 remains UNKNOWN; exact403 investigated in read01; no inference about historical acceptance/rejection',
          historical_404='Read failures preserved, not converted to terminal states; not evidence of current activity',
          actual_GPU_allocation='RUNTIME_CHECK_BEFORE_INFERENCE',actual_model_weight_hashes='RUNTIME_CHECK_BEFORE_INFERENCE',
          planned_window_seconds=10000,batch=batch)
        save(dest/'DYNAMIC_PRECHECK.json',value)
        print(json.dumps(dict(batch=batch,current_recent_resources_terminal=len(states),quota_report_seconds=str(remaining),slug_unused=True)))
        return dest
    finally:
        requests.Session.send=original;save(dest/'CLI_COMMANDS.json',commands);save(dest/'HTTP_LEDGER.json',ledger)

def launch(batch):
    directory,slug,eid=location(batch);spec=validate(batch)
    gates_path=sorted((directory/'cli-preflight').glob('*/DYNAMIC_PRECHECK.json'))[-1]
    gates=json.loads(gates_path.read_bytes())
    assert (datetime.now(timezone.utc)-datetime.fromisoformat(gates['HTTP'][-1]['utc'])).total_seconds()<600
    assert gates['current_readonly_GO'] and not list(directory.glob('execution*/dispatch.claim'))
    import subprocess
    gates['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    grant=json.loads((directory/'RUNTIME_AUTHORIZATION.json').read_bytes())
    assert grant['quota_at_dispatch_report_seconds']==gates['remaining_report_seconds'],'Quota changed: freeze a new outer grant, do not alter shared payload'
    grant.update(execution_id=eid,slug=slug,model_source='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',
                 **{k:spec[k] for k in ('Notebook_sha256','wire_sha256','payload_sha256')})
    # Authenticate/read identity BEFORE entering the SaveKernel-only transport.
    # An earlier local attempt stopped here with zero dispatches; retain its lock/journal.
    from kaggle import api
    from kaggle.cli import main
    assert api.get_config_value('username')==OWNER
    attempt=1+len([p for p in directory.glob('execution*') if p.is_dir()])
    execution='execution' if attempt==1 else f'execution{attempt:02d}'
    suffix='' if attempt==1 else f'-attempt{attempt:02d}'
    save(directory/f'DISPATCH_AUTHORIZATION{suffix}.json',grant);save(directory/f'DISPATCH_BUILD{suffix}.json',spec)
    save(directory/f'DISPATCH_ATTEMPT{suffix}.json',dict(execution_directory=execution,scope='Local pre-send failures do not consume a GPU SaveKernel; existing claims always block',batch=batch))
    c=controller(batch).Controller(directory/execution,spec)
    def submit_cli():
        # Same official CLI entrypoint, in-process so inherited transport guard
        # persists HTTP metadata before the SDK/CLI parses a response.
        result=cli(['kernels','push','--path',str(directory/'notebook'),'--timeout','10000','--accelerator','NvidiaL4'])
        save(directory/f'CLI_PUSH_RESULT{suffix}.json',result)
        if result['exit_code']:raise RuntimeError('CLI push failed; never repeat a claimed request')
        return None # CLI prints instead of returning SDK identity; reconcile source/version read-only.
    try:c.execute(grant,gates,submit_cli)
    finally:save(directory/f'DISPATCH_SUMMARY{suffix}.json',dict(dispatches=c.dispatches,states=c.journal.states(),GPU=True,batch=batch,formal_submission=False,execution_directory=execution))

if __name__=='__main__':
    mode=sys.argv[1];batch=int(sys.argv[2])
    if mode=='preflight':preflight(batch)
    elif mode=='launch':launch(batch)
    elif mode=='validate':print(validate(batch)['Notebook_sha256'])
    else:raise ValueError(mode)
