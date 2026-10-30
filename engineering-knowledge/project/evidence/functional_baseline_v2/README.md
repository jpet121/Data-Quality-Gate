# Current XML audit status

**NOT APPROVED.** Final extracted-candidate run: 211 tests passed, no failures/errors/skips. See [FINAL_EVIDENCE_REPORT.md](FINAL_EVIDENCE_REPORT.md) and [REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md) for unresolved mandatory development and verification obligations. The sections and reports below describe earlier historical candidate states. Installation and audit commands are in [ASSURANCE_OPERATOR_GUIDE.md](ASSURANCE_OPERATOR_GUIDE.md).

# Structured Event Schema Validator — repaired synthetic B2B demonstration

**v1.0.2 corrected assurance candidate; NOT APPROVED for production.**

**Current independent results:** 194 tests passed on Python 3.12, including Hypothesis and isolated PostgreSQL. Two PostgreSQL defects were repaired. See `INDEPENDENT_VERIFICATION_REPORT.md` for current evidence and the missing-specification blocker. The older verification statements below are historical and are superseded by that report.

**Historical candidate status:** The full release gate remains red because Hypothesis is absent, and Python 3.12 runtime, PostgreSQL integration, original validator-specific XML requirements and human release approval remain unverified. See `docs/REMEDIATION_AUDIT_2026_10_29.md`.

A Python 3.12+ / Pydantic v2 demonstration of deterministic ingestion, explicit rule-matrix classification, strict typed validation, failure separation, safe trace metadata, SQLite ACID persistence and a disabled-by-default transactional-outbox stub. Designed as a technical portfolio example for hiring managers and engineers. **The included event types, currencies, identifiers, workflow labels and example thresholds are synthetic and illustrative. They are NOT production integration or business rules.** Do not point at live ERP/payment/WMS/carrier systems without organization-governed configuration, model review, security authorization and connector development.

## Quick start

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
python main.py --matrix examples/matrix_v1.json --input examples/replay.jsonl --db demo.sqlite
pytest -q
python benchmarks/benchmark.py --count 1000 --seed 1701
python benchmarks/benchmark.py --count 300 --seed 1701 --db
```

The `--db` flag is optional; without it, validation produces stdout JSONL only. CLI `--input -` reads stdin. The `main.py` entry point is now a generated, standalone application; it runs without an editable installation or `PYTHONPATH=src`, provided Pydantic v2 is installed. The package remains separately importable for development and tests. The Python API is `load_matrix(path)`, `validate(raw,input_ref,cfg,index=0)`, `validate_many(iterable,batch_ref,cfg)` and `SQLiteRepository(path)`. For Windows, substitute activation syntax accordingly. The package never sends network traffic. `workflow.dispatch_once(repo)` returns `DISABLED`; to exercise workflow locally, pass `LocalStubSink()`.

## Pipeline and trust boundaries

1. **ConfigLoader / MatrixRegistry** loads JSON, rejects duplicate keys, unsafe matcher instructions, unapproved schema bindings and budgets, hashes a canonical versioned snapshot. Config is data, never imported code. Only exact-match event classification is supported; regex execution is disallowed.
2. **Ingestor** computes hash over the original string and guards 4,096 UTF-8 bytes, 32 tokens and 10,000 events per batch in demo v1. The configured budgets can be reduced. Over-limit batches raise a typed `ValueError` at the generator boundary and never silently truncate.
3. **Lexer/Parser** accepts ASCII field keys separated by `|` and `=`. Quoted values permit embedded `|` and only escaped `\\`, `\"`, and `\|`; plain values cannot have interior whitespace. A single trailing delimiter, arbitrary prose, duplicate keys, unclosed quotes or stray escapes rejects deterministically.
4. **Normalizer** applies only declared aliases `event → event_type`, `tenant → tenant_id`, `order → order_id`; alias collisions reject. Whitespace surrounding values is trimmed only outside quotes. `occurred_at`, money and integer lexemes are decoded from declared patterns; no implicit timezone, float money or numeric exponent allowed.
5. **Classifier** examines all matching configured exact event-type rules, chooses the highest *explicit* priority and rejects ties (`AMBIGUOUS_EVENT`). No match is `UNSUPPORTED_EVENT`. Schema resolution never uses a best-effort fallback.
6. **StrictValidator** executes `model_validate(strict=True)` on frozen, extra-forbidden Pydantic v2 records. Each example type is a separate registry entry. Decimal money is greater than zero, limited to two fractional digits and at most 13 integer digits (maximum 9999999999999.99), positive integral quantities bounded at one million, calendar timestamps timezone-aware. Optional `lines_json` is parsed with unique-key checks and exact Decimal numbers; each `unit_price` may be a money string or a JSON number using the same integer-or-two-decimal money lexeme, without exponents. JSON integer prices convert exactly to Decimal. Totals must match `gross_amount` exactly.
7. **ResultBuilder/Audit** returns `ACCEPTED` or `REJECTED` with one enumerated failure category, a schema fingerprint, safe path and rule code, token *names* only in trace, and before/after **hashes** for transformations. No raw invalid values or customer/payment references are printed inside error text; accepted structured records include synthetic references by design.
8. **Repository** uses SQLite with WAL-independent `BEGIN IMMEDIATE` serialized writes and FK checks. Results, error rows, transforms and accepted/quarantine outbox rows commit atomically. Idempotency is `(tenant_id,event_ref,matrix_version_id)`; equal hashes return `DUPLICATE`, content changes raise `IdempotencyConflict` and roll back.
9. **Workflow** has `PENDING → LEASED → DONE/RETRY/DEAD_LETTER`; rejected inputs create `QUARANTINED` rows, never accepted-event jobs. The stub sink is manually passed and has no external effects. A production consumer must add explicit authorized connectors, safety guards, leases with recovery/reclaim and independent idempotent delivery acknowledgment before deployment.

