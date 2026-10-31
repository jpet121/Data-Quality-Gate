"""Formal obligation must execute; an unavailable checker is not a passing skip."""
from assurance.formal import verify

def test_lean_gate_proofs_and_python_correspondence():
    report=verify()
    assert report['passed'] and report['checked_theorems']==9
    assert report['proof_gaps']==0
    assert report['empirical_cases']==1984
    assert report['disagreements']==[]
