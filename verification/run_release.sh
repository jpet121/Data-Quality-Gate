#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${SESV_TEST_DSN:?Set this to a disposable PostgreSQL database; tests DROP public schema}"
python -m pip install -e '.[test,postgres]' build bandit
python tools/build_standalone.py --check
python scripts/build_standalone.py --check
python -m pytest -q test_suite.py tests --junitxml=evidence/reproduced_release.xml
python verification/seeded_boundary_sweep.py --cases 50000 --seed 20261029
python verification/mutation_check.py
python -m build --wheel
python -m venv /tmp/sesv-wheel-check
/tmp/sesv-wheel-check/bin/python -m pip install dist/*.whl
python verification/distribution_check.py /tmp/sesv-wheel-check/bin/python
# Bandit reports the documented fixed-table-name B608 finding; inspect rather than suppress.
python -m bandit -r src -f json -o evidence/reproduced_bandit.json
