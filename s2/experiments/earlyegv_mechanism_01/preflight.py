"""Read-only current API snapshot; no Notebook save or session creation."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
import requests

HERE = Path(__file__).resolve().parent
SLUG = 'wudangdexiaodoashi/gemma4-s2-earlyegv-mechanism-01'


def now():
    return datetime.now(timezone.utc).isoformat()


def emit(name, obj):
    with (HERE / name).open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + '\n')


send_original = requests.Session.send


def send(self, request, **kwargs):
    kwargs.setdefault('timeout', 30)
    response = send_original(self, request, **kwargs)
    endpoint = urlsplit(request.url).path.rsplit('/', 1)[-1]
    if endpoint in ('GetAcceleratorQuotaStatistics', 'ListSubmissions'):
        emit('RAW_' + endpoint + '.json', dict(queried_at_utc=now(), method=request.method,
             http_status=response.status_code, response=response.json()))
    return response


requests.Session.send = send
from kaggle import api


def duration(value):
    if not re.fullmatch(r'\d+(?:\.\d{1,9})?s', value):
        raise ValueError('Invalid raw protobuf Duration; no SDK string correction')
    return Decimal(value[:-1])


if __name__ == '__main__':
    started = now()
    api.quota_view()
    raw = json.loads((HERE / 'RAW_GetAcceleratorQuotaStatistics.json').read_text(encoding='utf-8'))
    q = raw['response']['gpuQuota']
    remaining = duration(q['totalTimeAllowed']) - duration(q['timeUsed']) - duration(q['timeReserved'])
    emit('GPU_QUOTA_BEFORE.json', dict(queried_at_utc=raw['queried_at_utc'], raw=q,
         total_seconds=str(duration(q['totalTimeAllowed'])), used_seconds=str(duration(q['timeUsed'])),
         reserved_seconds=str(duration(q['timeReserved'])), remaining_seconds=str(remaining),
         threshold_seconds=20600, passed=remaining >= 20600,
         units='Reported quota seconds from raw HTTP; not device-hours or guaranteed wall time.'))
    assert remaining >= 20600, 'GPU quota below frozen threshold'
    submissions = [r.to_dict(ignore_defaults=False) for r in api.competition_submissions('gemma-4-developer-agent')]
    emit('FORMAL_SCORE_STATUS.json', dict(queried_at_utc=now(), submissions=submissions, new_submission=False))
    inventory = []
    exhausted = False
    for page in range(1, 6):
        rows = api.kernels_list(mine=True, page=page, page_size=100)
        inventory.extend(r.to_dict(ignore_defaults=False) for r in rows or [])
        if not rows or len(rows) < 100:
            exhausted = True
            break
    emit('NOTEBOOK_INVENTORY_BEFORE.json', dict(queried_at_utc=now(), pagination_exhausted=exhausted, records=inventory))
    assert exhausted
    assert not any(r['ref'] == SLUG for r in inventory), 'Same execution Notebook already exists; do not resubmit'
    assert not any('earlyegv-mechanism-01' in r['ref'] for r in inventory), 'Potential duplicate execution'
    recent = inventory[:20]
    statuses = {}
    for row in recent:
        ref = row['ref']
        try:
            status = api.kernels_status(ref).to_dict(ignore_defaults=False)
            statuses[ref] = dict(queried_at_utc=now(), response=status)
        except Exception as exc:
            statuses[ref] = dict(queried_at_utc=now(), error=repr(exc))
            emit('RECENT_SESSION_STATUS_BEFORE.json', statuses)
            raise
        if status['status'] not in ('COMPLETE', 'ERROR'):
            emit('RECENT_SESSION_STATUS_BEFORE.json', statuses)
            raise RuntimeError('Observed non-terminal saved Notebook: ' + ref)
        time.sleep(.3)
    emit('RECENT_SESSION_STATUS_BEFORE.json', statuses)
    emit('GPU_RESOURCE_ADMISSION.json', dict(
        started_at_utc=started, finished_at_utc=now(), quota_passed=True,
        remaining_reported_seconds=str(remaining), no_observed_recent_saved_session_conflict=True,
        recent_saved_sessions_checked=len(statuses), duplicate_saved_execution=False,
        full_interactive_inventory_exposed_by_sdk=False,
        reservation_seconds=str(duration(q['timeReserved'])),
        live_machine_capacity='PLATFORM_ADMISSION_REQUIRED',
        requested_machine='NvidiaL4', required_devices='4 NVIDIA L4', requested_window_seconds=10000,
        machine_and_account_final_admission='One authorized SaveKernel request; accepted scheduling and in-container device/window checks before model startup. No alternate machine or retry.',
        authorization_source='Current user message explicitly authorizes exactly this two-task four-run experiment and one Notebook save/start request.',
        GPU_started=False, execution_submission_requests=0,
        platform_window_contract='CLI supports explicit session_timeout_seconds=10000; successful platform acceptance required, not inferred from an old Notebook.',
        limitations='Recent saved sessions terminal and no reserved quota; not a claim of exhaustive interactive-session absence. Platform admission must reject actual allocation conflict.'))
    print(json.dumps(dict(quota_remaining=str(remaining), recent_terminal=len(statuses), duplicate=False,
                         scores=[{k:r.get(k) for k in ('ref','status','publicScore','errorDescription')} for r in submissions]), indent=2))
