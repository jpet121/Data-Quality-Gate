# Defect, failure and repair ledger

Evidence references are relative to the portable knowledge package. Tests listed in JSON are actual passing cases from the completed post-upload run, not reruns performed for knowledge capture. The immutable original delivery contains the complete code, tests and earlier logs.

## D01 — application

**Status:** Repaired and regression verified in completed project

**Defect:** PostgreSQL jobs retried instead of delivering decoded JSONB records.

**Reproduction evidence:** project/evidence/reproductions/pg_live.txt

**Root cause:** Dispatcher unconditionally called json.loads although psycopg returns a dict for JSONB.

**Repair:** Accept decoded dict or serialized JSON at the adapter boundary.

**Regression verification:** 3 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Test real backend data representations; normalize at the correct boundary.

## D02 — application/concurrency

**Status:** Repaired and regression verified in completed project

**Defect:** Concurrent PostgreSQL matrix registration could raise a hash unique-constraint violation.

**Reproduction evidence:** project/evidence/reproductions/release_after_fix.txt

**Root cause:** ON CONFLICT(id) omitted the separate unique hash constraint reached by racing clients.

**Repair:** Use untargeted ON CONFLICT DO NOTHING for the two fingerprint-derived unique constraints; retain ingestion content/identity conflict checks.

**Regression verification:** 10 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Test all relevant uniqueness constraints with genuinely competing independent connections.

## D03 — architecture/type contract

**Status:** Repaired and regression verified in completed project

**Defect:** Callable annotations and dependency boundaries did not fully meet Development requirements.

**Reproduction evidence:** project/evidence/observations/APPLICATION_REMEDIATION.diff; immutable delivery final_evidence/mypy_initial.txt

**Root cause:** Untyped callables and policy dependencies on concrete repository/configuration I/O modules.

**Repair:** Annotate nine modules; use structural repository/sink protocols; move immutable ConfigSnapshot into the domain model and preserve re-exports.

**Regression verification:** 3 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Use justified interfaces and inward dependencies; static types supplement runtime validation.

## D04 — application/input grammar

**Status:** Repaired and regression verified in completed project

**Defect:** Nested numeric money accepted exponent or excessive scale lexemes rejected by the top-level contract.

**Reproduction evidence:** project/evidence/observations/nested_money_reproduction.txt

**Root cause:** JSON parse_float converted spelling to Decimal before applying the shared lexical contract.

**Repair:** Route decimal JSON tokens through the same money decoder.

**Regression verification:** 10 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** A shared requirement must be enforced through every representation and nesting path.

## D05 — application/input grammar

**Status:** Repaired and regression verified in completed project

**Defect:** Valid integer-notation JSON money was rejected.

**Reproduction evidence:** project/evidence/observations/json_integer_money_reproduction.txt

**Root cause:** Default JSON integer values were not converted to exact money; bool needs separate exclusion because it is an int subclass.

**Repair:** Convert values whose exact type is int to Decimal, preserving strict bool/zero/negative rejection.

**Regression verification:** 8 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Pair negative tests with valid neighboring representations; avoid bool/int type confusion.

## D06 — application/arithmetic

**Status:** Repaired and regression verified in completed project

**Defect:** Valid exact line totals were rejected under low ambient Decimal precision.

**Reproduction evidence:** project/evidence/observations/decimal_context_reproduction.json

**Root cause:** Decimal multiplication/summation inherited mutable rounding context.

**Repair:** Use integer-cent arithmetic based on exact ratios; independent reference uses Fraction.

**Regression verification:** 12 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Exact invariants must not accidentally depend on ambient numerical context.

## D07 — application/resource control

**Status:** Repaired and regression verified in completed project

**Defect:** Oversized config could exhaust memory before its size-limit rejection.

**Reproduction evidence:** project/evidence/observations/config_resource_reproduction.txt

**Root cause:** The entire file was allocated before its byte limit was checked.

**Repair:** Read at most limit plus one byte before validation; bounded-memory regression uses a sparse oversize file.

**Regression verification:** 1 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Enforce allocation/read bounds before doing the expensive operation.

## D08 — application/error boundary

**Status:** Repaired and regression verified in completed project

**Defect:** Deep malformed JSON could leak RecursionError instead of a typed failure.

**Reproduction evidence:** project/evidence/observations/config_resource_reproduction.txt; immutable delivery nested-event regression evidence

**Root cause:** Nested JSON recursion failure was outside controlled exception conversion.

**Repair:** Translate decoder recursion failures into ConfigError or declared schema rejection.

