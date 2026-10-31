# Data dictionary and reference schema

- `matrix_version(id, hash, created_at)`: pinned configuration snapshot, id is SHA-256 in this demo.
- `event_ingestion(ingestion_id, tenant_id, event_ref, input_hash, ingested_at, matrix_version_id)`: delivery identity. Unique per tenant, event reference and matrix version.
- `validation_result(id, ingestion_id, event_type, schema_id, schema_version, status, error_category, canonical_payload, validated_at)`: one immutable semantic outcome for each delivery identity.
- `validation_error(id, result_id, field_path, rule_code, sanitized_message)`: no raw customer/payment data.
- `normalization_audit(id, result_id, field_path, rule_id, before_digest, after_digest)`: no original values.
- `workflow_outbox(id, result_id, kind, payload, state, attempts, next_attempt_at, created_at)`: accepts `ACCEPTED_EVENT` jobs; rejection uses non-executable `QUARANTINE` kind and `QUARANTINED` state.

The production PostgreSQL migration is a DDL example only, and JSONB types must be handled by an authorized adapter rather than guessing runtime behavior.
