"""Constructive strategies and independent finite-domain reference for V:CORE12."""
from hypothesis import given,settings,example,target,strategies as st
from assurance.gate import evaluate

@st.composite
def obligations(draw):
    states=draw(st.lists(st.sampled_from(['PASS','FAIL','BLOCKED','INCONCLUSIVE','UNPROVEN']),max_size=20))
    return [{'id':f'obligation-{i}','mandatory':True,'status':s,'evidence':['control.json']} for i,s in enumerate(states)]

@settings(max_examples=150,deadline=None,derandomize=True)
@given(obligations(),st.booleans(),st.booleans(),st.booleans(),st.booleans())
@example([],True,True,True,True)
def test_gate_matches_declared_all_obligations_reference(rows,tests_ok,calibrated,oracle,mutations):
    target(len(rows),label='obligation_count')
    # Expected behavior derives from the verification contract's conjunction,
    # independent of the gate implementation and with no application oracle claim.
    expected=bool(rows) and all(r['status']=='PASS' for r in rows) and tests_ok and calibrated and oracle and mutations
    counts={'passed':1,'failed':0 if tests_ok else 1}
    approvals={'requirements_oracle':oracle,'mutation_thresholds':mutations,'human_release':True}
    result=evaluate(rows,counts,calibrated,approvals)
    assert (result['status']=='AUTOMATED_CRITERIA_MET')==expected
    # Reordering independent obligations must not change eligibility.
    permuted=evaluate(list(reversed(rows)),counts,calibrated,approvals)
    assert permuted['status']==result['status']
    # Human approval cannot be inferred from passing technical conditions.
    refused=evaluate(rows,counts,calibrated,{**approvals,'human_release':False})
    assert refused['status']=='NOT APPROVED'