**Regression verification:** 2 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Exercise deep invalid structures and preserve the specified failure interface.

## D09 — verification gate

**Status:** Repaired and regression verified in completed project

**Defect:** Truthy calibration strings or inconsistent count totals could produce false gate eligibility.

**Reproduction evidence:** project/evidence/observations/verifier_reproduction.json

**Root cause:** Gate trusted truthiness and insufficiently validated outcome schemas.

**Repair:** Require explicit Boolean success, valid rows/evidence, nonnegative integer counts and consistent totals.

**Regression verification:** 24 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Treat evidence as validated data; malformed success inputs must fail closed.

## D10 — verification comparator

**Status:** Repaired and regression verified in completed project

**Defect:** Observable crash/timeout could be hidden by missing-oracle classification.

**Reproduction evidence:** project/evidence/observations/verifier_reproduction.json

**Root cause:** Uncertainty was classified before observable execution failure.

**Repair:** Classify crash, timeout, resource and harness errors before oracle uncertainty.

**Regression verification:** 5 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Separate observed execution failure from uncertainty about semantic correctness.

## D11 — verification/integrity

**Status:** Repaired and regression verified in completed project

**Defect:** Weak manifest validation permitted malformed or unsafe evidence inputs.

**Reproduction evidence:** Immutable delivery tests/assurance/test_manifest_validation.py and verifier_security.xml

**Root cause:** Manifest schema, duplicate keys, path traversal, symlinks and resource bounds were not fully validated.

**Repair:** Reject malformed/empty/oversized manifests, unsupported hashes, unsafe/escaping/symlink paths and duplicate keys; stream file hashing.

**Regression verification:** 15 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Integrity machinery needs negative controls and safe path/data handling, not only a happy-path checksum.

## D12 — verification/source correspondence

**Status:** Repaired and regression verified in completed project

**Defect:** Historical passing evidence could outlive source changes or incomplete collection.

**Reproduction evidence:** Immutable delivery assurance/release_evidence.py; discarded campaign and evidence-binding tests

**Root cause:** Reports were not all bound to exact current source, collection, proofs and reference identities.

**Repair:** Bind fresh source snapshot, exact collected/JUnit identities and run/report hashes; validate proof/mutation/reference source identity.

**Regression verification:** 2 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Make evidence freshness and completeness explicit; a passing old report cannot certify current bytes.

## H01 — harness/install

**Status:** Repaired in prior verification; distribution replay passes in POST_UPLOAD_ZIP_CHECK.json

**Defect:** Distribution harness invoked the base interpreter instead of its venv.

**Reproduction evidence:** project/evidence/reproductions/distribution_harness_failure.txt

**Root cause:** Resolving the venv executable symlink changed interpreter context.

**Repair:** Preserve the venv path using absolute(), and assert installed import location from a clean directory.

**Regression verification:** project/evidence/reproductions/distribution_harness_failure.txt

**Reusable lesson:** Preserve environment identity and test installation without accidental local imports.

## H02 — harness/mutation

**Status:** Repaired and regression verified in completed project

**Defect:** An exploratory mutation campaign had a changed test collection.

**Reproduction evidence:** project/evidence/reproductions/discarded_campaign_disposition.json

**Root cause:** Tests/source advanced while the experiment was being prepared; detection and setup failures were not cleanly separated.

**Repair:** Quarantine that run; freeze a master copy, run a passing baseline, require exact JUnit accounting and distinguish error categories.

**Regression verification:** 7 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Freeze experiments and never count harness errors or timeouts as mutant detection.

## H03 — harness/resources

**Status:** Repaired and regression verified in completed project

**Defect:** Two Lean model runs failed to create their default thread pool under the memory cap.

**Reproduction evidence:** project/evidence/reproductions/lean_thread_limit_failure.xml

**Root cause:** Default toolchain parallelism was incompatible with the bounded process address space.

**Repair:** Set an explicit single thread for checking/model execution; retain proofs, assertions and resource policy.

**Regression verification:** 2 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Budget orchestration and toolchains together; diagnose apparatus failure without weakening the target invariant.

## H04 — harness/resources

**Status:** Repaired and regression verified in completed project

**Defect:** Profile preexec setup originally applied process limits to the orchestrator itself.

**Reproduction evidence:** Immutable delivery assurance/run.py; project/evidence/VERIFIED_RELEASE_REPORT.md

**Root cause:** preexec_fn received process_limits() instead of the callable process_limits.

**Repair:** Pass the callable, then rerun bounded profiles; code inspection and final A/B/C logs establish correction.

