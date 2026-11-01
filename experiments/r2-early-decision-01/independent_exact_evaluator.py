"""Proposed independent endpoint; never replaces or modifies official SDK results."""
import xml.etree.ElementTree as ET

def canonical(req):
    path,*rest=req.split('::')
    if not rest:return None
    module=path.removesuffix('.py').replace('/','.')
    return '.'.join([module]+rest[:-1])+'::'+rest[-1]

def validate(xml,exit_code,targets,controls,allowed_ambiguous=()):
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
            key=canonical(req)
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
    print('CPU_CONTRACT_PASS: 8 evaluator boundary checks; no task repair evidence; pending design approval')
