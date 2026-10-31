"""Optional PostgreSQL repository port; requires psycopg and managed migrations.

Integration-verified against a disposable PostgreSQL 17 instance; production
deployment and migration governance remain outside the local demo scope.
Use migrations/001_postgresql.sql under the organization's migration process.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone,timedelta
from typing import Any
from .models import ValidationResult
from .storage import uid,IdempotencyConflict

try:
    import psycopg as _psycopg
    from psycopg.types.json import Jsonb as _Jsonb
except ImportError:  # optional dependency
    psycopg: Any = None
    Jsonb: Any = None
else:
    psycopg = _psycopg
    Jsonb = _Jsonb

class PostgreSQLRepository:
    def __init__(self,dsn:str) -> None:
        if psycopg is None:raise RuntimeError('Install structured-event-schema-validator[postgres] for PostgreSQL')
        self.conn=psycopg.connect(dsn,autocommit=True)
    def close(self) -> None:self.conn.close()
    def persist(self,result:ValidationResult,tenant_id:str,event_ref:str)->str:
        if result.status == 'ACCEPTED' and (
            result.record is None or tenant_id != result.record.tenant_id or event_ref != result.record.event_id
        ):
            raise ValueError('ingestion_identity_mismatch')
        matrix_id=result.config_fingerprint
        ingestion_id=uid(tenant_id,event_ref,matrix_id)
        result_id=uid(ingestion_id,'result')
        now=datetime.now(timezone.utc)
        with self.conn.transaction():
            with self.conn.cursor() as c:
                c.execute('INSERT INTO matrix_version(id,hash,created_at) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(matrix_id,matrix_id,now))
                c.execute('SELECT input_hash FROM event_ingestion WHERE ingestion_id=%s FOR UPDATE',(ingestion_id,))
                existing=c.fetchone()
                if existing:
                    if existing[0]!=result.input_sha256:raise IdempotencyConflict('event_id_reused_with_different_content')
                    return 'DUPLICATE'
                # Race-safe insertion under the tenant/event/matrix unique constraint.
                c.execute('INSERT INTO event_ingestion VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id,event_ref,matrix_version_id) DO NOTHING RETURNING ingestion_id',(
                    ingestion_id,tenant_id,event_ref,result.input_sha256,now,matrix_id))
                if not c.fetchone():
                    c.execute('SELECT input_hash FROM event_ingestion WHERE tenant_id=%s AND event_ref=%s AND matrix_version_id=%s FOR UPDATE',(tenant_id,event_ref,matrix_id))
                    row=c.fetchone()
                    if not row or row[0]!=result.input_sha256:raise IdempotencyConflict('event_id_reused_with_different_content')
                    return 'DUPLICATE'
                c.execute('INSERT INTO validation_result VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(
                    result_id,ingestion_id,result.event_type,result.schema_id,result.schema_version,result.status,
                    result.failure_category.value if result.failure_category else None,Jsonb(json.loads(result.canonical())),now))
                for i,error in enumerate(result.errors):
                    c.execute('INSERT INTO validation_error VALUES(%s,%s,%s,%s,%s)',(
                        uid(result_id,'err',i),result_id,error.path,error.code,error.message))
                for i,t in enumerate(result.transforms):
                    c.execute('INSERT INTO normalization_audit VALUES(%s,%s,%s,%s,%s,%s)',(
                        uid(result_id,'norm',i),result_id,t.path,t.rule_id,t.before_digest,t.after_digest))
                kind='ACCEPTED_EVENT' if result.status=='ACCEPTED' else 'QUARANTINE'
                payload=Jsonb({'result_id':result_id,'event_type':result.event_type,'status':result.status})
                c.execute('INSERT INTO workflow_outbox VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(
                    uid(result_id,kind),result_id,kind,payload,'PENDING' if kind=='ACCEPTED_EVENT' else 'QUARANTINED',0,now,now))
                return 'CREATED'
    def claim(self) -> tuple[str, int, dict[str, Any]] | None:
        with self.conn.transaction():
            with self.conn.cursor() as c:
                c.execute('''WITH chosen AS (
                    SELECT id FROM workflow_outbox WHERE state IN ('PENDING','RETRY') AND next_attempt_at<=now()
                    ORDER BY next_attempt_at,id FOR UPDATE SKIP LOCKED LIMIT 1)
                    UPDATE workflow_outbox AS w SET state='LEASED',attempts=attempts+1
                    FROM chosen WHERE w.id=chosen.id RETURNING w.id,w.attempts,w.payload''')
                return c.fetchone()
    def finish(self,work_id:str,success:bool,max_attempts:int=3)->str:
        with self.conn.transaction():
            with self.conn.cursor() as c:
                c.execute('SELECT attempts FROM workflow_outbox WHERE id=%s AND state=%s FOR UPDATE',(work_id,'LEASED'))
                row=c.fetchone()
                if not row:raise ValueError('invalid_workflow_state')
                state='DONE' if success else ('DEAD_LETTER' if row[0]>=max_attempts else 'RETRY')
                c.execute('UPDATE workflow_outbox SET state=%s,next_attempt_at=%s WHERE id=%s',(
                    state,datetime.now(timezone.utc)+timedelta(seconds=min(3600,2**row[0])),work_id))
                return state
