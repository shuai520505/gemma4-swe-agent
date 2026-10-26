"""Public provenance and metadata projection only; never read reference patches."""
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess

import requests

from .cli_recovery import HERE, PRIVATE, ROOT, sha


def get(url, path):
    response=requests.get(url,proxies={'https':'http://127.0.0.1:7890'},timeout=120)
    response.raise_for_status()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(response.content)
    return response.content


def investigate():
    directory=PRIVATE/'external-sources'
    directory.mkdir(parents=True,exist_ok=False)
    identity='SWE-bench/SWE-bench_Verified'
    meta=json.loads(get('https://huggingface.co/api/datasets/'+identity,directory/'hf_metadata.json'))
    revision=meta['sha']
    readme=get(f'https://huggingface.co/datasets/{identity}/resolve/{revision}/README.md',directory/'README.md')
    files=[r['rfilename'] for r in meta['siblings'] if r['rfilename'].endswith('.parquet')]
    rows=[];digests={}
    import pyarrow.parquet as pq
    for name in files:
        path=directory/Path(name).name
        raw=get(f'https://huggingface.co/datasets/{identity}/resolve/{revision}/{name}',path)
        digests[name]=dict(sha256=sha(raw),bytes=len(raw))
        # Explicit Parquet column projection. No patch, test_patch, solution,
        # hints, difficulty or outcome column is decoded/used to rank tasks.
        table=pq.read_table(path,columns=['instance_id','repo','base_commit','problem_statement'])
        for row in table.to_pylist():
            rows.append(dict(instance_id=row['instance_id'],repo=row['repo'],base_commit=row['base_commit'],
                             issue_sha256=sha(row['problem_statement'].encode())))
    tree=json.loads(get(f'https://huggingface.co/api/datasets/{identity}/tree/{revision}/data',
                        directory/'hf_file_metadata.json'))
    for item in tree:
        if item['path'] not in digests:continue
        expected=item.get('lfs',{}).get('oid') or item.get('lfs',{}).get('sha256')
        assert expected==digests[item['path']]['sha256']
        digests[item['path']].update(publisher_LFS_sha256=expected,publisher_hash_matches=True)
    assert all(r.get('publisher_hash_matches') for r in digests.values())
    historical=json.loads((ROOT/'egrd/v022/TASK_POOL_LOCK.json').read_bytes())
    old=historical['source_record_metadata']
    old_repos={r['repo'].lower() for r in old}
    exact={(r['repo'].lower(),r['base_commit'],r['issue_sha256']) for r in old}
    matches=[r['instance_id'] for r in rows if (r['repo'].lower(),r['base_commit'],r['issue_sha256']) in exact]
    # The first proposed external protocol uses repository disjointness. This
    # conservative gate is prospective; baseline/admission is still NOT_RUN.
    remaining=[r for r in rows if r['repo'].lower() not in old_repos]
    prefix='EGRD-V023-EXTERNAL-SWEBENCH:17:'
    remaining.sort(key=lambda r:(sha((prefix+r['instance_id']).encode()),r['instance_id']))
    if shutil.which('docker'):
        result=subprocess.run(['docker','info','--format','{{.ServerVersion}}'],capture_output=True,timeout=30)
        (directory/'docker.stdout').write_bytes(result.stdout)
        (directory/'docker.stderr').write_bytes(result.stderr)
        docker=dict(binary_present=True,daemon_reachable=result.returncode==0,returncode=result.returncode)
    else:docker=dict(binary_present=False,daemon_reachable=False)
    result=dict(classification='EXTERNAL_EVALUATION_ONLY',source='https://huggingface.co/datasets/'+identity,
        dataset=identity,revision=revision,access='public; no authentication supplied',
        readme_sha256=sha(readme),files=digests,task_count=len(rows),repositories=dict(Counter(r['repo'] for r in rows)),
        projected_columns=['instance_id','repo','base_commit','problem_statement (hash only)'],
        no_reference_patch_columns_read=True,official_native_compatible=False,
        exact_historical_identity_matches=matches,repository_disjoint_count=len(remaining),
        overlap_limit='Compared with original 129 metadata records; semantic aliases and model pretraining exposure are not proven absent',
        docker=docker,native_baselines_run=0,admitted_tasks=0,
        ranking_prefix=prefix,seed=17,max_future_CPU_baselines=16,selection='First two eligible in frozen order',
        ranked_metadata=remaining,
        status='SOURCE_METADATA_VERIFIED_EVALUATOR_EXECUTION_NOT_RUN')
    (HERE/'EXTERNAL_SOURCE_LOCK.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:result[k] for k in ('revision','task_count','repositories','repository_disjoint_count','docker')}))
    return result


if __name__=='__main__':investigate()
