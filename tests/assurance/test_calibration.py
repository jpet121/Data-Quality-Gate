from assurance.calibration import run
from assurance.gate import evaluate
from assurance.compare import compare, Observation
import pytest


def test_controlled_harness_defects_detected():
    report=run()
    assert report['passed'],report
    assert report['false_positives']==0
    assert report['negative_control_denominator']==20

@pytest.mark.parametrize('status',['FAIL','BLOCKED','INCONCLUSIVE','UNPROVEN','UNKNOWN'])
def test_gate_never_clears_missing_mandatory_evidence(status):
    row={'id':'synthetic','status':status,'mandatory':True,'evidence':['synthetic-control']}
    result=evaluate([row],{'passed':1},True,{'requirements_oracle':True,'mutation_thresholds':True,'human_release':True})
    assert result['status']=='NOT APPROVED'

@pytest.mark.parametrize('tests',[{'passed':0},{'passed':1,'failed':1},{'passed':1,'errors':1},{'passed':1,'skipped':1}])
def test_gate_rejects_test_failures_empty_runs_and_skips(tests):
    row={'id':'synthetic','status':'PASS','mandatory':True,'evidence':['synthetic-control']}
    assert evaluate([row],tests,True,{'requirements_oracle':True,'mutation_thresholds':True,'human_release':True})['status']=='NOT APPROVED'

def test_gate_demands_owner_authorization():
    assert evaluate([{'id':'synthetic','status':'PASS','evidence':['control']}],{'passed':1},True,{})['status']=='NOT APPROVED'

def test_gate_positive_control_does_not_grant_approval():
    result=evaluate([{'id':'synthetic','status':'PASS','evidence':['control']}],{'passed':1},True,dict.fromkeys(['requirements_oracle','mutation_thresholds','human_release'],True))
    assert result['status']=='AUTOMATED_CRITERIA_MET'
    assert result['human_approval_granted_by_evaluator'] is False

def test_comparator_exception_is_harness_failure():
    def broken(a,b):raise RuntimeError('injected')
    assert compare(Observation('OK',1),Observation('OK',1),True,comparator=broken)=='HARNESS_FAILURE'

@pytest.mark.parametrize('path',['absent.json','../escape.json'])
def test_gate_rejects_unavailable_or_escaping_evidence(tmp_path,path):
    from assurance.gate import evidence_errors
    assert evidence_errors([{'id':'synthetic','status':'PASS','evidence':[path]}],tmp_path)

def test_gate_accepts_existing_local_control_evidence(tmp_path):
    from assurance.gate import evidence_errors
    (tmp_path/'control.json').write_text('{}')
    assert evidence_errors([{'id':'synthetic','status':'PASS','evidence':['control.json']}],tmp_path)==[]
