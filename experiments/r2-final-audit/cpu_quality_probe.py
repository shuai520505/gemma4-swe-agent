"""Issue-derived expanded checks against isolated copies of locked production code."""
import sys,json,traceback,os,types,ast,copy,pickle
from pathlib import Path

task,variant=sys.argv[1:3]
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/r2-audit/quality'/task/('selected-'+variant)
sys.path.insert(0,str(source));rows=[]
def check(name,fn,kind='control'):
 try:detail=fn();rows.append(dict(name=name,kind=kind,status='PASS',detail=detail))
 except Exception as e:rows.append(dict(name=name,kind=kind,status='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc()))

if task.startswith('django'):
 from django.conf import settings
 settings.configure(INSTALLED_APPS=[],DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},USE_I18N=False,SECRET_KEY='owned-cpu-audit')
 import django;django.setup()
 from django.db import models,connection
 import enum,datetime,json as jsonlib
 class Text(models.TextChoices):
  FIRST='first','First';SECOND='second','Second'
 class Number(models.IntegerChoices):
  ONE=1,'One';TWO=2,'Two'
 class Auto(models.TextChoices):ALPHA=enum.auto();BETA=enum.auto()
 class Date(datetime.date,models.Choices):DAY=2020,1,2,'Day'
 class Record(models.Model):
  text=models.CharField(max_length=10,choices=Text.choices)
  number=models.IntegerField(choices=Number.choices)
  class Meta:app_label='owned_expanded'
 with connection.schema_editor() as editor:editor.create_model(Record)
 r=Record.objects.create(text=Text.FIRST,number=Number.ONE)
 def assert_(condition):assert condition
 check('fresh_text_value',lambda:assert_(str(r.text)=='first'),'target')
 check('fresh_integer_value',lambda:assert_(str(r.number)=='1'),'target')
 check('database_readback',lambda:assert_((Record.objects.get(pk=r.pk).text,Record.objects.get(pk=r.pk).number)==('first',1)))
 check('choices_labels_values',lambda:assert_(Text.choices==[('first','First'),('second','Second')] and Text.labels==['First','Second'] and Number.values==[1,2] and Text.names==['FIRST','SECOND']))
 check('enum_type_and_inheritance',lambda:assert_(isinstance(Text.FIRST,str) and isinstance(Text.FIRST,models.Choices) and isinstance(Number.ONE,int) and isinstance(Number.ONE,enum.Enum)))
 check('value_equality_hash_lookup',lambda:assert_(Text('first') is Text.FIRST and Number(1) is Number.ONE and {Text.FIRST:'a'}['first']=='a' and hash(Number.ONE)==hash(1)))
 check('json_primitive_values',lambda:assert_(jsonlib.loads(jsonlib.dumps([Text.FIRST,Number.ONE]))==['first',1]))
 check('auto_choices',lambda:assert_(Auto.values==['ALPHA','BETA'] and Auto.labels==['Alpha','Beta']))
 check('date_choice_value',lambda:assert_(Date.DAY.value==datetime.date(2020,1,2) and Date.DAY.label=='Day'))
 check('enum_repr_copy',lambda:assert_('FIRST' in repr(Text.FIRST) and copy.copy(Text.FIRST) is Text.FIRST and copy.deepcopy(Number.ONE) is Number.ONE))
 check('format_text',lambda:assert_(format(Text.FIRST)=='first'),'target')
 check('integer_arithmetic',lambda:assert_(Number.ONE+Number.TWO==3))
elif task.startswith('pydata'):
 import numpy as np,xarray as xr,zarr,dask.array as da
 from xarray.core.variable import Variable
 from xarray.core.common import get_chunksizes
 def assert_(condition):assert condition
 check('numpy_dataset',lambda:assert_(dict(xr.Dataset({'v':('x',np.arange(4))}).chunks)=={}))
 check('dask_dataset_metadata',lambda:assert_(dict(xr.Dataset({'v':('x',da.arange(6,chunks=2))}).chunks)=={'x':(2,2,2)}))
 check('dask_aggregation',lambda:assert_(dict(get_chunksizes([Variable('x',da.ones(6,chunks=2)),Variable('y',da.ones(4,chunks=2))]))=={'x':(2,2,2),'y':(2,2)}))
 def inconsistent():
  try:get_chunksizes([Variable('x',da.ones(6,chunks=2)),Variable('x',da.ones(6,chunks=3))])
  except ValueError as e:assert 'inconsistent chunks' in str(e);return str(e)
  raise AssertionError('Expected original ValueError')
 check('inconsistent_chunks_exception',inconsistent)
 class Store(dict):
  def __init__(self):super().__init__();self.reads=[]
  def __getitem__(self,key):
   if key.startswith('v/') and not key.split('/')[-1].startswith('.'):self.reads.append(key)
   return super().__getitem__(key)
 def zarr_case(chunks):
  store=Store();g=zarr.group(store=store);a=g.create_dataset('v',data=np.arange(6)+1,chunks=2);a.attrs['_ARRAY_DIMENSIONS']=['x']
  ds=xr.open_dataset(store,engine='zarr',chunks=chunks,consolidated=False);store.reads.clear()
  result=dict(ds.chunks);assert not store.reads,store.reads
  assert result==({} if chunks is None else {'x':(2,2,2)})
  np.testing.assert_array_equal(ds.v.values,np.arange(6)+1);assert store.reads;ds.close()
  return dict(chunks=result,materialization_on_metadata=False,values_read_counter_active=True)
 check('zarr_lazy_chunks_none',lambda:zarr_case(None),'target')
 check('zarr_dask_chunks',lambda:zarr_case({}))
 class Duck:
  shape=(6,);ndim=1;dtype=np.dtype('i8')
  def __init__(self):self.materializations=0
  def __array__(self,*a,**k):self.materializations+=1;return np.arange(6)
  def __array_function__(self,*a,**k):return NotImplemented
  def __array_ufunc__(self,*a,**k):return NotImplemented
 def duck(chunked):
  d=Duck()
  if chunked:d.chunks=((2,2,2),)
  v=Variable('x',d,fastpath=True);assert dict(get_chunksizes([v]))==({'x':(2,2,2)} if chunked else {})
  assert d.materializations==0;return dict(materializations=d.materializations)
 check('duck_array_without_chunks',lambda:duck(False))
 check('duck_array_with_chunks',lambda:duck(True))
 from xarray.backends.common import BackendArray
 from xarray.core import indexing
 class Lazy(BackendArray):
  shape=(6,);dtype=np.dtype('i8')
  def __init__(self):self.reads=0
  def __getitem__(self,key):self.reads+=1;return np.arange(6)[key.tuple]
 def lazy():
  b=Lazy();v=Variable('x',indexing.LazilyIndexedArray(b),fastpath=True);assert dict(get_chunksizes([v]))=={};assert b.reads==0;return dict(reads=b.reads)
 check('lazy_backend_no_getitem',lazy,'target')
else:
 import numpy as np,unittest.mock as mock
 # Extract the exact unchanged/patched function to avoid conflating old pytest's
 # package/plugin compatibility with sentinel-identity behavior.
 p=source/'src/_pytest/compat.py';module=ast.parse(p.read_text(encoding='utf8'))
 fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='num_mock_patch_args')
 ns={'sys':sys};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),ns);count=ns['num_mock_patch_args']
 def count_(patchings):
  def f():pass
  if patchings is not None:f.patchings=patchings
  return count(f)
 def item(value,attr=None):return types.SimpleNamespace(attribute_name=attr,new=value)
 def assert_(condition):assert condition
 check('numpy_array_replacement',lambda:assert_(count_([item(np.array([-5.5,3.0]))])==0),'target')
 check('default_auto_argument',lambda:assert_(count_([item(mock.DEFAULT)])==1))
 check('plain_no_patchings',lambda:assert_(count_(None)==0))
 check('empty_patchings',lambda:assert_(count_([])==0))
 check('explicit_mock_replacement',lambda:assert_(count_([item(mock.Mock())])==0))
 check('attribute_name_excluded',lambda:assert_(count_([item(mock.DEFAULT,'field')])==0))
 check('mixed_parameter_count',lambda:assert_(count_([item(mock.DEFAULT),item(np.array([1,2])),item(mock.DEFAULT),item(mock.DEFAULT,'attr')])==2),'target')
 class EqTrap:
  def __eq__(self,other):raise AssertionError('Comparison must use identity')
 check('no_custom_equality_side_effect',lambda:assert_(count_([item(EqTrap())])==0),'target')
 fake=types.SimpleNamespace(DEFAULT=object());old=sys.modules.get('mock');sys.modules['mock']=fake
 try:check('both_mock_module_sentinels',lambda:assert_(count_([item(fake.DEFAULT),item(mock.DEFAULT)])==2))
 finally:
  if old is None:sys.modules.pop('mock',None)
  else:sys.modules['mock']=old
def source_identity():
 import hashlib
 loaded=Path(django.__file__) if task.startswith('django') else Path(xr.__file__) if task.startswith('pydata') else p
 assert loaded.resolve().is_relative_to(source.resolve())
 return dict(loaded_file=str(loaded.resolve()),sha256=hashlib.sha256(loaded.read_bytes()).hexdigest())
check('loaded_source_identity',source_identity)
out=Path(__file__).resolve().parent/'cpu-results';out.mkdir(exist_ok=True)
(out/(task+'-'+variant+'.json')).write_text(json.dumps(dict(task=task,variant=variant,evidence='CPU_VERIFIED',method='Expanded owned checks; no reference patch, hidden tests or trusted historical expectations changed',python=sys.version,source=str(source),checks=rows),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(task=task,variant=variant,passed=sum(r['status']=='PASS' for r in rows),failed=[r['name'] for r in rows if r['status']=='FAIL'])))
