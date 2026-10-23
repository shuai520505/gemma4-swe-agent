"""Prospective evidence-based categories; no candidate decision or test changes."""
import ast,json,re
from pathlib import Path

MISSING=re.compile(r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]")
IMPORT_API=re.compile(r"ImportError: cannot import name ['\"]([^'\"]+)['\"] from ['\"](fastapi\.[^'\"]+)['\"]")
KEYWORD=re.compile(r"TypeError: (\w+)\(\) got an unexpected keyword argument ['\"]([^'\"]+)['\"]")
KNOWN_EXTERNAL={'inline_snapshot':'inline-snapshot','dirty_equals':'dirty-equals','pytest_subtests':'pytest-subtests','multipart':'python-multipart','python_multipart':'python-multipart','sqlalchemy':'sqlalchemy'}
TARGET_FUNCTIONS={'Depends','Security','Query','Path','Body','Header','Cookie','Form','File'}

def declarations(source):
    text='\n'.join(v['text'] for k,v in source.items() if k.startswith('requirements') or k=='pyproject.toml')
    # Require a distribution occurrence at a requirement boundary rather than
    # treating arbitrary Issue/test mentions as package declarations.
    return set(re.findall(r'(?:^|[\s\"\'])((?:[a-zA-Z0-9]+[-_.])*[a-zA-Z0-9]+)(?=[<>=!~;\[\s\"\']|$)',text,re.M))

def event_class(event,source,issue,versions):
    detail=event.get('details','');missing=MISSING.search(detail)
    if missing:
        module=missing.group(1);dist=KNOWN_EXTERNAL.get(module,module.replace('_','-'))
        declared={s.lower().replace('_','-') for s in declarations(source)}
        external=not module.startswith(('fastapi','tests','test.'))
        # inline_snapshot's prior independent origin is already proved by the
        # diagnostic package/traceback evidence; others need a frozen declaration.
        if external and (module=='inline_snapshot' or dist.lower() in declared) and dist in versions and versions[dist] is None:
            return 'A',dict(error='MISSING_EXTERNAL_TEST_DEPENDENCY',module=module,distribution=dist,evidence='Frozen test dependency declaration or independently established inline-snapshot, missing interpreter metadata, external module namespace')
        return 'D',dict(error='UNEXPLAINED_MISSING_MODULE',module=module)
    imp=IMPORT_API.search(detail)
    if imp:
        name,module=imp.groups();file=module.replace('.','/')+'.py'
        if file in source and file in detail:
            definitions={n.name for n in ast.walk(ast.parse(source[file]['text'])) if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))}
            supported=name.lower() in issue.lower() or (name=='PydanticV1NotSupportedError' and module=='fastapi.exceptions' and 'pydantic.v1' in issue.lower() and 'error' in issue.lower())
            if supported and name not in definitions:
                return 'B',dict(error='TARGET_WORKSPACE_API_ABSENT',API=name,module=module,source_sha256=source[file]['sha256'],Issue_spells_exact_API=name.lower() in issue.lower(),formal_admission=False)
        return 'D',dict(error='UNEXPLAINED_WORKSPACE_IMPORT',API=name,module=module)
    kw=KEYWORD.search(detail)
    if kw:
        function,argument=kw.groups();file='fastapi/param_functions.py'
        if function in TARGET_FUNCTIONS and function.lower() in issue.lower() and argument.lower() in issue.lower() and file in source:
            defs=[n for n in ast.parse(source[file]['text']).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==function]
            if len(defs)==1:
                args=defs[0].args;names={a.arg for a in args.args+args.posonlyargs+args.kwonlyargs}
                if argument not in names and args.kwarg is None:return 'B',dict(error='TARGET_KEYWORD_ABSENT',API=function,argument=argument,source_sha256=source[file]['sha256'],formal_admission=False)
    return 'D',dict(error='UNCLASSIFIED_COLLECTION_SETUP_INTERNAL_FAILURE')

def classify(row,audit,source,issue,versions):
    if not row['evidence_ok']:return dict(category='E',status='STOP',reason='INTEGRITY_FAILURE',eligible=None)
    snapshot_pair=audit.get('snapshot_assertion_teardown_proven') is True and audit.get('duplicate_snapshot_finalizer_errors')==row['counts'].get('errors') and audit.get('environment_errors')==0
    if audit['category']=='assertion_failure' and not audit['infrastructure_stop'] and row['counts'].get('failures',0)>0 and (row['counts'].get('errors',0)==0 or snapshot_pair):
        return dict(category='TARGET_BEHAVIOR_FAILURE',status='BASELINE_ELIGIBLE',reason='Discriminating native behavior assertion; offline Issue relation review required before final lock',eligible=True,snapshot_assertion_teardown_pairs=audit.get('duplicate_snapshot_finalizer_errors',0),independent_environment_errors=0)
    if audit['category']=='passed' and not audit['infrastructure_stop']:
        return dict(category='NON_DISCRIMINATING',status='REJECT_CONTINUE',reason='Original base all passing',eligible=False)
    errors=[e for e in audit.get('events',[]) if e.get('category') in ('setup_error','collection_error','internal_error','unknown_unparsed')]
    classified=[event_class(e,source,issue,versions) for e in errors]
    kinds={k for k,v in classified};proof=[v for k,v in classified]
    if not kinds or 'D' in kinds:return dict(category='D',status='STOP',reason='UNKNOWN_INTERNAL_ERROR',eligible=None,errors=proof)
    if kinds=={'A'}:return dict(category='A',status='REJECT_CONTINUE',reason='INDEPENDENT_ENVIRONMENT_ERROR',eligible=False,errors=proof)
    if kinds=={'B'}:return dict(category='B',status='CONDITIONAL_TARGET_FAILURE',reason='TARGET_RELATED_COLLECTION_FAILURE_NOT_FORMAL',eligible=False,errors=proof)
    if kinds=={'A','B'}:return dict(category='C',status='REJECT_CONTINUE',reason='MIXED_COLLECTION_FAILURE_WITH_UNRESOLVED_ENVIRONMENT',eligible=False,errors=proof)
    return dict(category='D',status='STOP',reason='UNKNOWN_INTERNAL_ERROR',eligible=None,errors=proof)
