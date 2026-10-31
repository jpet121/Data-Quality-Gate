"""Independent PostgreSQL gates. SESV_TEST_DSN must select a disposable database."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from pathlib import Path
import pytest
import psycopg
from event_validator import validate
from event_validator.postgres import PostgreSQLRepository
from event_validator.storage import IdempotencyConflict
from event_validator.workflow import dispatch_once, LocalStubSink

@pytest.fixture
def pg():
    dsn = os.environ.get('SESV_TEST_DSN')
    if not dsn:
        pytest.fail('SESV_TEST_DSN required for mandatory PostgreSQL verification')
    r = PostgreSQLRepository(dsn)
    r.conn.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public')
    r.conn.execute((Path(__file__).resolve().parents[2]/'migrations/001_postgresql.sql').read_text())
    yield r
    r.close()

def counts(pg):
    return tuple(pg.conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in
                 ('event_ingestion','validation_result','workflow_outbox'))

def test_pg_persistence_reopen(pg,cfg,valid,invalid):
    good=validate(valid[0],'good',cfg)
    assert pg.persist(good,'TEN-ACME','EVT-001')=='CREATED'
    assert pg.persist(good,'TEN-ACME','EVT-001')=='DUPLICATE'
    assert pg.persist(validate(invalid[0],'bad',cfg),'REJECTED','bad')=='CREATED'
    pg.close(); pg.conn=psycopg.connect(os.environ['SESV_TEST_DSN'],autocommit=True)
    doc=pg.conn.execute("SELECT canonical_payload FROM validation_result WHERE status='ACCEPTED'").fetchone()[0]
    import json
    assert doc==json.loads(good.canonical())
    assert counts(pg)==(2,2,2)
    assert pg.conn.execute("SELECT state FROM workflow_outbox WHERE kind='QUARANTINE'").fetchone()[0]=='QUARANTINED'

def test_pg_collision_and_identity(pg,cfg,valid):
    a=validate(valid[1],'a',cfg)
    pg.persist(a,a.record.tenant_id,a.record.event_id)
    # Force an actual content difference without relying on a fixture amount.
    b=validate(valid[1]+' ','b',cfg)
    with pytest.raises(IdempotencyConflict): pg.persist(b,a.record.tenant_id,a.record.event_id)
    with pytest.raises(ValueError): pg.persist(a,'OTHER',a.record.event_id)
    assert counts(pg)==(1,1,1)

def test_pg_fault_rollback(pg,cfg,valid):
    pg.conn.execute("CREATE FUNCTION fail_outbox() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'injected'; END $$")
    pg.conn.execute('CREATE TRIGGER fail_outbox BEFORE INSERT ON workflow_outbox FOR EACH ROW EXECUTE FUNCTION fail_outbox()')
    a=validate(valid[0],'a',cfg)
    with pytest.raises(psycopg.Error): pg.persist(a,a.record.tenant_id,a.record.event_id)
    assert counts(pg)==(0,0,0)
    assert pg.conn.execute('SELECT count(*) FROM matrix_version').fetchone()[0]==0
    pg.conn.execute('DROP TRIGGER fail_outbox ON workflow_outbox')
    assert pg.persist(a,a.record.tenant_id,a.record.event_id)=='CREATED'

def test_pg_fk(pg):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        pg.conn.execute("INSERT INTO validation_error VALUES('bad','absent','x','x','x')")

@pytest.mark.parametrize('round_number',range(5))
@pytest.mark.parametrize('conflicting',[False,True])
def test_pg_concurrent_insert(pg,cfg,valid,conflicting,round_number):
    barrier=Barrier(8)
    def run(i):
        r=PostgreSQLRepository(os.environ['SESV_TEST_DSN'])
        try:
            a=validate(valid[1]+(' '*i if conflicting else ''),'race',cfg)
            barrier.wait(timeout=10)
            try: return r.persist(a,a.record.tenant_id,a.record.event_id)
            except IdempotencyConflict: return 'CONFLICT'
        finally: r.close()
    with ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(run,range(8)))
    assert results.count('CREATED')==1
    assert results.count('CONFLICT' if conflicting else 'DUPLICATE')==7
    assert counts(pg)==(1,1,1)

def test_pg_concurrent_claim_and_finish(pg,cfg,valid):
    for i in range(12):
        a=validate(valid[1].replace('EVT-002',f'RACE-{i}'),'race',cfg)
        pg.persist(a,a.record.tenant_id,a.record.event_id)
    def run(_):
        r=PostgreSQLRepository(os.environ['SESV_TEST_DSN'])
        try: return r.claim()
        finally: r.close()
    with ThreadPoolExecutor(max_workers=8) as pool: rows=list(pool.map(run,range(20)))
    rows=[r for r in rows if r]
    assert len(rows)==12 and len({r[0] for r in rows})==12
    assert all(r[1]==1 for r in rows)
    for row in rows: assert pg.finish(row[0],True)=='DONE'
    with pytest.raises(ValueError): pg.finish(rows[0][0],True)

def test_pg_dispatch(pg,cfg,valid):
    a=validate(valid[1],'a',cfg); pg.persist(a,a.record.tenant_id,a.record.event_id)
    sink=LocalStubSink()
    assert dispatch_once(pg,None)=='DISABLED'
    assert dispatch_once(pg,sink)=='DONE'
    assert len(sink.delivered)==1
    assert dispatch_once(pg,sink)=='EMPTY'

def test_pg_retry_dead_letter(pg,cfg,valid):
    a=validate(valid[1],'a',cfg); pg.persist(a,a.record.tenant_id,a.record.event_id)
    for expected in ['RETRY','RETRY','DEAD_LETTER']:
        row=pg.claim(); assert row
        assert pg.finish(row[0],False)==expected
        pg.conn.execute("UPDATE workflow_outbox SET next_attempt_at=now()-interval '1 minute'")
    assert pg.claim() is None
