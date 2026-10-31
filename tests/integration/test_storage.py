import sqlite3
import pytest
from event_validator import validate,validate_many
from event_validator.storage import SQLiteRepository,IdempotencyConflict
from event_validator.workflow import dispatch_once,LocalStubSink

@pytest.fixture
def repo(tmp_path):
    r=SQLiteRepository(tmp_path/'test.sqlite');r.migrate();yield r;r.close()

def test_transactions_idempotency_and_outbox(repo,cfg,valid,invalid):
    good=validate(valid[0],'ref',cfg);bad=validate(invalid[0],'bad',cfg)
    assert repo.persist(good,'TEN-ACME','EVT-001')=='CREATED'
    assert repo.persist(good,'TEN-ACME','EVT-001')=='DUPLICATE'
    assert repo.persist(bad,'REJECTED','bad')=='CREATED'
    counts=repo.counts()
    assert counts['event_ingestion']==2 and counts['validation_result']==2
    assert repo.connection.execute("SELECT count(*) FROM workflow_outbox WHERE kind='ACCEPTED_EVENT'").fetchone()[0]==1
    assert repo.connection.execute("SELECT count(*) FROM workflow_outbox WHERE kind='QUARANTINE'").fetchone()[0]==1
    assert dispatch_once(repo,None)=='DISABLED'
    sink=LocalStubSink()
    assert dispatch_once(repo,sink)=='DONE'
    assert len(sink.delivered)==1
    assert dispatch_once(repo,sink)=='EMPTY'

def test_id_collision_rollback(repo,cfg,valid):
    a=validate(valid[0],'ref',cfg);b=validate(valid[0].replace('25.00','26.00'),'other',cfg)
    repo.persist(a,'TEN-ACME','EVT-001')
    with pytest.raises(IdempotencyConflict):repo.persist(b,'TEN-ACME','EVT-001')
    assert repo.counts()['event_ingestion']==1

def test_fault_rollback_on_invalid_fk(repo,cfg,valid):
    good=validate(valid[0],'r',cfg)
    repo.persist(good,'TEN-ACME','EVT-001')
    with pytest.raises(sqlite3.IntegrityError):
        repo.connection.execute("INSERT INTO validation_error VALUES('invalid','nonexistent','x','x','x')")
    assert repo.counts()['validation_error']==0

def test_retry_dead_letter(repo,cfg,valid):
    repo.persist(validate(valid[0],'a',cfg),'TEN-ACME','EVT-001')
    class FailSink:
        def deliver(self,message):return False
    # Force retry due now for the deterministic local test.
    assert dispatch_once(repo,FailSink())=='RETRY'
    repo.connection.execute("UPDATE workflow_outbox SET next_attempt_at='2000-01-01T00:00:00+00:00'")
    assert dispatch_once(repo,FailSink())=='RETRY'
    repo.connection.execute("UPDATE workflow_outbox SET next_attempt_at='2000-01-01T00:00:00+00:00'")
    assert dispatch_once(repo,FailSink())=='DEAD_LETTER'
    assert dispatch_once(repo,FailSink())=='EMPTY'


def test_persistence_retains_complete_accepted_record(repo,cfg,valid):
    import json
    accepted=validate(valid[0],'identity',cfg)
    assert repo.persist(accepted,'TEN-ACME','EVT-001') == 'CREATED'
    payload=repo.connection.execute('SELECT canonical_payload FROM validation_result').fetchone()[0]
    doc=json.loads(payload)
    assert doc['record']['gross_amount']=='25.00'
    assert doc['record']['customer_ref']=='CUST-FAKE-11'
    assert doc['record']['lines_json'][0]['quantity']==2
