# Verification test traceability

| Behavioral contract | Test-suite checkpoints |
|---|---|
| Matrix integrity and approved bindings | `test_matrix_fingerprint_and_registry_binding`, `test_config_*`, `test_ambiguity_fails_closed`, `test_release_malformed_field_type_matrix_is_typed_config_error` |
| All five schema models and strict typed Pydantic | `test_each_example_valid_and_strictly_typed`, `test_strict_pydantic_rejects_string_decimal_and_naive_datetime` |
| Reject malformed, unknown or missing data | `test_each_golden_invalid_rejects`, `test_no_guessing_missing_values`, `test_malformed_lexer_rejected_with_typed_fault`, `test_alias_collision_and_exact_duplicate_reject` |
| Monetary and integer numeric boundaries | `test_money_*`, `test_quantity_*` |
| Offset-aware temporal acceptance | `test_timestamp_*` |
| Nested uniqueness and total reconciliation | `test_nested_duplicate_key_and_total_mismatch_reject` |
| Deterministic outputs, stable semantics | `test_repeatability_and_permutation_metamorphic`, `test_batch_isolation_and_exact_output_count` |
| Independent lexer differential oracle | `test_independent_restricted_lexer_differential`, `test_oracle_must_detect_mutated_output`, `test_hypothesis_differential_lexing_in_valid_domain` |
| Input budget boundaries and safe Unicode | `test_invalid_input_types_and_bytes_are_bounded`, `test_over_limit_batch_raises_without_truncation`, `test_release_invalid_unicode_must_not_crash`, `test_hypothesis_unicode_never_crashes` |
| No raw secret in diagnostics | `test_no_secret_leak_in_errors_or_trace` |
| Accepted JSON result fidelity | `test_release_serialization_must_preserve_all_event_fields` |
| Atomic SQLite and idempotency | `test_sqlite_atomic_persistence_and_quarantine`, `test_sqlite_idempotency_collision_rolls_back`, `test_sqlite_foreign_key_enforced`, `test_persistence_rejects_duplicate_result_with_new_content`, `TestRepositoryStateMachine` |
| Workflow fail-closed/quarantine/dead letter | `test_sqlite_atomic_persistence_and_quarantine`, `test_workflow_retries_and_dead_letter` |
| Real CLI input/output and persistence | `test_cli_complete_e2e`, `test_release_cli_rejected_inputs_use_collision_safe_identity` |
| Property, shrinking and stateful traces | `test_hypothesis_*`, `TestLexerStateMachine`, `TestRepositoryStateMachine` (not executed without Hypothesis) |
| Release dependency fail-closed | `test_release_hypothesis_dependency_must_be_installed` |

Limitations: Not a Lean formal proof; no production PostgreSQL execution, distributed workers, high-volume stress or externally authenticated real-event matrix. An independent restricted-domain oracle provides meaningful but limited diversity; it does not verify quote processing beyond deterministic checks.
