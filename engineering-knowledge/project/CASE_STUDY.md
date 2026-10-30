# Structured Event Schema Validator v1.0.2: evidence-based engineering retrospective

This case study reconstructs the available history from the visible conversation, explicit owner-decision records, authoritative files, preserved code/tests/logs, delivery commits and immutable artifacts. It does not recreate an unavailable raw conversation export or pre-upload development history. The JSON source inventory records what was copied and what remains unavailable. **This capture installs guidance; it does not rebuild or change the completed application.**

## Authority and original objectives

The user requested independent high-assurance verification and remediation of the supplied application ZIP. The ZIP was the source baseline, SHA-256 `30bc9d50aec1d39e6eecdd2f0913566fc1149f310ed79d77b5d6d9b14500e772`; the uploaded verification report was historical evidence. The GitHub main branch initially contained only a README and was unsuitable as the implementation source.

Mandatory project gates included a clean actual Python 3.12 environment with all declared tests including Hypothesis, deterministic/property/stateful/differential/integration/regression execution, isolated real PostgreSQL checks, standalone main.py, package/wheel/CLI verification, applicable boundaries/fault injection/mutation/security analysis, requirements comparison, iterative repairs, evidence and final integrity-protected release artifacts. No test weakening, fabricated execution, skipped required gates or self-granted human release approval was authorized.

Two XML contracts were assigned distinct roles: Development governs implementation constraints and architecture; Verification governs testing, methodology and evidence. Later supplemental assembler/compiler packages were context, not an instruction to build a different product. Five architecture references and six verification references inform methods; book examples do not silently redefine event behavior.

The decisive owner correction was: “Use the application’s README.md, docs/ACCEPTANCE.md and examples/matrix_v1.json as the authoritative functional requirements, alongside the two XML contracts.” Versioned copies and hashes preserve this designation. Earlier missing-functional-source blockers were superseded by that decision, not hidden by deriving requirements from production code.

## Project-specific requirements, interfaces and scope

This is a synthetic local five-event validator: ORDER_CREATED, PAYMENT_AUTHORIZED, INVENTORY_RESERVED, SHIPMENT_DISPATCHED and ORDER_CANCELLED. It loads a data-only matrix, tokenizes a strict key/value grammar, normalizes declared aliases, selects an unambiguous explicit-priority schema, validates strict immutable records, isolates per-event rejection, preserves original-input hashes and avoids raw-value diagnostic leaks. Default project limits are 4096 UTF-8 bytes per event, 32 tokens and 10000 events per batch; configured reductions must be enforced without silent truncation.

The Python API includes load_matrix, validate, validate_many, repositories and dispatch_once; standalone main.py and an installed console entry point are separately required interfaces. SQLite and optional PostgreSQL persist complete results, errors, audit/outbox rows atomically. Accepted delivery identity includes tenant, event identity and configuration fingerprint; identical content deduplicates and conflicting content rolls back. Rejected results produce non-executable quarantine. Dispatch is disabled by default; an explicitly supplied LocalStubSink fully implements local recording, retry and dead-letter demonstration behavior. No production ERP/payment/carrier connector was specified.

The owner delegated reconciliation of undocumented money/timestamp limits: “You decide the best path.” The engineering choice retained the original boundary expectations and documented positive money through 9999999999999.99 with at most two fractional digits; uppercase T/Z, at most six fractional-second digits, offsets within ±14:00, valid calendar seconds and no leap seconds. This is an authorized project decision, not a global recommendation. Integer nested JSON money is valid and exact; bool, exponent and excess-scale forms are rejected.

The owner separately accepted a finite mutation criterion: applicable listed classes covered, a passing baseline, all 16 selected valid mutants detected, no unexplained survivors, setup errors or timeouts. This was acceptance of a particular verification policy, not human release approval. Later explicit “YES!” authorized uploading the delivery ZIP to the private GitHub repository. Screenshot context and upload permission were never treated as production release approval.

Live business connectors, expired-lease/crash reclamation, governed production schemas, organization-specific authentication/access controls, production-data migration rollback and production-volume SLOs remain outside this local baseline. A future project must specify its own requirements rather than inherit these omissions or demo constants.

