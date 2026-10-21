"""Bounded, read-only reconciliation of existing CPU02; never imports launcher."""
import ast
import base64
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HERE = Path(__file__).resolve().parent
CPU02 = HERE.parent
OWNER = 'wudangdexiaodoashi'
SLUG = 'gemma4-u-re-fastapi-pilot01-cpu02'
REF = OWNER + '/' + SLUG
ID = 140021966
ALLOWED = {'IntrospectToken', 'GetKernel', 'ListKernels',
           'GetKernelSessionStatus', 'ListKernelSessionOutput'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, default=str)
        f.write('\n')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def allowed_api(method, url, body):
    u = urlsplit(url)
    if method != 'POST' or u.scheme != 'https' or u.hostname != 'api.kaggle.com' or u.query:
        return False
    op = u.path.rsplit('/', 1)[-1]
    service = 'security.OAuthService' if op == 'IntrospectToken' else 'kernels.KernelsApiService'
    if u.path != '/v1/' + service + '/' + op:
        return False
    if op not in ALLOWED:
        return False
    if op in {'GetKernel', 'GetKernelSessionStatus', 'ListKernelSessionOutput'}:
        return (body.get('userName') == OWNER and body.get('kernelSlug') == SLUG
                and body.get('versionLabel', '1') == '1')
    if op == 'ListKernels':
        return body.get('user') == OWNER and body.get('pageSize', 0) <= 100
    return True


def safe_fields(meta):
    names = ('id', 'ref', 'author', 'slug', 'is_private', 'current_version_number',
             'language', 'kernel_type', 'enable_gpu', 'enable_tpu', 'enable_internet',
             'model_data_sources', 'machine_shape', 'docker_image', 'last_run_time')
    return {k: getattr(meta, '_' + k, None) for k in names}


def identity(value):
    """Independent raw fields + exact/semantic source + embedded payload, no coercion."""
    meta = safe_fields(value.metadata)
    source = value.blob.source
    spec = json.loads((CPU02 / 'BUILD_FREEZE.json').read_bytes())
    source_audit = dict(API_source_sha256=digest(source.encode()),
                        frozen_file_sha256=spec['Notebook_sha256'],
                        frozen_wire_sha256=spec['wire_sha256'],
                        exact_wire_match=digest(source.encode()) == spec['wire_sha256'],
                        exact_file_match=digest(source.encode()) == spec['Notebook_sha256'],
                        semantic_JSON_match=False, payload_sha256=None, payload_match=False)
    try:
        nb = json.loads(source)
        frozen = json.loads((CPU02 / 'notebook/study.ipynb').read_bytes())
        source_audit['semantic_JSON_match'] = nb == frozen
        first = nb['cells'][0]['source']
        first = ''.join(first) if isinstance(first, list) else first
        prefix = "payload=__import__('base64').b64decode("
        line = next(x for x in first.splitlines() if x.startswith(prefix))
        raw = base64.b64decode(ast.literal_eval(line[len(prefix):-1]), validate=True)
        source_audit['payload_sha256'] = digest(raw)
        source_audit['payload_match'] = digest(raw) == spec['payload_sha256']
    except (ValueError, KeyError, TypeError, StopIteration, SyntaxError):
        pass
    # Raw ref spelling is preserved, not silently replaced in evidence.
    ref = meta['ref']
    if isinstance(ref, str) and ref.startswith('https://www.kaggle.com/code/'):
        u = urlsplit(ref)
        canonical_ref = u.path.removeprefix('/code/').rstrip('/') if not u.query and not u.fragment else None
    else:
        canonical_ref = ref
    if ref == SLUG and meta['author'] == OWNER:
        canonical_ref = OWNER + '/' + ref
    conflict = ((meta['id'] not in (None, 0) and meta['id'] != ID)
                or (canonical_ref and canonical_ref != REF)
                or (meta['slug'] and meta['slug'] != SLUG))
    fields_ok = (not conflict and meta['id'] == ID and canonical_ref == REF
                 and meta['slug'] == SLUG and meta['author'] == OWNER and meta['current_version_number'] == 1
                 and meta['is_private'] is True and meta['kernel_type'] == 'notebook'
                 and meta['enable_gpu'] is False and meta['enable_tpu'] is False
                 and meta['enable_internet'] is False and meta['model_data_sources'] == [])
    content_ok = source_audit['payload_match'] and (source_audit['exact_wire_match']
                    or source_audit['exact_file_match'] or source_audit['semantic_JSON_match'])
    state = 'IDENTITY_MISMATCH' if conflict else 'IDENTITY_CONFIRMED' if fields_ok and content_ok else 'RESOURCE_FOUND_IDENTITY_PARTIAL'
    return dict(state=state, metadata=meta, canonical_ref_for_comparison=canonical_ref,
                source=source_audit, version_requested='1', checked_at_utc=utc())


