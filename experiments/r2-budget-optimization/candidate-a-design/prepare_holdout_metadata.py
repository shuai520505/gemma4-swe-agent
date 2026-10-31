"""Conservative local exposure reconstruction; no reference repair/outcome selection."""
import hashlib,json,os,re
from collections import Counter,defaultdict
from pathlib import Path

OUT=Path(__file__).resolve().parent/'holdout-preparation'
PROJECT=Path('D:/kaggle/Gemma 4 Developer Agent Competition')
ROOT=Path(__file__).resolve().parents[3]
sha=lambda b:hashlib.sha256(b).hexdigest()
ID=re.compile(r'(?<![A-Za-z0-9])(?:fastapi|requests|rich|httpx)_\d+(?![A-Za-z0-9])|(?:django__django|pydata__xarray|pytest-dev__pytest)-\d+')
PRUNE={'.git','site-packages','node_modules','__pycache__','.venv','venv','sdk-env','snapshots','repositories','repos','base','selected-base','selected-r2','official-inputs','external-sources','official-current','official-source','official-sources','wheels','models'}
RECORD_NAMES=re.compile(r'EXPOSURE|EXCLUSION|ADMISSION.*LEDGER|SCREENING.*LEDGER|SELECTED_TASKS|TASK_IDENTITY|IDENTITY_LOCK|ABBA_RESULTS|PAIR_RESULTS|PAIRED_ANALYSIS|TASK_POOL_FREEZE|BATCH_\d+_EXECUTION|GPU_EXECUTION_MANIFEST',re.I)
SKIP_KEYS=re.compile(r'patch|reference|solution|gold|test|trajectory|trace|response|request|problem_statement|hints|stdout|stderr|resolved|score|success|error|failure|metric|token|seconds|duration|remaining|eligible|ranked_pool|source_pool|candidate_pool|all_tasks|metadata_rows',re.I)

def ids(v):
    if isinstance(v,str):return set(ID.findall(v))
    if isinstance(v,list):return set().union(*(ids(x) for x in v)) if v else set()
    if isinstance(v,dict):return set().union(*(ids(x) for k,x in v.items() if not SKIP_KEYS.search(k))) if v else set()
    return set()

def consume(v,name):
    if 'TASK_IDENTITY_LOCK' in name.upper() and isinstance(v,dict) and 'all129' in v:
        # Pool registration is not exposure. Only the historically prospective subset was reserved.
        return ids(v.get('prospective_ids',[]))
    if 'TASK_POOL_FREEZE' in name.upper():
        return set().union(*(ids(x) for k,x in v.items() if re.search('excluded|exposure|used|reserved',k,re.I))) if isinstance(v,dict) else set()
    return ids(v)

