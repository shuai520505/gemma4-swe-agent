"""Bind historical S0 and prior development evidence without rebuilding either."""
import hashlib
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIVATE=ROOT.parent/'private-evidence/egrd_v031'
PRIOR_PRIVATE=Path('C:/Users/HP/.codex/private-evidence/egrd_v03')
REF='wudangdexiaodoashi/egrd-v031-evidence-to-patch-cpu'
S0_SHA='3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf8',newline='\n')


def arm_input(original,receipt,arm):
    assert arm in ('A','B')
    if arm=='A':return original
    return original+'\n\n<EGRD_DEVELOPMENT_OBSERVATION>\n'+json.dumps(receipt,sort_keys=True,separators=(',',':'))+'\n</EGRD_DEVELOPMENT_OBSERVATION>'


def freeze():
    manifest=json.loads((ROOT/'candidates/s0/manifest.json').read_bytes())
    integrity=json.loads((ROOT/'s1/frozen_integrity.json').read_bytes())
    package=(ROOT/'candidates/s0/submission.zip').read_bytes()
    assert sha(package)==manifest['zip_sha256']==S0_SHA
    # Compare the independently recorded historical manifest bytes as well.
    assert sha((ROOT/'candidates/s0/manifest.json').read_bytes())=='3064d8e10b79ac4430ebaba586f5483f65228cb2026cb890760d877b3338b45c'
    with zipfile.ZipFile(ROOT/'candidates/s0/submission.zip') as z:
        assert z.testzip() is None
        members={n:sha(z.read(n)) for n in z.namelist()}
        assert members==manifest['source_hashes']
        for n,h in members.items():assert sha((ROOT/'candidates/s0/submission'/n).read_bytes())==h
    score=json.loads((ROOT/'s1/results/s0-score-observation.json').read_bytes())
    assert score['submission_id']==57261002 and score['public_score']==0.13 and score['status']=='COMPLETE'
    task=json.loads((PRIVATE/'original_task.json').read_bytes())
    previous=json.loads((ROOT/'egrd/v03/TASK_REPRODUCTIONS.json').read_bytes())
    original=next(r for r in previous['records'] if r['instance_id']==task['instance_id'])
    assert sha(task['problem_statement'].encode())==original['issue_sha256']
    assert task['base_commit']==original['base_commit']=='60a7bd89860e504c0c33b02c78edcac87f6d1b5a'
    archive=PRIOR_PRIVATE/'output-v1/egrd-v03-cpu-v1.zip'
    assert sha(archive.read_bytes())==previous['raw_archive_sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        raw=json.loads(z.read('results/tasks/django__django-16333/RESULT.json'))
        assert sha(z.read('results/tasks/django__django-16333/RESULT.json'))==original['raw_result_sha256']
        receipt=raw['probe'];assert receipt['controls_passed'] and receipt['phase']=='TARGET'
        assert len(receipt['checks'])==4 and sum(c['passed'] for c in receipt['checks'])==3
        target=receipt['checks'][-1]
        assert target['expected']==1 and target['actual']==0 and not target['passed']
        assert raw['source_tree_before']==raw['source_tree_after']==original['source_tree_before']
    lock={k:original[k] for k in ('instance_id','repo','base_commit','issue_sha256','snapshot_sha256',
        'probe_sha256','requirements_sha256','source_tree_before','probe_receipt_sha256')}
    lock.update(split='DEVELOPMENT_ONLY',prior_Notebook_id=141004018,prior_Notebook_version=1,
        prior_raw_archive_sha256=sha(archive.read_bytes()),source_unchanged=True,prior_cleanup=True,
        prior_positive_controls_passed=3,prior_executed_target_assertions=1,
        original_issue_bytes=len(task['problem_statement'].encode()),
        issue_source='SWE-bench Verified pinned Parquet metadata projection; only instance_id/repo/base_commit/problem_statement read',
        source_revision='78f471bf655a3137b2e8a75af1501690ec009ec3',
        parquet_sha256='030cfd7f2a704c4c0226e7f104c725a3b41230b1d3517f9c915ad7ea5be3fa25',
        independently_verified_original_issue=True,reference_columns_read=False)
    write(HERE/'TASK_IDENTITY_LOCK.json',lock)
    safe=dict(schema='EGRD_SOURCE_BOUND_FAILURE_OBSERVATION_V1',task_id=task['instance_id'],
        source_base_commit=task['base_commit'],source_snapshot_sha256=lock['snapshot_sha256'],
        tested_source_tree_sha256=lock['source_tree_before'],issue_sha256=lock['issue_sha256'],
        diagnostic_program_sha256=lock['probe_sha256'],original_receipt_sha256=lock['probe_receipt_sha256'],
        environment_requirements_sha256=lock['requirements_sha256'],
        observation='In this scoped check, a valid creation form did not persist the selected ManyToMany relation after save.',
        expected_related_count=1,observed_related_count=0,execution_returncode=1,
        actual_checks_executed=4,positive_control_assertions_passed=3,target_assertions_failed=1,
        controls=['Plain ModelForm validity','Plain ModelForm persists selected relation','Creation form validity'],
        target_exception='AssertionError',source_unchanged=True,
        limitations=['Owned development probe using built-in User.groups, not the complete custom-user application.',
            'No complete repair correctness or official evaluation outcome is established.',
            'Nonfatal sitecustomize/wrapt startup warning retained in original evidence.'],
        official_native_resolved=None,canonical_swebench_resolved=None)
    write(HERE/'EVIDENCE_RECEIPT.json',safe)
    inputs={arm:arm_input(task['problem_statement'],safe,arm) for arm in ('A','B')}
    for arm,text in inputs.items():(PRIVATE/f'input_{arm}.txt').write_bytes(text.encode())
    agent=dict(candidate='ORIGINAL_S0',original_package_path='candidates/s0/submission.zip',
        zip_sha256=S0_SHA,zip_bytes=len(package),members=members,
        official_submission_id=57261002,observed_official_score=0.13,
        historical_manifest_sha256=sha((ROOT/'candidates/s0/manifest.json').read_bytes()),
        frozen_integrity_record_sha256=sha((ROOT/'s1/frozen_integrity.json').read_bytes()),
        same_package_both_arms=True,package_rebuilt=False,
        evaluation=manifest['evaluation'],generation_origin='Exact S0 YAML plus pinned official Compiler defaults; no later EGR overrides',
        expected_defaults=dict(max_output_tokens=16384,thinking_config=dict(thinking_budget=4096)),
        seed_in_original_YAML=None,include_thoughts_in_original_YAML=None,
        research_context_guard_in_package=False,
        later_research_configuration_not_assumed=True,full_compiler_evidence='CPU_TEST_RESULTS.json')
    write(HERE/'S0_AGENT_LOCK.json',agent)
    write(PRIVATE/'INPUT_BUILD.json',dict(original_issue_sha256=lock['issue_sha256'],
        receipt_file_sha256=sha((HERE/'EVIDENCE_RECEIPT.json').read_bytes()),
        inputs={arm:dict(sha256=sha(text.encode()),bytes=len(text.encode())) for arm,text in inputs.items()},
        supplement_bytes=len(inputs['B'].encode())-len(inputs['A'].encode()),token_overhead=None,
        original_issue_contains_reporter_causal_claim=True,additional_hints_or_answers=False))
    print('Frozen S0 bytes and original Issue verified; source-bound observation generated; no GPU lock asserted.')


if __name__=='__main__':freeze()
