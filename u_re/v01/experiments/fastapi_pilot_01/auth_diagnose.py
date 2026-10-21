"""Bounded read-only Kaggle diagnosis. Never writes or emits credential values."""
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import re
import sys
import traceback
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
EXPECTED_USER = 'wudangdexiaodoashi'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def redact(text, secrets=()):
    text = str(text)
    for secret in sorted((x for x in secrets if isinstance(x, str) and x), key=len, reverse=True):
        text = text.replace(secret, '[REDACTED]')
    text = text.replace(str(Path.home()), '[USER_HOME]')
    text = re.sub(r'(?i)(bearer|authorization|cookie|api[_-]?key|token)\s*[:=]\s*[^\s,;]+', r'\1=[REDACTED]', text)
    text = re.sub(r'(?i)KGAT_[A-Za-z0-9_.-]+', '[REDACTED]', text)
    text = re.sub(r'[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}', '[REDACTED]', text)
    text = re.sub(r'[A-Za-z0-9_+/=-]{40,}', '[REDACTED]', text)
    text = re.sub(r'[A-Za-z]:\\[^\r\n]*', '[LOCAL_PATH]', text)
    return text[:1200]


def inventory():
    config_root = Path(os.environ.get('KAGGLE_CONFIG_DIR', Path.home() / '.kaggle'))
    files = {'config': config_root / 'kaggle.json',
             'access_token': Path.home() / '.kaggle/access_token',
             'access_token_txt': Path.home() / '.kaggle/access_token.txt',
             'oauth_credentials': Path.home() / '.kaggle/credentials.json'}
    secrets = [v for k, v in os.environ.items() if k.startswith('KAGGLE_') and any(x in k for x in ('TOKEN', 'KEY', 'PASSWORD'))]
    records = []
    for name, path in files.items():
        row = dict(source=name, credential_source_present=path.is_file(),
                   readable=None, credential_format_valid=None,
                   account_matches_expected=None, permissions='Windows ACL not assessed')
        if path.is_file():
            try:
                raw = path.read_text(encoding='utf-8'); row['readable'] = True
                if path.suffix == '.json':
                    data = json.loads(raw); row['credential_format_valid'] = isinstance(data, dict)
                    if isinstance(data, dict):
                        row['has_legacy_key'] = bool(data.get('key'))
                        row['has_token'] = bool(data.get('token') or data.get('access_token'))
                        row['has_refresh_token'] = bool(data.get('refresh_token'))
                        row['account_matches_expected'] = data.get('username') == EXPECTED_USER if data.get('username') else None
                        for k, value in data.items():
                            if any(word in k.lower() for word in ('token', 'key', 'password')) and isinstance(value, str):
                                secrets.append(value)
                else:
                    value = raw.strip(); secrets.append(value)
                    row['credential_format_valid'] = bool(value) and not any(c.isspace() for c in value)
            except (OSError, ValueError) as exc:
                row['credential_format_valid'] = False; row['exception_class'] = type(exc).__name__
        records.append(row)
    environment = dict(credential_source_present=bool(os.environ.get('KAGGLE_API_TOKEN')),
                       config_dir_override_present='KAGGLE_CONFIG_DIR' in os.environ,
                       credential_format_valid=None)
    token = os.environ.get('KAGGLE_API_TOKEN')
    if token:
        # Do not log token length, prefix, hash, or value.
        try:
            is_file = Path(token).is_file()
        except OSError:
            is_file = False
        environment['source_is_file'] = is_file
        environment['credential_format_valid'] = is_file or not any(c.isspace() for c in token)
    return files, records, environment, secrets