**Regression verification:** Immutable delivery assurance/run.py; project/evidence/VERIFIED_RELEASE_REPORT.md

**Reusable lesson:** When passing lifecycle callbacks, distinguish the function from its return value; keep the controller capable of collecting failures.

## H05 — environment/database setup

**Status:** Repaired and regression verified in completed project

**Defect:** Early disposable PostgreSQL initialization failed.

**Reproduction evidence:** Immutable delivery evidence/pg_baseline.* and pg_reproduction.*; INDEPENDENT_VERIFICATION_REPORT.md

**Root cause:** Custom socket location conflicted with image initialization expectations.

**Repair:** Mount the image-default /var/run/postgresql Unix socket, disable network, and verify readiness before fixtures run.

**Regression verification:** 1 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Use the real service lifecycle/readiness contract before interpreting integration failures.

## H06 — delivery

**Status:** Resolved delivery failure; native chat file-export capability still unavailable

**Defect:** Repeated chat download links did not deliver the files to the user.

**Reproduction evidence:** Visible user reports cannot download/not working; GitHub delivery commit 66213a8a7175d99ce14aed5e07799225dc0b4c8c and project/evidence/post_upload/POST_UPLOAD_ZIP_CHECK.json

**Root cause:** Cloud filesystem/sandbox links were presented as attachment exports without an available export tool.

**Repair:** Acknowledge limitation; obtain explicit YES for private-repository upload; push verified bytes, give real GitHub link, fetch them back and run the full gate.

**Regression verification:** Visible user reports cannot download/not working; GitHub delivery commit 66213a8a7175d99ce14aed5e07799225dc0b4c8c and project/evidence/post_upload/POST_UPLOAD_ZIP_CHECK.json

**Reusable lesson:** Verify delivery capability early and verify remotely delivered bytes. Upload authorization is separate from release approval.

## P01 — historical pre-baseline application

**Status:** Historical repair reported; current regressions executed and passing

**Defect:** Rejected inputs could collide across batches; malformed Unicode metadata could crash; standalone generators diverged.

**Reproduction evidence:** Immutable delivery docs/REMEDIATION_AUDIT_2026_10_29.md and audit/ logs

**Root cause:** These root causes/repairs are historical records, not newly reproduced during this capture: rejected identity omitted content; unpaired surrogates survived loading; generator implementations diverged.

**Repair:** Already in uploaded source: rejected-content hashing, typed Unicode checks and one canonical generator with delegating wrapper.

**Regression verification:** 14 mapped passing JUnit cases; see JSON identities.

**Reusable lesson:** Keep historical fixes and current regression evidence separate from new discovery claims.

## P02 — historical pre-baseline harness

**Status:** Historical justified harness correction; not an edit performed in the later independent audit or this capture

**Defect:** Two original-verifier setup paths used arbitrary accepted storage identities.

**Reproduction evidence:** Immutable delivery audit/TEST_SUITE_RECONCILIATION.diff and audit/upstream_test_suite.original.py

**Root cause:** Fixtures conflicted with the separately enforced validated event/tenant identity requirement.

**Repair:** Earlier documented correction set fixture event IDs to the validated identity and retained conflict assertions; uploaded baseline tests preserved thereafter.

**Regression verification:** Immutable delivery audit/TEST_SUITE_RECONCILIATION.diff and audit/upstream_test_suite.original.py

**Reusable lesson:** Correct a demonstrated fixture error transparently while retaining original evidence and requirements; do not weaken the identity guard.

## N01 — documentation

**Status:** Documented erratum in this capture; original immutable artifact intentionally unchanged

**Defect:** Architecture report retained an obsolete statement that LocalStubSink remains a D:p_20 discrepancy.

**Reproduction evidence:** project/evidence/ARCHITECTURE_COMPLIANCE.md versus project/evidence/SPECIFICATION_RECONCILIATION.md and VERIFIED_RELEASE_REPORT.md

**Root cause:** Status narrative was not fully reconciled when the owner designated the existing local synthetic functional scope.

**Repair:** Record this erratum here, cite the later explicit scoped reconciliation, and preserve immutable release bytes. No application behavior or user requirement is changed.

**Regression verification:** project/evidence/ARCHITECTURE_COMPLIANCE.md versus project/evidence/SPECIFICATION_RECONCILIATION.md and VERIFIED_RELEASE_REPORT.md

**Reusable lesson:** Reconcile current narrative status against authority decisions; preserve immutable evidence with explicit errata rather than silently rewriting a tested archive.
