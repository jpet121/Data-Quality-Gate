# Evidence, artifact identity and completion

Keep these independent states in the report; do not collapse them into a single green badge:

| State | Required support |
|---|---|
| Implementation complete | All required paths implemented; no missing required behavior disguised by a placeholder. |
| Applicable tests passing | Real execution of relevant and contract-required checks, with failures/errors/skips/unrun distinct. |
| Original requirements verified | Requirement-level expected outcomes and cited evidence; unresolved authority/conflicts remain visible. |
| Runtime/integration verified | Actual required environment/services, persistence/failure/side-effect behavior. |
| Artifact/install verified | Exact delivered bytes, valid distribution, installation/entry point and integrity evidence where required. |
| Required independent verification complete | Specified references/models/proofs checked; limits and common dependencies disclosed. |
| Release approved | The applicable approval authority actually granted the required approval. Automation or upload permission cannot supply reserved human approval. |
| Release blocked | Exact unmet criterion, evidence, consequence and smallest next action. Other completed states remain visible. |

Before recommending release, check specified functionality, authorized corrections, no unresolved confirmed in-scope defects, relevant regression tests, required integration/runtime behavior, deliverable format, accurate installation instructions, disclosed risks/skips, and required approvals. Do not invent a human approval gate when the contract does not require one, or grant it when it does.

For consequential runs preserve: source/spec/config/dependency identity; command and working directory; tool/runtime versions; start/end time and time zone; seed/replay identifier; collected and executed test identities where completeness matters; outcomes including zero tests, failures, errors, skips and unrun checks; relevant state/side effects; artifact hashes; limitations. A test's existence or old passing report is not evidence that its current version ran.

Keep the artifact immutable after its final hash. Store subsequent exact-artifact replay logs as external sidecars or in an outer evidence bundle; identify the inner tested archive precisely. Hash every shipped member except a self-referential manifest, verify exact member inventory, reject unsafe paths/symlinks where applicable, and verify source/distribution correspondence. Record which evidence must be refreshed when code, tests, requirements, dependencies or configuration change.

For installation, use a fresh environment when risk warrants. Keep the venv executable path intact; resolving a symlink can invoke a different interpreter. Run from a clean directory without accidental local imports. A successful wheel install does not demonstrate offline availability or byte-reproducible builds. Advisory scans are point-in-time and database-scoped.

Before promising a download, verify that this interface can export files. Filesystem paths and generated `sandbox:` links are not proof of downloadable attachments. If unavailable, report that limitation and use an authorized transfer route. Fetch remote bytes back and compare their hashes when feasible. Download/branch-upload permission is distinct from deployment or final release approval.
