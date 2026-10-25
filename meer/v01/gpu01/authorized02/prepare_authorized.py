"""Bind the human grant into unchanged GPU templates; never save or infer."""
import ast,base64,hashlib,json,subprocess,zipfile,io
from pathlib import Path
from .read_preflight import HERE,GPU,save

def sha(b):return hashlib.sha256(b).hexdigest()

def run():
    manifest=json.loads((GPU/'EXECUTION_MANIFEST.json').read_bytes())
    build=json.loads((GPU/'PAYLOAD_BUILD.json').read_bytes())
    grant_source=json.loads((HERE/'GPU_AUTHORIZATION_RECORD.json').read_bytes())
    assert grant_source['payload_sha256']==build['payload_sha256']==sha((GPU/'payload.zip').read_bytes())
    assert manifest['arms']==grant_source['arms']
    assert manifest['batches']==grant_source['batches']
    with zipfile.ZipFile(GPU/'payload.zip') as z:
        assert z.testzip() is None
        for n,h in build['payload_members'].items():assert sha(z.read(n))==h,n
    quota=json.loads((HERE/'preflight/read01/QUOTA_MODEL.json').read_bytes())['remaining_report_seconds']
    from meer.v01.gpu01.session import authorize
    records=[]
    for batch in (1,2):
        grant=dict(GPU_authorized=True,evidence_source='explicit_human_owner_message',
            owner_authorization_reference=grant_source['owner_authorization_reference'],
            human_message_reference=grant_source['owner_authorization_reference'],
            experiment_id=manifest['experiment_id'],manifest_sha256=sha((GPU/'EXECUTION_MANIFEST.json').read_bytes()),
            payload_sha256=build['payload_sha256'],batch=batch,order=manifest['batches'][str(batch)],arms=manifest['arms'],
            environment_lock_sha256=manifest['environment_lock_sha256'],model_files=manifest['model']['files'],
            max_SaveKernel_dispatches=1,max_Agent_runs=3,GPU_count=4,GPU_type='NVIDIA L4',TP=4,
            Agent_seconds=300,platform_window_seconds=10000,quota_at_dispatch_report_seconds=quota,
            authorization_record_sha256=sha((HERE/'GPU_AUTHORIZATION_RECORD.json').read_bytes()))
        authorize(grant,manifest,batch,dict(payload_sha256=build['payload_sha256'],production_entry=manifest['production_entry']))
        nb=json.loads((GPU/f'batch{batch:02d}/notebook/study.ipynb').read_bytes())
        source=nb['cells'][0]['source'];assert source.count('AUTHORIZATION=None')==1
        source=source.replace('AUTHORIZATION=None','AUTHORIZATION='+repr(grant))
        nb['cells'][0]['source']=source
        for cell in nb['cells']:
            compile(cell['source'],'<Frozen-MEER-authorized-outer>','exec')
            cell['id']=sha(cell['source'].encode())[:12]
        line=next(l for l in source.splitlines() if l.startswith("payload=__import__('base64').b64decode("))
        payload=base64.b64decode(ast.literal_eval(line.split('b64decode(',1)[1][:-1]))
        assert sha(payload)==build['payload_sha256']
        assert nb['cells'][1]['source']==json.loads((GPU/f'batch{batch:02d}/notebook/study.ipynb').read_bytes())['cells'][1]['source']
        directory=HERE/f'batch{batch:02d}'
        assert not list(GPU.glob(f'**/batch{batch:02d}/execution/dispatch.claim')),'Potential previous dispatch: reconcile only'
        raw=(json.dumps(nb,indent=1)+'\n').encode()
        meta=json.loads((GPU/f'batch{batch:02d}/notebook/kernel-metadata.json').read_bytes())
        meta.update(title=f'MEER V01 authorized matched batch {batch:02d}',machine_shape='NvidiaL4')
        path=directory/'notebook/study.ipynb';path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f:f.write(raw)
        save(directory/'notebook/kernel-metadata.json',meta)
        save(directory/'RUNTIME_AUTHORIZATION.json',grant)
        row=dict(batch=batch,slug=meta['id'],Notebook_sha256=sha(raw),wire_sha256=sha(json.dumps(nb).encode()),
                 payload_sha256=build['payload_sha256'],grant_sha256=sha((directory/'RUNTIME_AUTHORIZATION.json').read_bytes()),
                 order=grant['order'],configuration=dict(GPU=True,GPU_count=4,TP=4,Agent_runs=3,session_seconds=10000),
                 template_changes=['External human grant insertion','Cell IDs from final bytes','Metadata title and explicit frozen machine shape'],
                 production_source_changed=False,SaveKernel=0,status='SEALED_NOT_DISPATCHED',
                 quota_is_historical_at_build=True,live_conflict_quota_slug_recheck_required=True)
        save(directory/'BUILD.json',row);records.append(row)
    save(HERE/'OUTER_EXECUTION_MANIFEST.json',dict(source_commit='f8b63e9db3d97760d1798fe12dfd5139871dcdc0',
         execution_branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
         shared_production_members=len(build['payload_members']),shared_production_sha256=build['payload_sha256'],
         authorization_scope='Same unconsumed two-batch/six-session experiment, no extra retry',batches=records,
         dispatches=0,GPU_runtime_checks='NOT_RUN',conflict_gate='NOT_ESTABLISHED'))
    print(json.dumps(dict(outer_notebooks_sealed=2,shared_production_unchanged=True,SaveKernel=0)))

if __name__=='__main__':run()
