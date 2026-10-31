-- Reference PostgreSQL migration, apply with a controlled migration tool.
CREATE TABLE IF NOT EXISTS matrix_version(id text PRIMARY KEY, hash text NOT NULL UNIQUE, created_at timestamptz NOT NULL);
CREATE TABLE IF NOT EXISTS event_ingestion(
 ingestion_id text PRIMARY KEY, tenant_id text NOT NULL, event_ref text NOT NULL,
 input_hash char(64) NOT NULL, ingested_at timestamptz NOT NULL,
 matrix_version_id text NOT NULL REFERENCES matrix_version(id),
 UNIQUE(tenant_id,event_ref,matrix_version_id));
CREATE INDEX IF NOT EXISTS idx_ingest_tenant_time ON event_ingestion(tenant_id,ingested_at);
CREATE TABLE IF NOT EXISTS validation_result(
 id text PRIMARY KEY, ingestion_id text NOT NULL UNIQUE REFERENCES event_ingestion(ingestion_id),
 event_type text, schema_id text, schema_version text,status text NOT NULL,
 error_category text, canonical_payload jsonb NOT NULL,validated_at timestamptz NOT NULL);
CREATE INDEX IF NOT EXISTS idx_result_status_time ON validation_result(status,validated_at);
CREATE TABLE IF NOT EXISTS validation_error(
 id text PRIMARY KEY,result_id text NOT NULL REFERENCES validation_result(id),
 field_path text NOT NULL,rule_code text NOT NULL,sanitized_message text NOT NULL);
CREATE TABLE IF NOT EXISTS normalization_audit(
 id text PRIMARY KEY,result_id text NOT NULL REFERENCES validation_result(id),
 field_path text NOT NULL,rule_id text NOT NULL,before_digest char(64) NOT NULL,after_digest char(64) NOT NULL);
CREATE TABLE IF NOT EXISTS workflow_outbox(
 id text PRIMARY KEY,result_id text NOT NULL REFERENCES validation_result(id),
 kind text NOT NULL,payload jsonb NOT NULL,state text NOT NULL,
 attempts int NOT NULL DEFAULT 0,next_attempt_at timestamptz NOT NULL,created_at timestamptz NOT NULL,
 UNIQUE(result_id,kind));
CREATE INDEX IF NOT EXISTS idx_outbox_state_time ON workflow_outbox(state,next_attempt_at);
