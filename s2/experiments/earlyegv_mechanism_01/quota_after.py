"""One post-run raw quota query; no SDK-formatted duration arithmetic."""
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import re
import requests

HERE = Path(__file__).resolve().parent
original = requests.Session.send


def send(self, request, **kwargs):
    kwargs.setdefault('timeout', 30)
    response = original(self, request, **kwargs)
    if request.url.rstrip('/').endswith('/GetAcceleratorQuotaStatistics'):
        raw = dict(queried_at_utc=datetime.now(timezone.utc).isoformat(),http_status=response.status_code,response=response.json())
        with (HERE / 'GPU_QUOTA_AFTER_RAW.json').open('x',encoding='utf-8') as file:
            json.dump(raw,file,indent=2)
    return response


requests.Session.send = send
from kaggle import api


def seconds(value):
    assert re.fullmatch(r'\d+(?:\.\d{1,9})?s',value)
    return Decimal(value[:-1])


if __name__ == '__main__':
    api.quota_view()
    raw = json.loads((HERE / 'GPU_QUOTA_AFTER_RAW.json').read_text(encoding='utf-8'))
    q = raw['response']['gpuQuota']
    before = json.loads((HERE / 'GPU_QUOTA_BEFORE.json').read_text(encoding='utf-8'))
    used, reserved, total = [seconds(q[k]) for k in ('timeUsed','timeReserved','totalTimeAllowed')]
    delta = used - Decimal(before['used_seconds'])
    result = dict(queried_at_utc=raw['queried_at_utc'],raw=q,total_seconds=str(total),
        used_seconds=str(used),reserved_seconds=str(reserved),remaining_seconds=str(total-used-reserved),
        account_used_delta_reported_seconds=str(delta),
        accounting_settled=reserved==0 and delta>=0,
        attribution='Account aggregate delta, not a request-level invoice or isolated per-arm charge. Cannot rule out unrelated interactive-account usage solely from saved-session inventory.',
        units='Reported protobuf Duration seconds; SDK .seconds formatting is not used.')
    with (HERE / 'GPU_QUOTA_AFTER.json').open('x',encoding='utf-8') as handle:
        json.dump(result,handle,indent=2)
    print(json.dumps(result,indent=2))
