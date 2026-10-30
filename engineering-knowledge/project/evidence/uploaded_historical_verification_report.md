# Structured Event Schema Validator v1.0.2 — remediation and verification

**Assessment:** October 29, 2026. **Status: NOT APPROVED for production release.**

## Scope and source authority

Combined the supplied 1.0.1 repaired application with the independently developed verification suite. Retained the original verifier byte-for-byte in `audit/upstream_test_suite.original.py`; the exact suite reconciliation is in `audit/TEST_SUITE_RECONCILIATION.diff` and input hashes in `audit/SOURCE_PROVENANCE.json`. No original application-specific functional XML was supplied. Requirements were reconciled against the supplied README, matrix, acceptance documentation and verifier. This is a synthetic demonstration, not a live system integration.

## Reproduced issues and justified changes

1. **Rejected-event idempotency collision (production bug):** default batch/index was reused across runs even when rejected raw inputs differed, producing `IdempotencyConflict`. Rejected storage identity now includes the SHA-256 of the raw input as well as its batch/index reference. Accepted events continue to use their *validated* tenant ID and event ID. `tests/regression/test_rejected_identity.py` verifies distinct invalid values are both stored, identical repeats deduplicate, and accepted cross-content event-ID collisions fail closed.
2. **Independent-suite identity mismatch (test defect):** a deterministic test and an unexecuted Hypothesis state-machine test required accepted records to persist under an arbitrary `same-ref` or `key-N`, contradicting the existing, separately verified accepted-record identity invariant. Corrected those two test setup paths to use `record.event_id`; kept the duplicate-content conflict assertions and the original suite. The application identity guard was not weakened.
3. **Two divergent standalone generators (packaging defect):** `scripts/build_standalone.py` and `tools/build_standalone.py` produced different outputs. The documented scripts entry point now delegates to the AST-checked canonical tool. Both `--check` paths agree, and the standalone is regenerated from the patched modules.
4. **Malformed Unicode in configuration (production bug):** unpaired surrogates in `version`, `schema_id`, and `schema_version` passed matrix loading and crashed canonical serialization. The loader now rejects invalid Unicode scalar strings as `ConfigError`. Public API `input_ref` metadata rejects malformed Unicode with a controlled `ValueError`. New parameterized regression tests cover both boundaries.
5. **Original fixed defects remain protected:** full event-model serialization, surrogate raw input rejection, malformed field-types handling, and nonzero CLI exit on persistence failure all remain under independent tests.

## Executed gates — final observed results

- **Combined full release suite:** `1 failed, 162 passed, 2 skipped`; exit code 1. Sole failure: mandatory Hypothesis dependency check. Logs: `audit/full_pytest_output.txt`.
- **Diagnostic non-Hypothesis checks:** `162 passed, 2 skipped, 1 deselected`; exit code 0. The deselected test is the mandatory dependency release gate; diagnostic PASS is not release approval. Logs: `audit/deterministic_pytest_output.txt`.

- Python 3.13.5 runtime, Pydantic 2.13.5, pytest 9.0.2.
- Core, regression, independent suite and generated standalone command-line tests executed.
- Seeded Unicode/structured boundary sweep: **50,000 generated cases PASS**, seed `20261029` (`audit/seeded_boundary_sweep_output.json`). The sweep is *not* Hypothesis.
- Standalone built and verified with both generator entry points; Python 3.12 syntax grammar parsed by Python 3.13, not actual 3.12 runtime execution.
- Python wheel built and tested using explicitly preinstalled external Pydantic dependencies. This is not a truly dependency-clean installation.

## Mandatory unresolved gates

1. **Hypothesis unavailable in this runtime**; dependency installation was attempted and failed. The full independent release suite deliberately fails its Hypothesis-must-run check. Property/stateful tests have not executed and cannot count as PASS.
2. **Python 3.12 runtime unavailable.** The syntax grammar check does not substitute for runtime execution.
3. **PostgreSQL driver and server unavailable.** Optional PostgreSQL path and concurrency claims remain unverified.
4. **Original application-specific functional XML specification absent.** Specification completeness and authority-based acceptance cannot be certified.
5. **No external human production-release approval provided.** Human-only authority cannot be inferred from testing.

**Interpretation:** No confirmed functional defects remain in the tests that actually executed after repair. This is not a proof of zero defects. The mandatory release gate remains **NOT APPROVED**, and the ZIP is an assurance candidate for continued testing rather than a production-certified release.

## Reproduction

```bash
python -m pip install -e '.[test]'
python tools/build_standalone.py --check
python scripts/build_standalone.py --check
python -m pytest -q test_suite.py tests
python verification/seeded_boundary_sweep.py --cases 50000 --seed 20261029
python main.py --matrix examples/matrix_v1.json --input examples/replay.jsonl
```

The complete suite must be executed on a dependency-equipped Python 3.12 environment and validated against a provisioned PostgreSQL test instance before production approval can be reconsidered. Unavailable checks must not be silently skipped or reclassified as passing.
