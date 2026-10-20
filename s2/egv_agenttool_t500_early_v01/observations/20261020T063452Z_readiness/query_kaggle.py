"""One read-only snapshot. Never saves, starts, cancels, or submits a kernel."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import importlib.metadata
import inspect
import json
from pathlib import Path
from urllib.parse import urlsplit
import requests

HERE = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, default=str) + '\n', encoding='utf-8')


original_send = requests.Session.send


def bounded_send(self, request, **kwargs):
    kwargs.setdefault('timeout', 30)
    response = original_send(self, request, **kwargs)
    # Keep response bodies, but never persist authentication headers or cookies.
    path = urlsplit(request.url).path
    if any(s in path.lower() for s in ('quota', 'submissions')):
        try:
            body = response.json()
        except ValueError:
            body = response.text
        save('wire_' + path.rstrip('/').split('/')[-1] + '.json', {
            'queried_at_utc': now(), 'method': request.method, 'path': path,
            'http_status': response.status_code, 'response': body,
        })
    return response


requests.Session.send = bounded_send
from kaggle import api
from kagglesdk.kernels.services.kernels_api_service import KernelsApiClient
from kagglesdk.kernels.types import kernels_api_service as types


def dictionary(obj):
    return obj.to_dict(ignore_defaults=False)


def query(label, function):
    result = {'started_at_utc': now()}
    try:
        result.update(ok=True, result=function())
    except Exception as exc:
        result.update(ok=False, exception_type=type(exc).__name__, error=str(exc))
    result['finished_at_utc'] = now()
    save(label + '.json', result)
    return result


def quota():
    value = api.quota_view()
    # SDK formatted Duration strings have previously been malformed; retain
    # underlying typed fields as well as formatted SDK/wire responses.
    return {'sdk': dictionary(value), 'typed_gpu_fields': {
        name: {'repr': repr(getattr(value.gpu_quota, name)),
               'type': type(getattr(value.gpu_quota, name)).__name__}
        for name in ('total', 'used', 'reserved') if hasattr(value.gpu_quota, name)
    }, 'gpu_object_repr': repr(vars(value.gpu_quota))}


def inventory():
    records = []
    pages = 0
    for page in range(1, 11):
        batch = api.kernels_list(mine=True, page=page, page_size=100)
        pages += 1
        records.extend(dictionary(x) for x in batch or [])
        if not batch or len(batch) < 100:
            return {'records': records, 'pages': pages, 'pagination_exhausted': True}
    return {'records': records, 'pages': pages, 'pagination_exhausted': False}


if __name__ == '__main__':
    save('sdk_surface.json', {
        'queried_at_utc': now(),
        'versions': {name: importlib.metadata.version(name) for name in ('kaggle', 'kagglesdk')},
        'read_write_endpoint_names': [n for n in dir(KernelsApiClient) if not n.startswith('_')],
        'quota_type_source': inspect.getsource(types.ApiAcceleratorQuota),
        'session_request_fields': inspect.getsource(types.ApiSaveKernelRequest)[:24000],
        'status_scope': 'Latest saved kernel session only; not an account-wide live interactive-session inventory.',
    })
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            'quota_raw': executor.submit(query, 'quota_raw', quota),
            'submissions_raw': executor.submit(query, 'submissions_raw', lambda: [
                dictionary(row) for row in api.competition_submissions('gemma-4-developer-agent')]),
            'notebooks_raw': executor.submit(query, 'notebooks_raw', inventory),
        }
        results = {name: future.result() for name, future in futures.items()}
    inventory_result = results['notebooks_raw']
    if inventory_result['ok']:
        records = inventory_result['result']['records']
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {r['ref']: executor.submit(query, 'status_' + r['slug'],
                lambda ref=r['ref']: dictionary(api.kernels_status(ref))) for r in records}
            statuses = {ref: f.result() for ref, f in futures.items()}
        save('notebook_statuses.json', statuses)
    for label, value in results.items():
        if label == 'submissions_raw' and value['ok']:
            print(label, json.dumps([x for x in value['result'] if str(x.get('ref')) in ('57402336', '57261002')], default=str))
        elif label == 'notebooks_raw' and value['ok']:
            print(label, len(value['result']['records']), 'pagination_exhausted', value['result']['pagination_exhausted'])
        else:
            print(label, json.dumps(value, default=str))
