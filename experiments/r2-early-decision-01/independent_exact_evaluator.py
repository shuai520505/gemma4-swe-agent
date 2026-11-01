"""Proposed independent endpoint; never replaces or modifies official SDK results."""
import xml.etree.ElementTree as ET

BARE_NODES_MODULES={'sympy__sympy-24661':'sympy.parsing.tests.test_sympy_parser'}
BASELINE_CO_TARGETS={'pydata__xarray-6599':('xarray/tests/test_computation.py::test_polyval[timedelta-True]',)}

def infrastructure_controls(observed,task_id):
    """Keep raw metadata/results; distinguish an observed original co-failure.

    This never relaxes validate(): every original control remains mandatory
    for a successful repair. Only baseline/ordinary-failure attribution differs.
    """
    co_targets=BASELINE_CO_TARGETS.get(task_id,())
    controls=observed.get('controls',{})
    known={k:v for k,v in controls.items() if k not in co_targets and v is not None}
    unknown=[k for k,v in controls.items() if v is None]
    allowed=['tests/config/test_config.py::test_csv_regex_comma_in_quantifier[foo,'] if task_id=='pylint-dev__pylint-8898' else []
    return dict(passed=bool(known) and all(v and set(v)=={'pass'} for v in known.values()) and all(k in allowed for k in unknown),
        raw_positive_controls_passed=observed.get('positive_controls_passed'),
        original_co_targets={k:controls.get(k) for k in co_targets},unknown_nodes=unknown,
        success_criterion_relaxed=False,all_original_controls_still_required_for_repair=True)

def canonical(req,bare_module=None):
    path,*rest=req.split('::')
    if not rest:return bare_module+'::'+req if bare_module else None
    module=path.removesuffix('.py').replace('/','.')
    return '.'.join([module]+rest[:-1])+'::'+rest[-1]

def validate(xml,exit_code,targets,controls,allowed_ambiguous=(),bare_module=None):
    result=dict(status='FAIL',official_sdk_resolved_override=False,ambiguous_nodes=[],nodes={})
    if exit_code!=0:
        return dict(result,reason='Complete trusted test command did not exit zero')
    try:root=ET.fromstring(xml)
    except ET.ParseError:return dict(result,reason='Malformed XML')
    cases=root.findall('.//testcase')
    if not cases:return dict(result,reason='No recorded tests')
    indexed={}
    for case in cases:
        outcome=next((s for s in ('failure','error','skipped') if case.find(s) is not None),'pass')
        key=case.get('classname','')+'::'+case.get('name','')
        indexed.setdefault(key,[]).append(outcome)
        if outcome in ('failure','error'):return dict(result,reason='Test failure or collection/runtime error')
    if not targets or not controls:return dict(result,reason='Missing trusted target or positive controls')
    for kind,requirements in [('target',targets),('control',controls)]:
        for req in requirements:
            name=req.split('::')[-1]
            if '[' in name and not name.endswith(']'):
                result['nodes'][req]=None;result['ambiguous_nodes'].append(req)
                if kind=='target' or req not in allowed_ambiguous:
                    return dict(result,reason='Undeclared or target metadata ambiguity')
                continue
            key=canonical(req,bare_module)
            if key is None:return dict(result,reason='Unqualified required node without declared trusted module: '+req)
            matches=indexed.get(key,[])
            # An unparameterized required function may denote all its parameter cases.
            # Never accept underscore-prefixed siblings or partial parameter IDs.
            if not matches and '[' not in name and key:
                matches=[o for k,values in indexed.items() if k.startswith(key+'[') for o in values]
            result['nodes'][req]=matches
            if not matches or set(matches)!={'pass'}:
                return dict(result,reason='Exact required identity missing, failed or skipped: '+req)
    return dict(result,status='INDEPENDENT_TEST_PASS',reason=None,
        semantic_review='REQUIRED_SEPARATELY',production_fix='REQUIRED_SEPARATELY',
        all_raw_metadata_confirmed=not result['ambiguous_nodes'])

if __name__=='__main__':
    required='xarray/tests/test_computation.py::test_vectorize_dask_dtype'
    control='xarray/tests/test_computation.py::test_control'
    xml='<testsuite><testcase classname="xarray.tests.test_computation" name="test_vectorize_dask_dtype"/><testcase classname="xarray.tests.test_computation" name="test_control"/><testcase classname="xarray.tests.test_computation" name="test_vectorize_dask_dtype_meta"><skipped/></testcase></testsuite>'
    assert validate(xml,0,[required],[control])['status']=='INDEPENDENT_TEST_PASS'
    assert validate(xml,1,[required],[control])['status']=='FAIL'
    assert validate(xml.replace('name="test_control"','name="test_control_other"'),0,[required],[control])['status']=='FAIL'
    assert validate(xml.replace('name="test_vectorize_dask_dtype"','name="test_vectorize_dask_dtype_other"'),0,[required],[control])['status']=='FAIL'
    assert validate(xml.replace('name="test_control"/>','name="test_control"><skipped/></testcase>'),0,[required],[control])['status']=='FAIL'
    assert validate(xml,0,[required+'[broken,'],[control])['status']=='FAIL'
    assert validate(xml,0,[required],[control+'[broken,'])['status']=='FAIL'
    r=validate(xml,0,[required],[control,control+'[broken,'],[control+'[broken,'])
    assert r['status']=='INDEPENDENT_TEST_PASS' and not r['all_raw_metadata_confirmed']
    assert validate(xml,0,['test_vectorize_dask_dtype'],[control])['status']=='FAIL'
    assert validate(xml,0,['test_vectorize_dask_dtype'],[control],bare_module='xarray.tests.test_computation')['status']=='INDEPENDENT_TEST_PASS'
    assert validate(xml,0,['test_vectorize_dask_dtype'],[control],bare_module='wrong.module')['status']=='FAIL'
    print('CPU_CONTRACT_PASS: 11 evaluator boundary checks; no task repair evidence')