class ReadGuard:
    def __init__(self, directory):
        self.directory = directory
        self.events = []
        self.urls = set()
        self.download_enabled = False

    def __enter__(self):
        self.original = requests.Session.send
        guard = self

        def send(session, req, **kw):
            is_download = req.method == 'GET' and req.url in guard.urls and guard.download_enabled
            body = json.loads(req.body or '{}') if req.method == 'POST' else {}
            if not is_download and not allowed_api(req.method, req.url, body):
                raise PermissionError('Non-whitelisted operation blocked before transport')
            if len(guard.events) >= 30:
                raise RuntimeError('Read-only request cap reached')
            op = 'download existing output' if is_download else urlsplit(req.url).path.rsplit('/', 1)[-1]
            record = dict(at_utc=utc(), operation=op, method=req.method, HTTP_status=None)
            guard.events.append(record)
            # No query/header/token/URL or arbitrary response body enters the journal.
            adapter = HTTPAdapter(max_retries=Retry(total=0, connect=0, read=0, status=0, redirect=0, other=0))
            session.mount('https://', adapter)
            kw.update(timeout=60, allow_redirects=False)
            try:
                r = guard.original(session, req, **kw)
                record.update(HTTP_status=r.status_code, content_type=r.headers.get('Content-Type', '').split(';')[0])
                return r
            except BaseException as e:
                record['exception_class'] = type(e).__name__
                raise
            finally:
                write(guard.directory / 'HTTP' / f'{len(guard.events):03d}.json', record)
        requests.Session.send = send
        return self

    def __exit__(self, *args):
        requests.Session.send = self.original


