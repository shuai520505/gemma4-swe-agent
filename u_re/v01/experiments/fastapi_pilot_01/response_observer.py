"""Non-masking HTTP response receipt for future host runs, never a retry policy."""
from datetime import datetime, timezone


def describe_response(response):
    record=dict(received_at_utc=datetime.now(timezone.utc).isoformat(),
                http_status=response.status_code,
                content_type=response.headers.get('Content-Type','').split(';')[0],
                response_bytes=len(response.content))
    try:
        value=response.json()
        # Do not copy arbitrary response bodies, headers, cookies or tokens.
        record['json_response']=True
        if isinstance(value,dict):
            for name in ('versionNumber','kernelId','status'):
                if isinstance(value.get(name),(str,int,bool)):record[name]=value[name]
    except ValueError:
        record['json_response']=False
    return record


def capture_response(path,response):
    """Best-effort evidence must never replace SDK response/error semantics."""
    import json
    try:
        with path.open('x',encoding='utf-8',newline='\n') as out:
            json.dump(describe_response(response),out,indent=2);out.write('\n')
        return True
    except (OSError,TypeError):
        return False
