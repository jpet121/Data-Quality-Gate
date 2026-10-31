# Independent assurance operator guide

Use the supplied application tree in place; no new worktree is needed. Development and Verification XML remain separate authorities. The owner designated README.md, docs/ACCEPTANCE.md and examples/matrix_v1.json as the functional specification. Frozen source copies and explicit owner decisions are under specifications/. Supplemental assembler documents are context; this package does not implement another product. Human release approval remains reserved.

On Linux with Python 3.12, create a clean venv from the release root:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-linux-cp312.hashed.lock
python -m pip check
bash scripts/install_lean.sh /tmp/sesv-toolchain
export SESV_LEAN=/tmp/sesv-toolchain/lean-4.24.0-linux/bin/lean
```

The hash lock includes the shipped application wheel and all 28 verification dependency artifacts. It targets Linux CPython 3.12. Dependency wheels and Lean binaries are not bundled; network access is needed for a fresh install. The Lean installer retains TLS verification and verifies the official archive SHA-256. The equivalent download/hash/extract/check operations were executed for this audit; the installer wrapper itself is supplied for replay. This is not an offline or byte-reproducible-build claim.

Provision a disposable PostgreSQL 17.11 container, with no network and a local Unix socket:

```bash
mkdir -p /tmp/sesv-pgsocket
chmod 777 /tmp/sesv-pgsocket
docker run -d --name sesv-audit-pg --network none \
  -v /tmp/sesv-pgsocket:/var/run/postgresql \
  -e POSTGRES_HOST_AUTH_METHOD=trust \
  postgres@sha256:31ba9c94a03ada9988f2bb493a22a75eef3a185884533e5cdbcd498ea835b08f
docker exec sesv-audit-pg pg_isready
export SESV_TEST_DSN='host=/tmp/sesv-pgsocket user=postgres dbname=postgres'
```

**The PostgreSQL fixtures destroy and recreate the public schema. Use only a disposable test database.** Trust authentication is restricted to this network-disabled test instance. The commands are not production deployment guidance. Retain configured managed-environment proxy/CA settings during network operations.

```bash
python -m assurance.run --profile A
python -m assurance.run --profile B
python -m assurance.run --profile C --authorized-local-target
python -m assurance.final_run
python -m assurance.trace
python -m assurance.gate
```

A is diagnostic and excludes PostgreSQL. B runs the full suite, synthetic calibration, 16 isolated source mutations and a 50,000-case boundary sweep. C runs a seeded 100,000-case local independent-model comparison. No external business target is contacted. Profiles enforce wall-time, CPU, address-space, file-size and file-descriptor limits. These bounds and disposable copies are not a general hostile-code sandbox. The final runner freezes source hashes, collects the exact suite, executes it with Hypothesis statistics and branch coverage, and binds collection/JUnit/source hashes. Final gate results require current source identity; changed source requires rerunning affected evidence.

The gate returns exit 2 while human approval is pending. Passing automation never grants human approval. Compiler-only, nonmandatory and inactive clauses stay inventoried with explicit scope reasons. Formal evidence comprises 14 checked model theorems plus finite implementation comparisons; it does not prove all Python execution or cryptographic collision resistance.

Additional release checks:

```bash
python -m mypy --disallow-untyped-defs --check-untyped-defs src/event_validator
python tools/build_standalone.py --check
python scripts/build_standalone.py --check
python -m assurance.formal
python -m assurance.idempotency
python -m assurance.calibration
python -m bandit -r src assurance -f json -o continuation_evidence/security.json
python -m build
python verification/distribution_check.py /path/to/fresh-venv/bin/python
python verify_release.py
```

Bandit findings and its nonzero scan result are retained for manual disposition. Dependency advisory results reflect the queried PyPI metadata at execution time, not a universal security guarantee. Distribution validation uses a separate fresh venv. Full copyrighted books/toolchains are not redistributed; hashes and relevant citations identify the supplied references. Historical runs remain available, clearly distinct from final evidence. Regenerate the integrity manifest after any shipped-file change. Final exact-ZIP replay results are external to the ZIP, preserving the tested artifact bytes.
