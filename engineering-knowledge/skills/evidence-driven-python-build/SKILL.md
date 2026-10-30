---
name: evidence-driven-python-build
description: Implement, repair, verify, and retrospectively improve software from authoritative requirements using reproducible defects, risk-based tests, and exact-artifact evidence. Use for substantial Python builds, remediation, specification audits, release verification, or engineering knowledge capture; adapt principles to other languages and keep routine changes proportionate.
---

# Evidence-driven software engineering

Use this workflow when the task warrants specification-driven implementation or assurance. Read the project instructions and authoritative inputs first. Current user instructions and applicable higher-priority guidance take precedence. This skill does not authorize external publication, message delivery, destructive actions, or changes outside the user's scope.

For a small change, use only the relevant steps and required checks. Do not impose a particular Python version, framework, database, executable layout, test count, fuzzing budget or manual approval gate on unrelated projects. Follow each project's contract.

## Workflow

1. **Intake:** inventory the actual source baseline, authoritative specifications, user corrections, existing tests and historical reports. Separate requirements from evidence and contextual documents. Ask only about consequential ambiguity that cannot be resolved from available sources; continue independent work.
2. **Traceability:** record requirement IDs/source locations, expected outcomes, relevant errors/state/side effects, verification method and unresolved assumptions. Freeze expected behavior before interpreting newly generated results. New authority decisions must be explicit.
3. **Architecture:** select the smallest sufficient design, with policies separated from I/O and justified interfaces. Preserve public interfaces, immutability or compatibility where required. Avoid speculative abstraction.
4. **Baseline:** inspect runtime/dependency/service prerequisites; execute relevant existing checks and record actual exit codes, outcomes and environment. Preserve original tests and distinguish setup, harness and application failures.
5. **Implement or reproduce:** build complete executable behavior, or capture a minimal failing example with a reliable expected outcome before remediation. Inspect serialization, failure propagation and adjacent boundaries where risk warrants.
6. **Repair:** fix the root cause here when authorized and supported. Preserve working behavior; add a meaningful regression test for a reproducible defect. A harness correction must preserve the requirement and original assertions, with its reason documented.
7. **Verify:** run the affected checks, then expand according to risk and mandatory project gates. Select methods from [verification selection](references/verification-selection.md). Repeat Detect → Reproduce → Diagnose → Repair → Test → Reassess until applicable criteria pass or a precise blocker remains.
8. **Independent checks:** when warranted, use a simpler separately constructed reference, different storage/runtime path, calibrated fault injection or checked model. Record shared dependencies and oracle uncertainty. Parity of generated artifacts is a distribution check, not independent semantic proof.
9. **Deliver:** build the required outputs, verify installation/execution and source/artifact correspondence, hash immutable artifacts, and test a fresh extraction when relevant. Record test evidence outside an immutable archive rather than repeatedly rewriting it. If delivery requires an external destination, use only an authorized route and verify the remotely stored bytes when feasible.
10. **Close and learn:** report distinct implementation/test/requirements/integration/artifact/independence/approval states, precise blockers and bounded conclusions. Perform knowledge capture when requested or when a reusable lesson is supported; update owned guidance without duplicating or overriding unrelated instructions.

Use the [detailed workflow](references/workflow.md) for larger tasks, [evidence and release criteria](references/evidence-and-release.md) for completion, and [retrospective method](references/retrospective.md) for knowledge capture. Record requirements in [the CSV template](templates/requirements.csv), defects in [the defect template](templates/defect.md), and completion in [the state template](templates/completion.json); adapt templates instead of treating their fields as new product requirements.

## Claim discipline

Never count an unavailable oracle, harness setup error, unauthorized skipped test, invalid mutant or timeout as successful verification. Capture actual collected/executed identities and counts when completeness matters. Recheck evidence affected by source, dependency, configuration or artifact changes. Use finite evidence to support finite conclusions; do not infer universal zero defects, full security certification, mathematical equivalence or human release approval.

If blocked, finish useful independent work, explain the specific failed prerequisite and its effect, and identify the smallest required action. Do not transfer a repair elsewhere merely because this environment needs ordinary setup work.

## Explicit invocation

Use $evidence-driven-python-build to implement and verify this project against its attached authoritative specification. Repair confirmed defects here, run risk-appropriate tests, preserve regression coverage, and verify the exact required release artifacts.
