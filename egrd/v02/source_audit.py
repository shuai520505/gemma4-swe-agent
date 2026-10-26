"""Offline provenance checks; no SDK, model, Agent, package installation or network."""
import ast
import json
from pathlib import Path
import subprocess
import zipfile

from .context_audit import HERE, ROOT, ARCHIVE_REL, EXPECTED_ARCHIVE, sha

BASE='780f7620b051fd6c43ca0f19659a4994c36a4882'
PR32='a1dcc83acba369b5bf3960d2a4fae86dc997d97c'
WHEELS=ROOT.parent/'gemma4-swe-agent/artifacts/harness-v2/official-wheels'


def wheel_sources():
    pins=json.loads((ROOT/'meer/v01/OFFICIAL_SOURCE_PINS.json').read_bytes())
    sources={};wheels={}
    selected={
        'adk_submission-0.2.13-py3-none-any.whl':[
            'adk_submission/compiler.py','adk_submission/schema.py','adk_submission/resolvers/callbacks.py',
            'adk_submission/resolvers/tools.py'],
        'google_adk-1.36.1-py3-none-any.whl':[
            'google/adk/apps/compaction.py','google/adk/apps/_configs.py',
            'google/adk/flows/llm_flows/compaction.py','google/adk/flows/llm_flows/contents.py',
            'google/adk/models/lite_llm.py','google/adk/tools/skill_toolset.py'],
        'swegemma-0.2.11-py3-none-any.whl':['swegemma/harness/agent_runner.py','swegemma/config.py']}
    for filename,members in selected.items():
        path=WHEELS/filename;assert sha(path.read_bytes())==pins[filename]['sha256']
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            for name in members:
                raw=z.read(name);sources[name]=raw
                if name in pins[filename].get('members',{}):assert sha(raw)==pins[filename]['members'][name]['sha256']
        wheels[filename]=dict(sha256=sha(path.read_bytes()),members={n:dict(sha256=sha(sources[n]),lines=len(sources[n].splitlines())) for n in members})
    return sources,wheels