## Architecture and change rationale

The application separates domain models, matrix loading, lexer/parser, validation orchestration, SQLite/PostgreSQL adapters, workflow dispatch and CLI. Generated standalone source preserves responsibility boundaries while meeting the one-file deployment interface. The canonical generator is checked through both documented entry points.

Architecture remediation added complete callable annotations and structural repository/sink protocols, moved ConfigSnapshot from I/O loading into the domain layer while retaining public re-exports, and tested deep immutability instead of equating annotations with runtime enforcement. These changes apply the references' inward-dependency and composition principles without inventing speculative factories or forcing an unrelated runtime framework.

Verifier modules are separate from production. The new functional oracle imports neither production modules nor Pydantic; regex lexing and standard-library/rational validation provide a simpler algorithmic path. Lean models address release eligibility and abstract store behavior. SQLite/PostgreSQL exercise different storage engines, while standalone/wheel parity deliberately shares generated application source. These are different kinds of evidence and must not be conflated.

## Defects, repairs and regression coverage

The complete six-part chains are in DEFECT_LEDGER.md/JSON. Twenty-one records distinguish application, architecture, verifier, environment/harness, delivery, historical and documentary findings.

Newly reproduced application defects included psycopg JSONB dict dispatch treated as serialized JSON, concurrent registration of a second unique fingerprint constraint, nested JSON money bypassing the lexical contract, rejection of valid integer money, Decimal-context-sensitive exact totals, allocation before config size checks and uncontrolled JSON recursion failures. Repairs targeted the representation boundary, complete constraint behavior, shared lexical conversion, exact arithmetic, bounded reads and typed failure conversion. Positive and negative neighboring cases protect valid inputs as well as rejection rules.

Verifier defects included truthiness/inconsistent count acceptance, crashes hidden behind missing-oracle classification, unsafe or malformed manifests and stale evidence not bound to current source/test identity. Negative controls, strict schemas and exact collection/source/report identities provide failure-detection evidence. Tests of the verifier are not self-issued approval.

Original tests in the uploaded baseline remained byte-identical during the subsequent audit: 13 files including test_suite.py. Tests were additive. Earlier pre-upload history includes two justified fixture corrections to align accepted storage identities with validated event IDs; the untouched upstream verifier and exact reconciliation diff remain in the original delivery. Those are historical repairs, not new changes made during this capture.

## Failed approaches and apparatus corrections

- Early PostgreSQL setup used a custom socket path incompatible with image initialization. The final disposable service used the image-default Unix socket, network disabled and explicit readiness. Setup failures were not counted as application defects.
- A distribution harness resolved a venv interpreter symlink to the base interpreter. Preserving the venv executable path and checking site-packages import location exposed and corrected the context error.
- A mutation experiment ran while collection was advancing. Its evidence was quarantined. A frozen master copy, passing control and exact JUnit accounting replaced ambiguous detection. Invalid/setup-error/time-out outcomes never count as kills.
- The final memory cap exposed default Lean thread-pool allocation failure: 408 passed and two model runs failed. Explicit single-thread invocations retained proofs, assertions and resource policy; the complete gate then passed. Limits were also corrected to execute in subprocess children rather than the controller itself.
- Repeated workspace/sandbox links failed to deliver the files in the user's local ChatGPT interface. The session had no supported file-export tool. After explicit authorization, GitHub delivery resolved the actual transfer problem; bytes were fetched back and checked rather than merely assuming upload success.
- Repeated requests for an unspecified application XML became unnecessary after the owner explicitly designated functional authority. The reusable improvement is to establish source roles early, not to dispense with consequential clarification or fabricate missing requirements.

A further apparatus limit occurred during this knowledge task: native fresh Codex skills/list discovery passed, but an inference-driven fresh session was denied by the proxy with HTTP CONNECT 403 before model execution. The probe was stopped; no authentication or network policy workaround was used. This is a documented limitation of instruction-application verification, not evidence that the installed skill failed parsing.

## Successful verification and exact completion evidence

Earlier historical reports recorded incomplete gates, a 173-test baseline, then 194- and 211-test phases. These are separate source/execution states and must not be added together or used to certify later changes. Current final evidence is 410 passed, zero failures/errors/skips, including actual Hypothesis properties/state machines and real PostgreSQL.

