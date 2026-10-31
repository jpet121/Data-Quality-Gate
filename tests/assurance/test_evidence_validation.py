"""Regression gates for malformed evidence, not changes to business requirements."""
import pytest
from assurance.gate import evaluate
from assurance.compare import Observation, compare

APPROVALS=dict.fromkeys(['requirements_oracle','mutation_thresholds','human_release'],True)
ROW={'id':'control','mandatory':True,'status':'PASS','evidence':['control.json']}

@pytest.mark.parametrize('counts',[
    {'passed':1,'total':0}, {'passed':1,'total':2}, {'passed':True},
    {'passed':1.5}, {'passed':'1'}, {'passed':-1}, {'passed':1,'failed':-1},
    {'passed':1,'errors':False}, {'passed':1,'skipped':0.0}, {'passed':1,'total':True},
])
def test_malformed_or_inconsistent_counts_never_clear_gate(counts):
    assert evaluate([ROW],counts,True,APPROVALS)['status']=='NOT APPROVED'

@pytest.mark.parametrize('calibration',['PASS','failed',1,[],{},None])
def test_only_explicit_boolean_calibration_pass_is_accepted(calibration):
    assert evaluate([ROW],{'passed':1},calibration,APPROVALS)['status']=='NOT APPROVED'

@pytest.mark.parametrize('row',[
    {**ROW,'mandatory':0,'scope_reason':'synthetic'},
    {**ROW,'mandatory':'false','scope_reason':'synthetic'},
    {**ROW,'id':[]}, {**ROW,'id':{}}, {**ROW,'status':[]},
    {**ROW,'evidence':'nonempty string is not an evidence list'},
    {**ROW,'evidence':['']}, {**ROW,'evidence':[None]},
])
def test_bad_requirement_rows_never_clear_gate(row):
    assert evaluate([row],{'passed':1},True,APPROVALS)['status']=='NOT APPROVED'

@pytest.mark.parametrize(('kind','expected'),[
    ('EXCEPTION','UNEXPECTED_CRASH'),('TIMEOUT','TIMEOUT'),
    ('RESOURCE','RESOURCE_LIMIT'),('HARNESS_ERROR','HARNESS_FAILURE'),
    ('unsupported','HARNESS_FAILURE'),
])
def test_observable_failures_not_hidden_by_missing_oracle(kind,expected):
    assert compare(None,Observation(kind),True)==expected

@pytest.mark.parametrize('row',[None,[],{'id':'bad','status':'PASS','evidence':None},{'id':'bad','status':'PASS','evidence':[{}]}])
def test_malformed_filesystem_evidence_is_a_controlled_failure(tmp_path,row):
    from assurance.gate import evidence_errors
    assert evidence_errors([row],tmp_path)
