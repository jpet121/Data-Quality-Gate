"""Specification-derived oracle checks; no production code in reference implementation."""
import ast
import json
from pathlib import Path
from hypothesis import given,settings,strategies as st
from event_validator import validate
from assurance.reference import expected,lex

ROOT=Path(__file__).resolve().parents[2]
MATRIX=json.loads((ROOT/'specifications/authorized_functional_baseline_v2/examples/matrix_v1.json').read_text())

def test_reference_has_no_production_or_pydantic_imports():
    tree=ast.parse((ROOT/'assurance/reference.py').read_text())
    for n in ast.walk(tree):
        if isinstance(n,ast.ImportFrom):assert not n.level and not (n.module or '').startswith(('event_validator','pydantic'))
        if isinstance(n,ast.Import):assert not any(x.name.startswith(('event_validator','pydantic')) for x in n.names)

def test_reference_known_valid_and_invalid_cases(valid,invalid):
    assert all(expected(raw,MATRIX).status=='ACCEPTED' for raw in valid)
    assert all(expected(raw,MATRIX).status=='REJECTED' for raw in invalid)

@settings(max_examples=200,deadline=None,derandomize=True)
@given(st.dictionaries(st.sampled_from(['a','b','c']),st.text(alphabet='abcXYZ012 |="\\',min_size=1,max_size=30),min_size=1,max_size=3))
def test_reference_quoted_grammar_has_independent_roundtrip(values):
    def quote(s):return '"'+s.replace('\\','\\\\').replace('"','\\"').replace('|','\\|')+'"'
    raw=' | '.join(k+'='+quote(v) for k,v in values.items())
    assert lex(raw,32)==values

@settings(max_examples=300,deadline=None,derandomize=True)
@given(st.integers(min_value=0,max_value=4),st.integers(min_value=1,max_value=1000000),st.integers(min_value=1,max_value=9999999))
def test_all_event_models_agree_with_independent_reference(cfg,valid,event,quantity,number):
    raw=valid[event].replace('event_id=EVT-00'+str(event+1),'event_id=GEN-'+str(number))
    if event in {2,3}:raw=raw.replace('quantity=2','quantity='+str(quantity))
    oracle=expected(raw,MATRIX);actual=validate(raw,'independent',cfg)
    assert oracle.status==actual.status=='ACCEPTED'
    observed=actual.record.model_dump(exclude_none=True)
    if 'lines_json' in observed: observed['lines_json']=list(observed['lines_json'])
    assert observed==oracle.record