The accepted 16-mutant experiment used a passing 393-test non-PostgreSQL baseline, all 16 generated/executed/killed, zero survivors/invalid/timeouts/harness errors, explicit denominator 16 and all 13 applicable listed classes. PostgreSQL was mandatory in the full suite and excluded only from disposable mutation runs to avoid shared destructive fixtures.

The independent-model campaign compared 100000 actual cases: 25000 valid agreements, 75000 permitted-rejection agreements, 1031 replays and no anomalies. A separate 50000-case seeded boundary sweep passed. These finite counts are case facts, not future global gates. Calibration detected 14 synthetic known conditions with 0 false positives in 20 negative controls, not an operational error-rate estimate.

Official Lean 4.24.0 checked nine release-gate and five store-model theorems; built-in propext is disclosed. The implementation correspondence is finite: 1984 gate combinations and 51 SQLite traces/2005 operations, zero disagreements. No proof of all Python behavior, cryptographic collision resistance or formal Python equivalence is claimed.

Application coverage measured 525/540 statements and 192/212 branches; no coverage acceptance threshold was invented. Bandit returned 26 retained findings (21 low, five medium), each reviewed with a scoped disposition, no confirmed unresolved issue in the exercised scope. Dependency checks queried all 28 pins through verified HTTPS with no unavailable queries or listed PyPI advisories at that time. These checks do not certify a complete security posture.

The complete trace inventory contains 773 rows: 51 mandatory Development, 167 functional and 504 technical Verification rows pass in the documented scoped assessment; three human-governance rows remain blocked and 48 compiler/nonmandatory/inactive exclusions are explicit. Many XML clauses are manual reviews linked to evidence; they are not 773 independent executed tests or formal proofs.

The tested application ZIP SHA-256 is `f06ab83d0c56872460b30a402ce48662a06bb7cfdd3d73c10aebcc4919c02243`. The complete delivery bundle SHA-256 is `bf5984b925bc55378c0c0037e575953e37abf7ac571dfb7cd41f6a9f5deaabd6`. Exact inventory and all 492 application manifest entries were verified. The GitHub ZIP introduced by commit 66213a8a7175d99ce14aed5e07799225dc0b4c8c was fetched back, freshly extracted and passed all 410 tests plus standalone/distribution checks; the recorded results were uploaded in commit 7858d5456154d865b5744036388bfe66d383dd84. The immutable original delivery and post-upload observations are retained here.

## Residual erratum and completion states

ARCHITECTURE_COMPLIANCE.md still contains the older sentence that LocalStubSink remains a D:p_20 discrepancy, whereas the later explicit scope reconciliation and final report explain the completed local recording behavior. The contradiction is a documentation-status erratum, recorded as N01. This capture does not rewrite a tested archive or present that older sentence as the current functional decision. A future release-document update should reconcile stale status text under a new artifact identity if requested.

Implementation, applicable tests, required runtime/integrations, artifact/installation and scoped independent methods have their documented technical evidence. Final human release approval remains absent, so release approval remains pending/NOT APPROVED. No new application repair or broad application rerun was needed for knowledge capture: protected source hashes and delivery ZIP identities are rechecked instead. Ten isolated installer safety tests and real native fresh-process skill discovery test the new installation work.

## Proposed improvements and scope of reuse

Generalize verified mechanisms: preserve authority and user corrections; reproduce before fixing; keep evidence failure-visible; apply contracts across nested representations; calculate exact invariants independently of mutable context; test real adapter return types/constraints; enforce bounds before allocation; bind evidence to current artifacts; use proportionate independent checks; preserve immutable delivery with sidecar replay; verify actual file transfer.

Recommendations, not new application requirements: freeze source/collection before costly campaigns, maintain one current status/errata index, establish a usable delivery route earlier and verify cold-session discovery when its environment permits. The improvement provenance table links each installed rule to evidence and its validation. Global guidance stays short; the skill carries workflow detail; this case study contains project-specific facts. No unrelated future build inherits Python 3.12, Pydantic v2, PostgreSQL, these money/time rules, main.py or these test quotas.
