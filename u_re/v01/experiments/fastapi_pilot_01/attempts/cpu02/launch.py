"""Requires a separate trusted human CPU02 grant; no implicit execution mode."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess

from .dispatch import Controller,checked_authorization,checked_config,SLUG
from .prepare import HERE,PILOT,ROOT


def validate_local():
    spec=json.loads((HERE/'BUILD_FREEZE.json').read_bytes());checked_config(spec)
    nb=(HERE/'notebook/study.ipynb').read_bytes();meta=(HERE/'notebook/kernel-metadata.json').read_bytes()
    assert hashlib.sha256(nb).hexdigest()==spec['Notebook_sha256']
    assert hashlib.sha256(meta).hexdigest()==spec['metadata_sha256']
    assert hashlib.sha256(json.dumps(json.loads(nb)).encode()).hexdigest()==spec['wire_sha256']
    assert hashlib.sha256((PILOT/'SELECTION_PROTOCOL.json').read_bytes()).hexdigest()==spec['selection_protocol_sha256']
    for name,version in spec['sdk_versions'].items():assert importlib.metadata.version(name)==version,'SDK drift'
    import inspect
    from kagglesdk.kaggle_http_client import KaggleHttpClient
    from kagglesdk.kernels.services.kernels_api_service import KernelsApiClient
    audit=json.loads((HERE/'evidence/SDK_RETRY_AUDIT.json').read_bytes())
    assert hashlib.sha256(inspect.getsource(KaggleHttpClient.call).encode()).hexdigest()==audit['SDK_call_source_sha256']
    assert hashlib.sha256(inspect.getsource(KernelsApiClient.save_kernel).encode()).hexdigest()==audit['SDK_save_method_sha256']
    pins=json.loads((PILOT/'CANDIDATE_INTEGRITY.json').read_bytes())['candidates']
    for arm,pin in pins.items():assert hashlib.sha256((ROOT/'u_re/v01'/('submission_'+arm+'.zip')).read_bytes()).hexdigest()==pin['zip_sha256']
    return spec


def request_for_build():
    from kagglesdk.kernels.types.kernels_api_service import ApiSaveKernelRequest
    meta=json.loads((HERE/'notebook/kernel-metadata.json').read_bytes())
    req=ApiSaveKernelRequest();req.slug=SLUG;req.new_title=meta['title']
    req.text=json.dumps(json.loads((HERE/'notebook/study.ipynb').read_bytes()))
    req.language='python';req.kernel_type='notebook';req.is_private=True
    req.enable_gpu=False;req.enable_tpu=False;req.enable_internet=False;req.model_data_sources=[]
    req.dataset_data_sources=meta['dataset_sources'];req.competition_data_sources=meta['competition_sources']
    req.docker_image=meta['docker_image'];req.docker_image_pinning_type=meta['docker_image_pinning_type'];req.session_timeout_seconds=7200
    return req


def launch(authorization_file=None,preflight_file=None):
    spec=validate_local()
    authorization=json.loads(Path(authorization_file).read_bytes()) if authorization_file else None
    checked_authorization(authorization,spec)  # Before any SDK authentication/network.
    seal=json.loads((HERE/'INTEGRITY_MANIFEST.json').read_bytes())
    for name,h in seal['files'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h,'CPU02 preparation-source drift: '+name
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert authorization.get('source_commit')==commit,'Grant must bind actual source commit'
    assert preflight_file,'Fresh CPU02 read-only gates are required'
    gates=json.loads(Path(preflight_file).read_bytes())
    age=(datetime.now(timezone.utc)-datetime.fromisoformat(gates['queried_at_utc'])).total_seconds()
    assert 0<=age<=600,'Read-only runtime identity/collision snapshot stale'
    assert gates['identity_confirmed'] and gates['current_readonly_GO'] and gates['slug_conflict'] is False
    gates.update(payload_integrity=True,source_commit=commit)
    # No helper creates authorization or refreshes credentials. Future operator
    # supplies trusted evidence only after a separate explicit human message.
    from kagglesdk.kaggle_env import get_access_token_from_env
    from kagglesdk.kaggle_client import KaggleClient
    token,_=get_access_token_from_env();assert token,'Existing credential required; no creation/refresh'
    request=request_for_build();controller=Controller(HERE/'execution',spec)
    def submit():
        with KaggleClient(api_token=token,verbose=False) as client:
            return client.kernels.kernels_api_client.save_kernel(request)
    result=controller.execute(authorization,gates,submit)
    print(json.dumps(dict(state=controller.journal.states()[-1],accepted_version=result.version_number or None)))
    if result.version_number and result.version_number!=1:
        raise RuntimeError('Accepted unexpected existing-resource version: integrity STOP,never resave')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorization');parser.add_argument('--preflight');args=parser.parse_args()
    launch(args.authorization,args.preflight)