def run():
    evidence = HERE / 'evidence'
    evidence.mkdir(exist_ok=False)  # Explicit re-entry refusal, no overwritten query evidence.
    ledger = dict(started_at_utc=utc(), target=REF, Notebook_id=ID, version=1,
                  SaveKernel=0, reruns=0, GPU=0, Gemma=0, Agent=0, formal_submission=0)
    resource = dict(state='IDENTITY_UNKNOWN', metadata=None, source=None)
    status_record = dict(state='RUN_STATUS_UNKNOWN', official_status=None, failure_message=None)
    from kagglesdk.kaggle_creds import KaggleCredentials
    originals = {n: getattr(KaggleCredentials, n) for n in ('save', 'delete', 'generate_access_token', 'refresh_access_token')}
    def refuse(*a, **kw):
        raise PermissionError('Credential mutation forbidden')
    for n in originals:
        setattr(KaggleCredentials, n, refuse)
    capture = io.StringIO()
    with ReadGuard(evidence) as guard:
        try:
            with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
                from kaggle import api
            assert api.get_config_value('username') == OWNER, 'Account mismatch'
            ledger['account_confirmed'] = True
            from kagglesdk.kernels.types.kernels_api_service import (ApiGetKernelRequest,
                ApiGetKernelSessionStatusRequest, ApiListKernelSessionOutputRequest,
                ApiListKernelsRequest, KernelsListViewType, KernelsListSortType)
            with api.build_kaggle_client() as client:
                svc = client.kernels.kernels_api_client
                def get(label='1'):
                    q = ApiGetKernelRequest();q.user_name = OWNER;q.kernel_slug = SLUG
                    if label is not None:q.version_label = label
                    return svc.get_kernel(q)
                try:
                    value = get()
                except requests.HTTPError:
                    # No repeat of the same denied query; complete own profile fallback.
                    matched = [];seen = set();token = None;complete = False
                    for page in range(1, 6):
                        q = ApiListKernelsRequest();q.user = OWNER;q.group = KernelsListViewType.PROFILE
                        q.sort_by = KernelsListSortType.DATE_CREATED;q.page = page;q.page_size = 100
                        q.kernel_type = 'all';q.language = 'all';q.output_type = 'all';q.search = ''
                        if token:q.page_token = token
                        r = svc.list_kernels(q)
                        keys = {x.ref for x in r.kernels or []}
                        matched.extend(safe_fields(x) for x in r.kernels or [] if getattr(x, 'id', None) == ID)
                        new = keys - seen;seen |= keys
                        if not r.next_page_token and len(r.kernels or []) < 100:complete = True;break
                        if not new:break
                        token = r.next_page_token or None
                    ledger['list_fallback'] = dict(pages=page, visible_records=len(seen), complete=complete, ID_matches=matched)
                    if matched:
                        resource = dict(state='RESOURCE_FOUND_IDENTITY_PARTIAL', metadata=matched, source=None)
                    raise RuntimeError('Exact version/source unavailable; no status/output queries')
                resource = identity(value)
                write(evidence / 'RESOURCE_IDENTITY.json', resource)
                if resource['state'] != 'IDENTITY_CONFIRMED':
                    raise RuntimeError('Identity gate not satisfied; no status/output queries')
                # Keep only verified frozen source, never unrelated Notebook content.
                (evidence / 'platform_source.ipynb').write_bytes(value.blob.source.encode())
                latest = identity(get(None));write(evidence / 'LATEST_BEFORE_STATUS.json', latest)
                assert latest['state'] == 'IDENTITY_CONFIRMED', 'Latest version/source drift'
                q = ApiGetKernelSessionStatusRequest();q.user_name = OWNER;q.kernel_slug = SLUG;q.version_label = '1'
                result = svc.get_kernel_session_status(q)
                name = result.status.name
                status_record.update(official_status=name, queried_at_utc=utc(),
                    state='RUN_COMPLETE' if name == 'COMPLETE' else 'RUN_ERROR' if name == 'ERROR' else 'RUN_IN_PROGRESS',
                    failure_message=result.failure_message or None, version_label_sent='1',
                    times_not_provided_by_endpoint=True)
                write(evidence / 'RUN_STATUS.json', status_record)
                if name not in ('COMPLETE', 'ERROR'):
                    return
                files = [];token = None;raw_log = None
                for page in range(1, 11):
                    q = ApiListKernelSessionOutputRequest();q.user_name = OWNER;q.kernel_slug = SLUG;q.version_label = '1';q.page_size = 100
                    if token:q.page_token = token
                    result = svc.list_kernel_session_output(q)
                    files.extend(result.files or []);raw_log = raw_log or result.log;token = result.next_page_token
                    if not token:break
                assert not token and len(files) <= 1000, 'Incomplete output listing'
                listing = []
                chosen = []
                for item in files:
                    p = PurePosixPath(item.file_name)
                    assert not p.is_absolute() and '..' not in p.parts and '\\' not in item.file_name and ':' not in item.file_name
                    listing.append(dict(file=item.file_name))
                    # Download only already-exported evidence archive and runtime logs, not task/reference sources.
                    if item.file_name.endswith('.zip') and 'cpu02/' in item.file_name and '/source/' not in item.file_name:
                        chosen.append(item)
                write(evidence / 'OUTPUT_LISTING.json', dict(files=listing, pages=page, complete=True, log_available=bool(raw_log)))
                latest = identity(get(None));write(evidence / 'LATEST_BEFORE_DOWNLOAD.json', latest)
                assert latest['state'] == 'IDENTITY_CONFIRMED'
                guard.download_enabled = True
                assert len(chosen) <= 4, 'Unexpected evidence archives; no broad download'
                output = evidence / 'output';output.mkdir()
                records = []
                for item in chosen:
                    u = urlsplit(item.url)
                    host = u.hostname or ''
                    assert u.scheme == 'https' and (host == 'storage.googleapis.com' or host.endswith('.googleusercontent.com')
                        or host.endswith('.kaggleusercontent.com')), 'Unrecognized output host'
                    guard.urls.add(item.url)
                    r = requests.get(item.url, stream=True);r.raise_for_status()
                    path = output / item.file_name;path.parent.mkdir(parents=True, exist_ok=True)
                    h = hashlib.sha256();size = 0
                    with path.open('xb') as f:
                        for chunk in r.iter_content(1024 * 1024):
                            size += len(chunk);assert size <= 200 * 1024 * 1024
                            h.update(chunk);f.write(chunk)
                    records.append(dict(file=item.file_name, bytes=size, sha256=h.hexdigest(),
                        Notebook_id=ID, version=1, downloaded_at_utc=utc(), complete=True))
                if raw_log:
                    raw = raw_log.encode();(output / 'notebook.log').write_bytes(raw)
                    records.append(dict(file='notebook.log', bytes=len(raw), sha256=digest(raw), Notebook_id=ID, version=1, complete=True))
                latest = identity(get(None));write(evidence / 'LATEST_AFTER_DOWNLOAD.json', latest)
                assert latest['state'] == 'IDENTITY_CONFIRMED', 'Version changed while reading output'
                write(evidence / 'OUTPUT_MANIFEST.json', dict(files=records, version_bound_before_after=True,
                    status=name, complete_listing=True, archive_downloaded=bool(chosen), admission_audited=False))
        except BaseException as e:
            ledger['stop_exception_class'] = type(e).__name__
            # No arbitrary SDK exception/response/capture text is persisted.
        finally:
            for n, original in originals.items():setattr(KaggleCredentials, n, original)
            if not (evidence / 'RESOURCE_IDENTITY.json').exists():write(evidence / 'RESOURCE_IDENTITY.json', resource)
            if not (evidence / 'RUN_STATUS.json').exists():write(evidence / 'RUN_STATUS.json', status_record)
            ledger.update(finished_at_utc=utc(), HTTP=guard.events, identity_state=resource['state'],
                          run_state=status_record['state'], original_UNKNOWN_STOP_preserved=True)
            write(evidence / 'READONLY_QUERY_LEDGER.json', ledger)
    print(json.dumps(dict(identity=resource['state'], run=status_record['state'], HTTP=len(guard.events),stop=ledger.get('stop_exception_class'))))


if __name__ == '__main__':
    run()
