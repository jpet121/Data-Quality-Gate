"""Local ACID reference repository; PostgreSQL DDL is supplied as a migration blueprint."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import hashlib,json,sqlite3
from pathlib import Path
from typing import Any
from .models import ValidationResult

DDL_SQL = 'PRAGMA foreign_keys=ON;\nCREATE TABLE IF NOT EXISTS matrix_version(\n id TEXT PRIMARY KEY, hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);\nCREATE TABLE IF NOT EXISTS event_ingestion(\n ingestion_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, event_ref TEXT NOT NULL,\n input_hash TEXT NOT NULL, ingested_at TEXT NOT NULL, matrix_version_id TEXT NOT NULL REFERENCES matrix_version(id),\n UNIQUE(tenant_id,event_ref,matrix_version_id));\nCREATE INDEX IF NOT EXISTS idx_ingest_tenant_time ON event_ingestion(tenant_id,ingested_at);\nCREATE TABLE IF NOT EXISTS validation_result(\n id TEXT PRIMARY KEY, ingestion_id TEXT NOT NULL UNIQUE REFERENCES event_ingestion(ingestion_id),\n event_type TEXT, schema_id TEXT, schema_version TEXT, status TEXT NOT NULL,\n error_category TEXT, canonical_payload TEXT NOT NULL, validated_at TEXT NOT NULL);\nCREATE INDEX IF NOT EXISTS idx_result_status_time ON validation_result(status,validated_at);\nCREATE TABLE IF NOT EXISTS validation_error(\n id TEXT PRIMARY KEY, result_id TEXT NOT NULL REFERENCES validation_result(id),\n field_path TEXT NOT NULL, rule_code TEXT NOT NULL, sanitized_message TEXT NOT NULL);\nCREATE TABLE IF NOT EXISTS normalization_audit(\n id TEXT PRIMARY KEY, result_id TEXT NOT NULL REFERENCES validation_result(id),\n field_path TEXT NOT NULL, rule_id TEXT NOT NULL, before_digest TEXT NOT NULL, after_digest TEXT NOT NULL);\nCREATE TABLE IF NOT EXISTS workflow_outbox(\n id TEXT PRIMARY KEY, result_id TEXT NOT NULL REFERENCES validation_result(id),\n kind TEXT NOT NULL, payload TEXT NOT NULL, state TEXT NOT NULL,\n attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at TEXT NOT NULL, created_at TEXT NOT NULL,\n UNIQUE(result_id,kind));\nCREATE INDEX IF NOT EXISTS idx_outbox_state_time ON workflow_outbox(state,next_attempt_at);\n'

def utcnow() -> str:return datetime.now(timezone.utc).isoformat()
def uid(*items: object) -> str:return hashlib.sha256('|'.join(map(str,items)).encode()).hexdigest()

class IdempotencyConflict(ValueError): pass

class SQLiteRepository:
    def __init__(self,path:str|Path) -> None:
        self.connection=sqlite3.connect(str(path),timeout=10,isolation_level=None)
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.execute('PRAGMA busy_timeout=10000')
    def migrate(self) -> None:
        # executescript manages its own transaction: only run under controlled setup
        self.connection.executescript(DDL_SQL)
    def close(self) -> None:self.connection.close()
    def persist(self,result:ValidationResult,tenant_id:str,event_ref:str) -> str:
        c=self.connection
        if result.status == 'ACCEPTED' and (
            result.record is None or tenant_id != result.record.tenant_id or event_ref != result.record.event_id
        ):
            raise ValueError('ingestion_identity_mismatch')
        matrix_id=result.config_fingerprint
        ingestion_id=uid(tenant_id,event_ref,matrix_id)
        result_id=uid(ingestion_id,'result')
        now=utcnow()
        c.execute('BEGIN IMMEDIATE')
        try:
            c.execute('INSERT OR IGNORE INTO matrix_version(id,hash,created_at) VALUES(?,?,?)',(matrix_id,matrix_id,now))
            current=c.execute('SELECT input_hash FROM event_ingestion WHERE ingestion_id=?',(ingestion_id,)).fetchone()
            if current:
                if current[0]!=result.input_sha256:raise IdempotencyConflict('event_id_reused_with_different_content')
                c.execute('COMMIT');return 'DUPLICATE'
            c.execute('INSERT INTO event_ingestion VALUES(?,?,?,?,?,?)',(ingestion_id,tenant_id,event_ref,result.input_sha256,now,matrix_id))
            c.execute('INSERT INTO validation_result VALUES(?,?,?,?,?,?,?,?,?)',(
                result_id,ingestion_id,result.event_type,result.schema_id,result.schema_version,
                result.status,result.failure_category.value if result.failure_category else None,
                result.canonical(),now))
            for i,e in enumerate(result.errors):
                c.execute('INSERT INTO validation_error VALUES(?,?,?,?,?)',(uid(result_id,'err',i),result_id,e.path,e.code,e.message))
            for i,t in enumerate(result.transforms):
                c.execute('INSERT INTO normalization_audit VALUES(?,?,?,?,?,?)',(uid(result_id,'norm',i),result_id,t.path,t.rule_id,t.before_digest,t.after_digest))
            # Explicit quarantine record is not an executable business workflow.
            kind='ACCEPTED_EVENT' if result.status=='ACCEPTED' else 'QUARANTINE'
            safe={'result_id':result_id,'event_type':result.event_type,'status':result.status}
            c.execute('INSERT INTO workflow_outbox VALUES(?,?,?,?,?,?,?,?)',(
                uid(result_id,kind),result_id,kind,json.dumps(safe,sort_keys=True),
                'PENDING' if kind=='ACCEPTED_EVENT' else 'QUARANTINED',0,now,now))
            c.execute('COMMIT');return 'CREATED'
        except Exception:
            c.execute('ROLLBACK');raise
    def counts(self) -> dict[str, int]:
        return {name:self.connection.execute('SELECT count(*) FROM '+name).fetchone()[0] for name in
                ('event_ingestion','validation_result','validation_error','normalization_audit','workflow_outbox')}
    def claim(self,now:str|None=None) -> tuple[str, int, str] | None:
        c=self.connection
        c.execute('BEGIN IMMEDIATE')
        try:
            clock=now or utcnow()
            row=c.execute("SELECT id,attempts,payload FROM workflow_outbox WHERE state IN ('PENDING','RETRY') AND next_attempt_at<=? ORDER BY next_attempt_at,id LIMIT 1",(clock,)).fetchone()
            if row:c.execute("UPDATE workflow_outbox SET state='LEASED',attempts=attempts+1 WHERE id=?",(row[0],))
            c.execute('COMMIT');return row
        except Exception:c.execute('ROLLBACK');raise
    def finish(self,work_id:str,success:bool,max_attempts:int=3) -> str:
        c=self.connection;c.execute('BEGIN IMMEDIATE')
        try:
            row=c.execute('SELECT state,attempts FROM workflow_outbox WHERE id=?',(work_id,)).fetchone()
            if not row or row[0]!='LEASED':raise ValueError('invalid_workflow_state')
            state='DONE' if success else ('DEAD_LETTER' if row[1]>=max_attempts else 'RETRY')
            next_time=(datetime.now(timezone.utc)+timedelta(seconds=min(3600,2**row[1]))).isoformat()
            c.execute('UPDATE workflow_outbox SET state=?,next_attempt_at=? WHERE id=?',(state,next_time,work_id))
            c.execute('COMMIT');return state
        except Exception:c.execute('ROLLBACK');raise
