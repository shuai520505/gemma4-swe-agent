"""Offline private archive verification and safe measured HTTP summaries."""
import json
from pathlib import Path
import zipfile
from .prepare import HERE,PRIVATE,sha,write


def lines(body):
    rows=[]
    for line in body.splitlines():
        try:rows.append(json.loads(line))
        except ValueError:break
    return rows


def transport(rows):
    requests=[r for r in rows if r['kind']=='http_request']
    replies=[r for r in rows if r['kind']=='http_response']
    usage=[];tools=[];finish=[]
    for r in replies:
        body=r['body'];u=body.get('usage')
        if isinstance(u,dict):usage.append(u)
        for choice in body.get('choices') or []:
            finish.append(choice.get('finish_reason'))
            tools.extend(choice.get('message',{}).get('tool_calls') or [])
    totals={k:sum(u[k] for u in usage if type(u.get(k)) is int) if any(type(u.get(k)) is int for u in usage) else None
            for k in ('prompt_tokens','completion_tokens','total_tokens')}
    return dict(requests=len(requests),responses=len(replies),HTTP_statuses=[r['status'] for r in replies],
        observed_response_usage=totals,usage_complete=bool(requests) and len(replies)==len(requests)==len(usage) and all(
            all(type(u.get(k)) is int for k in totals) for u in usage),
        received_HTTP_latency_seconds=sum(r['elapsed_seconds'] for r in replies) if replies else None,
        finish_reasons=finish,actual_emitted_tool_calls=len(tools),
        tool_names=[t.get('function',{}).get('name') for t in tools],
        reasoning_tokens=[u.get('completion_tokens_details',{}).get('reasoning_tokens') if isinstance(u.get('completion_tokens_details'),dict) else None for u in usage])


def run(path):
    path=Path(path);build=json.loads((HERE/'BUILD.json').read_bytes())
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        names=set(z.namelist());manifest=json.loads(z.read('evidence_manifest.json'))
        for name,row in manifest.items():
            body=z.read(name);assert len(body)==row['bytes'] and sha(body)==row['sha256'],name
        for name,digest in build['members'].items():assert sha(z.read('source/'+name))==digest,name
        root=PRIVATE/'verified-output';root.mkdir(exist_ok=False)
        for name in names:
            p=Path(name);assert not p.is_absolute() and '..' not in p.parts
        z.extractall(root)
    summaries={}
    for arm in ('A','B'):
        folder=root/'execution'/arm
        wire=folder/'model_transport/http_wire.jsonl'
        rows=lines(wire.read_bytes()) if wire.exists() else []
        item=dict(status='STARTED' if rows else 'NOT_RUN',transport=transport(rows))
        for name in ('SESSION_RESULT.json','AGENT_RESULT.json','COMPILED_CONFIGURATION.json','WORKER_EXCEPTION.json','audit_result.json','AGENT_CLEANUP.json'):
            if (folder/name).exists():item[name]=json.loads((folder/name).read_bytes())
        summaries[arm]=item
    record=dict(archive_sha256=sha(path.read_bytes()),archive_bytes=path.stat().st_size,
        manifest_files=len(manifest),source_files=len(build['members']),all_manifest_and_source_hashes_verified=True,
        extract_root=str(root),arms=summaries)
    write(PRIVATE/'VERIFIED_PRIVATE_RESULTS.json',record)
    print('Verified archive:',record['archive_sha256'],'manifest files:',len(manifest))
    for arm,item in summaries.items():
        print(arm,item['status'],json.dumps(item['transport']))
    return record


if __name__=='__main__':
    import sys
    run(sys.argv[1])
