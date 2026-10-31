#!/usr/bin/env bash
# Install the exact checker used by the gate-model proof, preserving TLS and SHA-256 verification.
set -euo pipefail
lean_destination=${1:?Usage: bash scripts/install_lean.sh /absolute/toolchain-directory}
mkdir -p "$lean_destination"
lean_archive="$lean_destination/lean-4.24.0-linux.tar.zst"
curl --fail --location --max-time 180 \
  https://github.com/leanprover/lean4/releases/download/v4.24.0/lean-4.24.0-linux.tar.zst \
  -o "$lean_archive"
python3 - "$lean_archive" <<'PY'
import hashlib,sys
from pathlib import Path
path=Path(sys.argv[1]); digest=hashlib.sha256()
with path.open('rb') as stream:
    for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
expected='b14f5e5159219dd1a1956c3b806813319f5e94ccd5bdfd56f54520609a5bb5ec'
if digest.hexdigest()!=expected:raise SystemExit('Lean archive integrity verification failed')
print('Lean archive SHA-256 verified')
PY
tar --zstd -xf "$lean_archive" -C "$lean_destination"
"$lean_destination/lean-4.24.0-linux/bin/lean" --version
