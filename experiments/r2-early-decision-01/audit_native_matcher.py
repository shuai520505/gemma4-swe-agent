"""Exercise frozen official validation functions; no task repair or model."""
import ast, hashlib, json
from pathlib import Path

D=Path(__file__).resolve().parent
source=D.parents[1]/'work/r2-audit/official-sources/swegemma/harness/verification.py'
raw=source.read_bytes();tree=ast.parse(raw)
names={'_node_matches_requirement','_extract_test_functions_from_patch','_validate_junit_xml'}
namespace={}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(source),'exec'),namespace)
xml='<testsuite tests="2" failures="0" errors="0" skipped="1"><testcase classname="xarray.tests.test_computation" name="test_vectorize_dask_dtype"/><testcase classname="xarray.tests.test_computation" name="test_vectorize_dask_dtype_meta"><skipped message="upstream intentional skip"/></testcase></testsuite>'
req=('xarray/tests/test_computation.py::test_vectorize_dask_dtype',)
plain=xml.replace('test_vectorize_dask_dtype_meta','unrelated_test')
results={
 'classification':'CPU_VERIFIED_VALIDATOR_BEHAVIOR_ONLY_NOT_REPAIR_EVIDENCE',
 'source_sha256':hashlib.sha256(raw).hexdigest(),
 'official_functions_modified':False,
 'same_exact_required_pass_with_prefix_named_skip':namespace['_validate_junit_xml'](xml,(),req),
 'same_exact_required_pass_with_unrelated_skip':namespace['_validate_junit_xml'](plain,(),req),
 'consequence':'A legal upstream skipped sibling can cause a false-negative SDK resolved result. No expected test outcome or SDK matcher is changed.',
 'real_task_relevance':'CPU4 raw xarray JUnit contains the same required test name and intentionally skipped _meta sibling. Does not establish any Agent repair.'}
(D/'NATIVE_MATCHER_AUDIT.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
