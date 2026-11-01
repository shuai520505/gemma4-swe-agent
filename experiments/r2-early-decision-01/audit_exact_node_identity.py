"""Check real recorded JUnit identities without altering any recorded outcome."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from independent_exact_evaluator import canonical,BARE_NODES_MODULES
D=Path(__file__).resolve().parent
trusted=json.loads((D/'TRUSTED_TEST_SPEC.private.json').read_bytes());rows=[]
for task in trusted:
    files=list((D/'cpu-output-v4').rglob(task['instance_id']+'/native-junit-0.xml'))
    assert len(files)==1,(task['instance_id'],files)
    raw=files[0].read_bytes();root=ET.fromstring(raw);index={}
    for tc in root.findall('.//testcase'):
        key=tc.get('classname','')+'::'+tc.get('name','')
        index.setdefault(key,[]).append(next((s for s in ('failure','error','skipped') if tc.find(s) is not None),'pass'))
    nodes=[]
    for role in ('FAIL_TO_PASS','PASS_TO_PASS'):
        for req in task[role]:
            short=req.split('::')[-1]
            if '[' in short and not short.endswith(']'):
                nodes.append(dict(required=req,role=role,identity='UNKNOWN_MALFORMED',outcomes=None));continue
            key=canonical(req,BARE_NODES_MODULES.get(task['instance_id']));values=index.get(key,[])
            if key and not values and '[' not in short:
                values=[o for k,v in index.items() if k.startswith(key+'[') for o in v]
            nodes.append(dict(required=req,role=role,identity='FOUND' if values else 'MISSING',outcomes=values))
    rows.append(dict(task=task['instance_id'],junit_sha256=hashlib.sha256(raw).hexdigest(),nodes=nodes))
result=dict(classification='CPU_RECORDED_IDENTITY_AUDIT_NOT_REPAIR_SUCCESS',
    status='PASS_IDENTITY_COVERAGE_WITH_DECLARED_UNKNOWN' if all(n['identity']!='MISSING' for r in rows for n in r['nodes']) else 'BLOCKED_MISSING_IDENTITIES',
    recorded_outcomes_changed=False,rows=rows)
(D/'EXACT_NODE_IDENTITY_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],tasks=len(rows),missing=[(r['task'],n['required']) for r in rows for n in r['nodes'] if n['identity']=='MISSING'])))