def main():
    OUT.mkdir(exist_ok=True)
    dataset=PROJECT/'official-inputs/tasks.jsonl'
    # Parse rows only to project the allowed public identity fields. Repair/test/hints values are never inspected, copied, hashed separately, or used in ranking.
    rows=[]
    for line in dataset.read_text(encoding='utf8').splitlines():
        if not line.strip():continue
        r=json.loads(line)
        rows.append({k:r[k] for k in ('instance_id','repo','base_commit','problem_statement')})
    pool={r['instance_id']:dict(instance_id=r['instance_id'],repo=r['repo'],base_commit=r['base_commit'],issue_sha256=sha(r['problem_statement'].encode())) for r in rows}
    roots=[PROJECT/n for n in ('gemma4-egrd-v01','gemma4-s1-score-optimization','gemma4-swe-agent','gemma4-u-re-v01','private-evidence')]
    roots += [ROOT/'work/gemma-pair-01/source',ROOT/'work/gemma-r12-01',ROOT/'outputs']
    evidence=[];excluded=defaultdict(set);errors=[];inventory=[];seen=set()
    for root in roots:
        if not root.exists():errors.append({'path':str(root),'error':'ROOT_MISSING'});continue
        for dp,dirs,files in os.walk(root):
            dirs[:]=[n for n in dirs if n not in PRUNE and not n.startswith('swegemma_sandbox')]
            d=Path(dp)
            # Actual/reserved task-labelled execution directories count conservatively, unlike identity-only pool rows.
            found=set(ID.findall(d.name))
            if found:
                e={'source':str(d),'kind':'TASK_LABELLED_DIRECTORY_CONSERVATIVE','task_ids':sorted(found)}
                idx=len(evidence);evidence.append(e)
                for x in found:excluded[x].add(idx)
            for name in files:
                if not name.endswith('.json') or not RECORD_NAMES.search(name):continue
                p=d/name
                if p in seen:continue
                seen.add(p)
                try:
                    raw=p.read_bytes()
                    if len(raw)>12_000_000:errors.append({'path':str(p),'error':'OVERSIZE_NOT_READ'});continue
                    data=json.loads(raw)
                    found=consume(data,name)
                    inventory.append({'path':str(p),'sha256':sha(raw),'bytes':len(raw),'identified_ids':len(found)})
                    if found:
                        kind='HISTORICAL_REGISTRY_IDENTITY_FIELDS_ONLY'
                        if re.search('EXPOSURE|EXCLUSION|POOL_FREEZE',name,re.I):kind='PRIOR_CONSERVATIVE_EXCLUSION_INCLUDES_RESERVED_UNCERTAIN'
                        e={'source':str(p),'sha256':sha(raw),'kind':kind,'task_ids':sorted(found)}
                        idx=len(evidence);evidence.append(e)
                        for x in found:excluded[x].add(idx)
                except Exception as exc:errors.append({'path':str(p),'error':type(exc).__name__})
    # Frozen known research identities, including different task ID conventions.
    known={'django__django-11964','pydata__xarray-6721','pytest-dev__pytest-5631','fastapi_9425','fastapi_14786'}
    idx=len(evidence);evidence.append({'source':'PR44 R12 and Action-First audited history','kind':'KNOWN_EXPOSED','task_ids':sorted(known)})
    for x in known:excluded[x].add(idx)
    # Exclude duplicate Issue/base identities even under another task ID.
    observed_keys={(pool[x]['repo'].lower(),pool[x]['base_commit'],pool[x]['issue_sha256']) for x in excluded if x in pool}
    for x,r in pool.items():
        if (r['repo'].lower(),r['base_commit'],r['issue_sha256']) in observed_keys and x not in excluded:
            idx=len(evidence);evidence.append({'source':'PUBLIC_METADATA_EQUIVALENCE','kind':'SAME_REPO_BASE_ISSUE_HASH','task_ids':[x]});excluded[x].add(idx)
    remaining=[r for x,r in pool.items() if x not in excluded]
    result={'status':'LOCAL_CORPUS_RECONSTRUCTED_NOT_GLOBAL_OMNISCIENCE','scope':'Available local project roots; identity fields and labelled directories only, no outcome/repair-based selection. Historical unknowns excluded conservatively. Metadata-only pool registration is not exposure. Sources outside available roots and deleted history remain UNKNOWN.',
        'dataset':str(dataset),'dataset_sha256':sha(dataset.read_bytes()),'public_development_count':len(pool),'official_hidden_count':None,
        'roots':[str(r) for r in roots],'inventory_records':len(inventory),'read_errors':errors,
        'excluded_ids':sorted(excluded),'excluded_public_count':len(set(pool)&set(excluded)),
        'remaining_count':len(remaining),'remaining_by_repo':dict(Counter(r['repo'] for r in remaining)),
        'remaining_identity_rows':sorted(remaining,key=lambda r:r['instance_id']),
        'interpretation':'Excluded does not mean actually run or issue-read: prior exclusions conservatively include reserved/planned/uncertain tasks. In particular the R12 exposure audit reserves the whole 129-task pool. Do not silently relax that historical policy to obtain a holdout.',
        'excluded':[dict(instance_id=x,identity=pool.get(x),evidence_indices=sorted(ix)) for x,ix in sorted(excluded.items())],
        'evidence':evidence,'inventory':inventory,
        'new_task_issue_text_displayed':False,'reference_repair_consumed':False,'task_outcome_used_for_selection':False}
    (OUT/'EXPOSURE_REGISTRY.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    (OUT/'PUBLIC_POOL_IDENTITIES.json').write_text(json.dumps({'source_sha256':result['dataset_sha256'],'rows':list(pool.values())},indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:result[k] for k in ('inventory_records','read_errors','excluded_public_count','remaining_count','remaining_by_repo','remaining_identity_rows')}))

if __name__=='__main__':main()