def audit():
    sources,wheels=wheel_sources()
    manifest=json.loads((ROOT/'meer/v01/gpu01/EXECUTION_MANIFEST.json').read_bytes())
    assert sha((ROOT/'meer/v01/gpu01/payload.zip').read_bytes())=='38170bc0d6684ea09097d106cb0a4fbcf5fbc67a0b7c061f139ae99bccc558b5'
    with zipfile.ZipFile(ROOT.parent/'private-evidence'/ARCHIVE_REL) as z,zipfile.ZipFile(ROOT/'meer/v01/gpu01/payload.zip') as payload:
        assert z.testzip() is None and sha((ROOT.parent/'private-evidence'/ARCHIVE_REL).read_bytes())==EXPECTED_ARCHIVE
        for n in payload.namelist():assert z.read('source/'+n)==payload.read(n),n
        assert json.loads(z.read('execution/MODEL_FILES.json'))==manifest['model']['files']
        native=[]
        historical=json.loads((ROOT/'meer/v01/gpu01/authorized02/SESSION_RESULTS.json').read_bytes())['sessions']
        for r in historical[3:]:
            prefix=f"execution/runs/{r['run']:02d}-{r['instance_id']}-{r['arm']}/"
            raw=z.read(prefix+'official_result.json');xml=z.read(prefix+'verifier/phase2.junit.xml')
            assert sha(raw)==r['TaskResult_sha256'] and sha(xml)==r['JUnit_sha256']
            native.append(dict(run=r['run'],arm=r['arm'],resolved=json.loads(raw)['resolved'],
                TaskResult_sha256=sha(raw),JUnit_sha256=sha(xml)))
        registered=json.loads(payload.read('gpu_registration.json'))['files']
        assert len(registered)==205
        assert set(registered)==set(payload.namelist())-{'gpu_registration.json'}
        for name,digest in registered.items():assert sha(payload.read(name))==digest,name
        payload_count=len(payload.namelist())
    frozen={}
    for n in ['harness_v2/context_budget.py','harness_v2/official.py','s1/guard.py','s1/config.py',
              'meer/v01/gpu01/worker.py','meer/v01/gpu01/session.py',
              'u_re/v01/experiments/action_priority_01/real_gemma_abba01/worker.py',
              'meer/v01/GPU_EXPERIMENT_LOCK.json','meer/v01/CANDIDATE_MANIFEST.json']:
        raw=(ROOT/n).read_bytes();original=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT)
        assert raw==original,n
        frozen[n]=dict(sha256=sha(raw),lines=len(raw.splitlines()))
    for arm,row in manifest['arms'].items():
        path=ROOT/f'meer/v01/submission_{arm}.zip';assert sha(path.read_bytes())==row['ZIP_sha256']
        with zipfile.ZipFile(path) as candidate:assert candidate.testzip() is None
    prior=ROOT.parent/'gemma4-egrd-v01'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=prior,text=True).strip()==PR32
    prior_manifest=json.loads((prior/'egrd/v01/INTEGRITY_MANIFEST.json').read_bytes())
    old={}
    for name in ['FAILURE_AUTOPSY.md','ARCHITECTURE_DECISION.md','BASELINE_AUDIT.md','TRAJECTORY_DATASET.json','EVIDENCE_MANIFEST.json']:
        raw=(prior/'egrd/v01'/name).read_bytes();assert sha(raw)==prior_manifest['files'][name]['sha256']
        old[name]=sha(raw)
    guide=ROOT.parent/'official-inputs/HARNESS_README.md'
    assert sha(guide.read_bytes())==json.loads((ROOT/'meer/v01/OFFICIAL_SOURCE_PINS.json').read_bytes())['HARNESS_README.md']['sha256']
    # AST confirms the actually adapted evaluator does not supply a compaction
    # option. The differently named s1.worker is not this execution entry.
    tree=ast.parse((ROOT/'u_re/v01/experiments/action_priority_01/real_gemma_abba01/worker.py').read_text())
    configs=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='EvalConfig']
    assert len(configs)==1 and 'events_compaction_config' not in [k.arg for k in configs[0].keywords]
    missing=[dict(source='Exact local Gemma tokenizer.json + chat_template.jinja',status='UNAVAILABLE',
                  limit='No exact per-message rendered token replay; archived aggregate serving-tokenizer counts remain verified'),
             dict(source='Current competition rules/data page body',status='UNAVAILABLE_WEB_READER_0_LINES',
                  limit='Pinned guide/wheel interface conclusions are not a guarantee about unseen private/current infrastructure'),
             dict(source='Official scripts/inference.py full evaluation-config loader',status='NOT_FOUND_LOCALLY',
                  limit='Do not claim competitor-configurable App compaction from a research EvalConfig option'),
             dict(source='Rejected final generation HTTP bodies',status='NOT_CAPTURED_BECAUSE_NOT_SENT',
                  limit='Exact guard counts exist but final per-message/component sizes remain null'),
             dict(source='Formal S0/Full/EGR per-task trajectories',status='NOT_AVAILABLE',
                  limit='No causal attribution of official score regression')]
    result=dict(PR33_base=BASE,PR32_source=PR32,PR31_frozen='f8b63e9db3d97760d1798fe12dfd5139871dcdc0',
        archive_sha256=EXPECTED_ARCHIVE,CRC_valid=True,shared_payload_members_verified=payload_count,
        registered_source_pins_verified=205,model_file_hashes_verified=8,native_outcomes=native,
        pinned_wheels=wheels,local_frozen_source=frozen,PR32_derived_source_hashes=old,
        PR32_scope='Existing26-session/784-action audit verified by source hashes; not independently re-reviewed in full this round',
        guide_sha256=sha(guide.read_bytes()),compaction_keyword_absent_in_actual_research_worker=True,
        exact_component_tokenizer_replay=False,missing_sources=missing,
        operations=dict(Notebook_SaveKernel=0,Agent_sessions=0,GPU_inference=0,formal_submissions=0,package_installs=0))
    path=HERE/'SOURCE_PROVENANCE.json';raw=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    if path.exists() and path.read_bytes()!=raw:raise ValueError('Provenance changed; preserve and investigate')
    if not path.exists():path.write_bytes(raw)
    print(json.dumps(dict(wheels_verified=3,source_members=payload_count,real_requests_audited=40,new_model_requests=0)))
    return result


if __name__=='__main__':audit()
