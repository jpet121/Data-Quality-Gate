# GitHub portfolio package — scope and provenance

This is a **curated, recruiter-readable subset** of the independently verified
**Structured Event Schema Validator v1.0.2** release. It is not the original
verified ZIP and should not be represented as a fresh full-package verification.

## What this GitHub package contains

- Original Python application code (`main.py`, `src/event_validator/`),
  SQLite/PostgreSQL DDL, example events and matrix, and exact prebuilt wheel/sdist.
- Original automated tests (`test_suite.py`, `tests/`) and their verification utilities.
- Original acceptance criteria, architecture material, selected authority contracts,
  and release operator instructions.
- Final independent verification report, requirement-traceability CSV, release status,
  exact-original-ZIP replay receipt, and selected testing evidence for inspection.
- A **new manifest for this curated GitHub subset**, regenerated from the files actually
  present here. It intentionally replaces the 492-file original release manifest;
  it is not the original release's manifest.

## Verified results — evidence scope

The original, complete candidate ZIP was reported to have passed **410/410 tests**
with no failures, errors, or skips. The release report also records the stated
fuzzing, mutation, PostgreSQL, Lean, coverage, and package checks. See
[`VERIFIED_RELEASE_REPORT.md`](../VERIFIED_RELEASE_REPORT.md),
[`RELEASE_STATUS.json`](../RELEASE_STATUS.json), and the
[external exact-artifact replay receipt](../release_evidence/FINAL_ZIP_REPLAY.json).
The report states **technical verification for a local synthetic demonstration**,
not approval of production financial deployments. **Final human release approval
remains pending.**

These results were measured on the **complete source candidate**, not this
trimmed publication. Publishing a subset removes some historical replay logs,
original-specification copies and full frozen requirement-evidence bindings.
A full high-assurance re-execution needs the *original complete release archive*
and its exact original manifest. Do **not** interpret the selected historical
reports as a new 410-test run on this curated ZIP.

The original uploaded release archive SHA-256 is:

`bf5984b925bc55378c0c0037e575953e37abf7ac571dfb7cd41f6a9f5deaabd6`

The original nested candidate ZIP SHA-256 is:

`f06ab83d0c56872460b30a402ce48662a06bb7cfdd3d73c10aebcc4919c02243`

## Runnable sample

On a workstation with **Python 3.12+**, run from the repository root:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python main.py --matrix examples/matrix_v1.json --input examples/replay.jsonl
```

The recorded full verification campaign additionally required an isolated
PostgreSQL database and Lean 4. Do not use disposable-test PostgreSQL commands
against any real database; some fixture operations destroy and recreate the
`public` schema. `ASSURANCE_OPERATOR_GUIDE.md` describes the original full run,
not an assurance guarantee for this reduced repo.

For a scoped Python test demonstration, run:

```bash
python -m pytest -q test_suite.py tests/unit tests/property tests/regression tests/differential
```

This is **not** equivalent to the original full 410-test verification. Individual
proof/assurance scripts can need additional original release assets, toolchains,
permissions, or environment variables that were not retained here.

## Why the rest of the original package was not selected

The source archive holds hundreds of historical intermediate test logs,
redundant JUnit XML files, multiple large requirements matrices and old
specification/revision copies. They are valuable for forensic auditing but
not useful as the top-level recruiter-facing project contents. The original
complete ZIP should be retained separately for audit preservation.

The existing GitHub root `README.md` is **not included** in this ZIP. Preserve
it during upload. Its old links to files/branches in a different repository
may require updating to these local repository paths.