def diagnose():
    import requests
    files, records, env, secrets = inventory()
    # In-memory comparison only; no credential bytes or hashes are persisted.
    before = {name: p.read_bytes() for name, p in files.items() if p.is_file()}
    result = dict(queried_at_utc=datetime.now(timezone.utc).isoformat(),
                  python_version=sys.version.split()[0],
                  sdk_version=importlib.metadata.version('kaggle'),
                  kagglesdk_version=importlib.metadata.version('kagglesdk'),
                  cli_distribution_version=importlib.metadata.version('kaggle'),
                  cli_entrypoint='kaggle.cli:main',cli_uses_same_import_auth=True,
                  sources=records,environment=env,read_only_requests=[],
                  SDK_initialized=False,identity_confirmed=False,read_only_request_succeeded=False,
                  credential_files_changed=False,credential_values_logged=False,
                  credential_mutation_attempted=False,SaveKernel_requests=0,
                  status='AUTH_BLOCKED',category='AUTH_UNKNOWN')
    original = requests.Session.send
    allowed = {'IntrospectToken', 'ListKernels'}
    def send(session, request, **kwargs):
        url = urlsplit(request.url); operation = url.path.rstrip('/').split('/')[-1]
        if operation not in allowed or url.hostname not in {'api.kaggle.com','www.kaggle.com','kaggle.com'}:
            raise RuntimeError('Read-only diagnostic refused operation: ' + operation)
        row = dict(operation=operation,method=request.method,hostname=url.hostname,
                   authentication_stage='token_introspection' if operation=='IntrospectToken' else 'owner_read_only_listing')
        result['read_only_requests'].append(row)
        kwargs['timeout'] = 40
        try:
            response = original(session, request, **kwargs)
            row['http_status'] = response.status_code
            row['content_type'] = response.headers.get('Content-Type','').split(';')[0]
            try:
                data = response.json()
                if isinstance(data, dict):
                    if isinstance(data.get('active'), bool): row['token_active'] = data['active']
                    if isinstance(data.get('username'), str): row['account_matches_expected'] = data['username'] == EXPECTED_USER
                    for key in ('message','error','errorMessage','code'):
                        if isinstance(data.get(key),(str,int)):
                            row['redacted_'+key] = redact(data[key], secrets)
            except ValueError:
                row['response_json'] = False
            return response
        except requests.RequestException as exc:
            row['exception_class'] = type(exc).__name__
            row['redacted_error'] = redact(str(exc),secrets)
            raise
    requests.Session.send = send
    # SDK OAuth fallback may refresh/save/delete credentials. Refuse all such
    # mutations during this diagnosis; do not alter its success decisions.
    from kagglesdk.kaggle_creds import KaggleCredentials
    replacements = {}
    def refuse(*args, **kwargs):
        result['credential_mutation_attempted'] = True
        raise RuntimeError('Credential refresh/write/delete is not authorized')
    for name in ('refresh_access_token','generate_access_token','save','delete'):
        replacements[name] = getattr(KaggleCredentials,name)
        setattr(KaggleCredentials,name,refuse)
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            from kaggle import api
            result['SDK_initialized'] = True
            user = api.get_config_value('username')
            result['identity_confirmed'] = user == EXPECTED_USER
            if not result['identity_confirmed']: raise RuntimeError('Current identity does not match expected owner')
            rows = api.kernels_list(mine=True,page_size=1)
            result['read_only_request_succeeded'] = True
            result['owner_notebook_count_in_page'] = len(rows)
            result['status'] = 'AUTH_READONLY_GO'
            result['category'] = None
    except BaseException as exc:
        result['exception_class'] = type(exc).__name__
        result['authentication_stage'] = 'import_authenticate' if not result['SDK_initialized'] else 'owner_read_only_listing'
        result['redacted_error'] = redact(str(exc),secrets)
        result['traceback'] = [dict(module=Path(f.filename).name,function=f.name,line=f.lineno)
                               for f in traceback.extract_tb(exc.__traceback__)]
        events = result['read_only_requests']
        if any(e.get('exception_class') for e in events): result['category']='AUTH_NETWORK_ERROR'
        elif any(e.get('token_active') is False for e in events): result['category']='AUTH_CREDENTIAL_REJECTED'
        elif any(e.get('http_status')==401 for e in events): result['category']='AUTH_CREDENTIAL_REJECTED'
        elif any(e.get('http_status')==403 for e in events): result['category']='AUTH_PERMISSION_DENIED'
        elif not any(r['credential_source_present'] for r in records) and not env['credential_source_present']:
            result['category']='AUTH_CONFIG_ERROR'
        # 400/404 alone cannot prove invalid/expired credentials. The SDK hides
        # these introspection failures; leave AUTH_UNKNOWN without server detail.
    finally:
        requests.Session.send=original
        for name,value in replacements.items():setattr(KaggleCredentials,name,value)
        result['captured_output_redacted']=redact(captured.getvalue(),secrets)
        after={name:p.read_bytes() for name,p in files.items() if p.is_file()}
        result['credential_files_changed']=before!=after
        if before!=after: raise RuntimeError('Credential mutation detected; stop')
    result['sdk_source_hashes']={}
    for dist,relative in [('kaggle','kaggle/__init__.py'),('kaggle','kaggle/cli.py'),
                          ('kaggle','kaggle/api/kaggle_api_extended.py'),
                          ('kagglesdk','kagglesdk/kaggle_env.py'),('kagglesdk','kagglesdk/kaggle_creds.py')]:
        result['sdk_source_hashes'][relative]=sha(Path(importlib.metadata.distribution(dist).locate_file(relative)))
    destination=HERE/'AUTH_STATUS.json'
    with destination.open('x',encoding='utf-8',newline='\n') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps({k:result[k] for k in ('status','category','SDK_initialized','identity_confirmed','read_only_request_succeeded','credential_files_changed')}))
    return result


if __name__=='__main__':diagnose()
