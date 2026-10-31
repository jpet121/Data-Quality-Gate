from assurance.idempotency import verify

def test_checked_idempotency_model_matches_sqlite_and_atomic_state():
    report=verify()
    assert report['checked_theorems']==5 and report['passed']
    assert report['compared_operations']==2005 and report['disagreements']==0
