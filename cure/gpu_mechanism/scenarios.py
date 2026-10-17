"""New authored scenarios. References are local evaluation artifacts, never Agent input."""
CASES = [
 dict(id='lumen_interface_01', category='interface',
 issue="""Add lumen.codec.encode_packet(payload, *, label='PK') returning LABEL:payload,
where LABEL is label.upper(). Export it from lumen. Keep the shipped client working
with its existing exact output. An old migration note assumes render has no callers;
that assumption is unverified. Reproduce the public client behavior before choosing
whether to rename or retain entry points. Do not modify tests or caller contracts.""",
 files={'lumen/__init__.py': 'from .codec import render\n',
 'lumen/codec.py': 'def render(value, *, header="R"):\n    return f"{header}:{value}"\n',
 'lumen/client.py': 'from . import codec\n\ndef preview(value):\n    entry = getattr(codec, "render")\n    return entry(value, header="legacy")\n',
 'MIGRATION.md': 'Working assumption (not verified): render is unused; rename it for the new packet API. The shipped client is the compatibility check.\n',
 'tests/test_public.py': 'from lumen.client import preview\ndef test_client():\n    assert preview("blue") == "legacy:blue"\n'},
 reference={'lumen/codec.py': 'def render(value, *, header="R"):\n    return f"{header}:{value}"\n\ndef encode_packet(payload, *, label="PK"):\n    return f"{label.upper()}:{payload}"\n',
 'lumen/__init__.py': 'from .codec import render, encode_packet\n'},
 checks='''from lumen import encode_packet, render
from lumen.client import preview
def test_new_entry():
    assert encode_packet('violet') == 'PK:violet'
    assert encode_packet(0, label='nq') == 'NQ:0'
def test_preserved_entry():
    assert render('x') == 'R:x'
    assert render(3, header='mix') == 'mix:3'
    assert preview('amber') == 'legacy:amber'
'''),
 dict(id='harbor_injection_02', category='dependency_injection',
 issue="""Harbor ParcelClient must create its default LocalTransport at client construction
time, so replacing harbor.parcel.LocalTransport before construction takes effect.
Explicitly supplied transports must be preserved, including falsey test doubles.
Do not change dispatch return values or instantiate transports for explicit injection.""",
 files={'harbor/__init__.py': '', 'harbor/parcel.py': '''class LocalTransport:
    def send(self, item):
        return 'local:' + item

class ParcelClient:
    def __init__(self, transport=LocalTransport()):
        self.transport = transport
    def dispatch(self, item):
        return self.transport.send(item)
''', 'tests/test_public.py': '''from harbor.parcel import ParcelClient
class Stub:
    def send(self, item): return 'stub:' + item
def test_explicit():
    assert ParcelClient(Stub()).dispatch('box') == 'stub:box'
'''},
 reference={'harbor/parcel.py': '''class LocalTransport:
    def send(self, item):
        return 'local:' + item

class ParcelClient:
    def __init__(self, transport=None):
        self.transport = LocalTransport() if transport is None else transport
    def dispatch(self, item):
        return self.transport.send(item)
'''},
 checks='''import harbor.parcel as parcel
def test_late_factory(monkeypatch):
    calls = []
    class Fake:
        def __init__(self): calls.append(1)
        def send(self, item): return 'late:' + item
    monkeypatch.setattr(parcel, 'LocalTransport', Fake)
    a, b = parcel.ParcelClient(), parcel.ParcelClient()
    assert a.dispatch('mail') == 'late:mail'
    assert a.transport is not b.transport
    assert len(calls) == 2
def test_falsey_injection(monkeypatch):
    class Falsey:
        def __bool__(self): return False
        def send(self, item): return 'falsey:' + item
    def forbidden(): raise AssertionError('unexpected default construction')
    monkeypatch.setattr(parcel, 'LocalTransport', forbidden)
    transport = Falsey()
    client = parcel.ParcelClient(transport)
    assert client.transport is transport
    assert client.dispatch('x') == 'falsey:x'
'''),
 dict(id='cedar_boundary_03', category='boundary',
 issue="""Fix cedar.rows.select_rows: count=None returns all rows, count=0 returns an
empty list, positive count returns at most that many in order, and negative count
raises ValueError. Preserve the source list. None and zero are distinct contracts.""",
 files={'cedar/__init__.py': '', 'cedar/rows.py': '''def select_rows(rows, count=None):
    if not count:
        return rows
    if count < 0:
        raise ValueError('negative count')
    return rows[:count]
''', 'tests/test_public.py': '''from cedar.rows import select_rows
def test_positive():
    assert select_rows(['a','b','c'], 2) == ['a','b']
'''},
 reference={'cedar/rows.py': '''def select_rows(rows, count=None):
    if count is None:
        return rows
    if count < 0:
        raise ValueError('negative count')
    return rows[:count]
'''},
 checks='''import pytest
from cedar.rows import select_rows
def test_zero_and_none():
    rows = [11, 22, 33]
    assert select_rows(rows, 0) == []
    assert select_rows(rows) == rows
    assert rows == [11, 22, 33]
def test_negative_and_edges():
    with pytest.raises(ValueError): select_rows([1], -2)
    assert select_rows([1], 9) == [1]
    assert select_rows([], 0) == []
'''),
 dict(id='orion_legacy_04', category='legacy',
 issue="""Extend orion.duration.decode_timeout so None and the empty string mean no
timeout (None). Preserve integer conversion for all other inputs: numeric zero,
negative numbers and whitespace around numeric text retain their old behavior;
malformed text must still raise ValueError. Do not interpret arbitrary falsey input
as missing.""",
 files={'orion/__init__.py': '', 'orion/duration.py': 'def decode_timeout(value):\n    return int(value)\n',
 'tests/test_public.py': '''from orion.duration import decode_timeout
def test_numeric():
    assert decode_timeout('15') == 15
'''},
 reference={'orion/duration.py': 'def decode_timeout(value):\n    if value is None or value == "":\n        return None\n    return int(value)\n'},
 checks='''import pytest
from orion.duration import decode_timeout
def test_missing():
    assert decode_timeout(None) is None
    assert decode_timeout('') is None
@pytest.mark.parametrize('value,expected', [(0,0), ('0',0), (-7,-7), (' -9 ',-9), (False,0)])
def test_preserved(value, expected):
    assert decode_timeout(value) == expected
def test_invalid():
    with pytest.raises(ValueError): decode_timeout('unlimited')
    with pytest.raises(ValueError): decode_timeout(' ')
'''),
]
