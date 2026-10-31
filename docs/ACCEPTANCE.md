# Executable acceptance matrix

| Contract checkpoint | Expected predicate | Concrete verification |
|---|---|---|
| Load matrix | valid data-only registry + stable SHA-256 fingerprint | `test_golden_valid`, `test_config_reject_unknown_registry` |
| Unique schema match | exactly one highest-priority match | `test_ambiguity`, `test_unsupported_free_prose` |
| Lexer failures | malformed/duplicate/alias collision reject | `test_parser_quote_and_escape`, `test_duplicate_even_identical` |
| Strict v2 type check | bypass parser string money/naive time rejected | `test_strict_model_without_lexer` |
| One event independent | valid-invalid-valid → two accepted | `test_batch_isolation` |
| Same payload + config | same canonical output | `test_determinism` |
| No raw secrets in diagnostics | no customer/payment raw values in errors | `test_no_sensitive_diagnostics` |
| ACID relational storage | results/errors/audits/outbox atomic, FK rejects | `test_transactions_idempotency_and_outbox`, `test_fault_rollback_on_invalid_fk` |
| Duplicate delivery | hash match duplicate; key collision rolls back | `test_id_collision_rollback` |
| Only accepted outbox | rejection creates quarantine not accepted job | `test_transactions_idempotency_and_outbox` |
| Bounded retry | retry then DEAD_LETTER at max attempts | `test_retry_dead_letter` |
| Differential oracle | independent lexer over shared subset | `test_differential_restricted_subset` |
| Hypothesis fuzz | Unicode, duplicate keys, stable lexing, stateful evolution | `tests/property/test_properties.py` (optional dependency) |
| Scale | measured seedable parsing and SQLite benchmark | `benchmarks/benchmark.py --count N --seed 1701 [--db]` |

**Not accepted as proven by this sample:** PostgreSQL production execution, migrations rollback under production data, two concurrent PostgreSQL transactions, durable consumer crash-reclamation, full high-volume stress, complete security posture or live event schema governance. The package documents these as open requirements instead of passing them by assertion.

## Repair-regression acceptance

- Full accepted record round-trip without dropped event-specific fields: `test_accepted_serialization_preserves_every_event_field`, `test_persistence_retains_complete_accepted_record`.
- Invalid Unicode, sanitized errors, nonzero failure exit and initialization failure: `tests/regression/test_hardening.py`, `tests/unit/test_regressions.py`.
- Standalone isolated replay with SQLite and parity: `test_standalone_cli_without_local_package`, `test_standalone_script_matches_package_replay`.
- Matrix registry consistency and cross-tenant persistence identity: `test_config_rejects_type_punning`, `test_storage_cannot_persist_event_under_other_tenant_or_event_id`.
- Fault injection and deterministic randomized mutation: `test_storage_transaction_rollback_on_outbox_insert_failure`, `test_deterministic_random_fuzz_no_crash`, `test_seeded_structured_mutation_stress`.

## Owner-delegated input profile clarification

Money is positive, at most 9999999999999.99, and uses integer notation or at most two fractional digits. The same lexical rule applies to quoted and numeric nested unit prices. Timestamps use uppercase T/Z, at most six fractional-second digits, offsets at most ±14:00 (zero minutes at ±14 hours), valid calendar dates and seconds 00–59. These explicit limits retain the pre-existing boundary behavior; the owner delegated this reconciliation decision during verification.