## Demo data contract (not a live enterprise schema)

Every type requires `event_type, event_id, tenant_id, order_id, occurred_at, source`. Identifiers match `[A-Za-z0-9][A-Za-z0-9_-]*` and length 1–64. `source ∈ {ERP,PAYMENT,WMS,CARRIER}`. `occurred_at` uses a strict RFC3339-style calendar-time profile: uppercase `T` and `Z`, zero to six fractional-second digits, offsets within ±14:00 (only zero minutes at ±14 hours), and seconds 00–59; leap-second notation is not supported. All other keys are forbidden unless declared per type:

| Event | Required additional fields | Optional | Semantic guard |
|---|---|---|---|
| ORDER_CREATED | customer_ref, gross_amount, currency | lines_json | currency USD; Decimal gross > 0; optional line subtotal exact match |
| PAYMENT_AUTHORIZED | payment_ref, authorized_amount, currency | — | currency USD; Decimal amount > 0 |
| INVENTORY_RESERVED | warehouse_ref, sku_code, quantity | — | integer 1–1,000,000 |
| SHIPMENT_DISPATCHED | shipment_ref, carrier_code, tracking_ref, quantity | — | integer 1–1,000,000 |
| ORDER_CANCELLED | reason | — | reason CUSTOMER_REQUEST / FULFILLMENT_FAILURE |

`examples/valid.jsonl` includes each of the five distinct event types. `examples/invalid.jsonl` has missing, duplicate, alias-conflict, wrong-currency, invalid-offset, precision, total-mismatch, unsupported and free-form cases. `examples/replay.jsonl` is a mixed three-element batch. `examples/matrix.schema.json` provides a machine-readable JSON Schema for the *matrix* and runtime adds registry/cross-field verification. To extend the engine, new business rules need approved model registry entries and a compatible matrix — no arbitrary Python imports from configuration. Changing schema versions requires explicit migration/review; nothing automatically translates live business events.

## Persistence, workflow and safe operations

`migrations/001_sqlite.sql` is also embedded in the SQLite adapter for standalone execution, and `SQLiteRepository.migrate` initializes a new local database; `migrations/001_postgresql.sql` is a production-style **DDL blueprint**, not a deployed or integration-verified production migration. For operational production use, integration-test and harden the included optional psycopg repository, controlled migration/rollback path, authenticated source identity, tenant partitioning/access controls, encryption at rest, raw-payload vault references and a reclaimed-lease outbox consumer. Do not store full raw events in log messages. The example retains validated synthetic values in the local DB; it is not intended to hold real secrets.

Useful SQLite exploration:
```sql
SELECT status, count(*) FROM validation_result GROUP BY status;
SELECT kind, state, count(*) FROM workflow_outbox GROUP BY kind,state;
SELECT field_path,rule_code,count(*) FROM validation_error GROUP BY field_path,rule_code;
SELECT tenant_id,event_ref,input_hash FROM event_ingestion ORDER BY ingested_at LIMIT 20;
```

## Verification and limitations

- Unit tests cover golden success/rejection, parser errors, strict Pydantic bypass, aliases, determinism, unauthorized registry and ambiguous matchers.
- Integration tests cover SQLite foreign keys, atomic result/outbox insertion, replay, duplicate collision rollback and retries to dead letter.
- Differential tests use a truly separate split-based reference implementation only over the deliberately unquoted and ambiguity-free subset where both semantics agree.
- Hypothesis tests under `tests/property` cover Unicode, duplicates, determinism and a stateful parser model; the suite is explicitly skipped if Hypothesis is unavailable. **Requires installing the optional `hypothesis` dependency before those tests can execute**; no claim is made for unexecuted property tests. Reproduction uses explicit `@seed` and Hypothesis examples/settings.
- Benchmarks report actual local CPU and wall time, events/sec, p50/p95 latency, tracemalloc peak and DB row counts. These are environment-specific local observations, not scaling or SLO guarantees. Use `--seed` to replay synthetic selection.
- No live PostgreSQL, distributed concurrency, lease crash recovery, production connector, real user permission framework, audit ledger encryption, external API or genuine production source config is provided. Startup tests require authorized configuration for any non-demo schema. Tests conducted under Python 3.13 are not direct Python 3.12 certification.

See `docs/ACCEPTANCE.md` for test predicates and `docs/SECURITY.md` for controls.

### Optional PostgreSQL repository

`src/event_validator/postgres.py` supplies a candidate psycopg 3 repository against `migrations/001_postgresql.sql`, using parameterized statements, transactional insert/outbox and `FOR UPDATE SKIP LOCKED` work claiming. It is **not tested here** because no PostgreSQL server or psycopg driver was available. It remains a deployment candidate, not validated production infrastructure; in particular recoverable expired leases, deployment migration reversals and multi-worker idempotent delivery are outside this demo.

## 1.0.2 assurance-candidate status

See `docs/REMEDIATION_AUDIT_2026_10_29.md` for the latest remediation and actual release gate; `docs/REPAIR_RELEASE_REPORT.md` is the source 1.0.1 report retained for provenance. The standalone `main.py` is reproducibly built from the modular source with `python scripts/build_standalone.py`; it is tested under Python isolated mode with no local package import. This is an executable local demonstration, **not a certified production integration**.
