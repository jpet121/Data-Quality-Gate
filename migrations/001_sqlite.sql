PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS matrix_version(
 id TEXT PRIMARY KEY, hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS event_ingestion(
 ingestion_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, event_ref TEXT NOT NULL,
 input_hash TEXT NOT NULL, ingested_at TEXT NOT NULL, matrix_version_id TEXT NOT NULL REFERENCES matrix_version(id),
 UNIQUE(tenant_id,event_ref,matrix_version_id));
CREATE INDEX IF NOT EXISTS idx_ingest_tenant_time ON event_ingestion(tenant_id,ingested_at);
CREATE TABLE IF NOT EXISTS validation_result(
 id TEXT PRIMARY KEY, ingestion_id TEXT NOT NULL UNIQUE REFERENCES event_ingestion(ingestion_id),
 event_type TEXT, schema_id TEXT, schema_version TEXT, status TEXT NOT NULL,
 error_category TEXT, canonical_payload TEXT NOT NULL, validated_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_result_status_time ON validation_result(status,validated_at);
CREATE TABLE IF NOT EXISTS validation_error(
 id TEXT PRIMARY KEY, result_id TEXT NOT NULL REFERENCES validation_result(id),
 field_path TEXT NOT NULL, rule_code TEXT NOT NULL, sanitized_message TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS normalization_audit(
 id TEXT PRIMARY KEY, result_id TEXT NOT NULL REFERENCES validation_result(id),
 field_path TEXT NOT NULL, rule_id TEXT NOT NULL, before_digest TEXT NOT NULL, after_digest TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS workflow_outbox(
 id TEXT PRIMARY KEY, result_id TEXT NOT NULL REFERENCES validation_result(id),
 kind TEXT NOT NULL, payload TEXT NOT NULL, state TEXT NOT NULL,
 attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(result_id,kind));
CREATE INDEX IF NOT EXISTS idx_outbox_state_time ON workflow_outbox(state,next_attempt_at);
