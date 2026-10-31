"""Collect and execute the complete required suite against a frozen source identity."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from .run import process_limits

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'continuation_evidence'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot() -> dict[str, str]:
    paths = []
    for directory in ['src', 'tests', 'assurance', 'verification', 'tools', 'scripts',
                      'formal', 'specifications', 'examples', 'migrations', 'benchmarks']:
        paths.extend(p for p in (ROOT / directory).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts
                     and p.suffix in {'.py', '.lean', '.json', '.xml', '.md', '.sql', '.sh', '.jsonl'})
    paths.extend(ROOT / name for name in ['main.py', 'test_suite.py', 'verify_release.py',
                 'pyproject.toml', 'requirements-verification.lock',
                 'requirements-linux-cp312.hashed.lock', 'README.md',
                 'docs/ACCEPTANCE.md', 'SPECIFICATION_RECONCILIATION.md',
                 'ASSURANCE_OPERATOR_GUIDE.md'])
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))}


def main() -> int:
    EVIDENCE.mkdir(exist_ok=True)
    before = snapshot()
    source_file = EVIDENCE / 'final_source_snapshot.json'
    source_file.write_text(json.dumps(before, indent=2) + '\n')
    collect = [sys.executable, '-m', 'pytest', '--collect-only', '-q', 'test_suite.py', 'tests']
    result = subprocess.run(collect, cwd=ROOT, capture_output=True, text=True, timeout=60)
    (EVIDENCE / 'final_collection.txt').write_text(result.stdout + result.stderr)
    if result.returncode:
        return result.returncode
    nodes = [line.strip() for line in result.stdout.splitlines()
             if line.startswith(('test_suite.py::', 'tests/')) and '::' in line]
    identities = []
    for node in nodes:
        base, separator, parameters = node.partition('[')
        components = base.split('::')
        classname = components[0].removesuffix('.py').replace('/', '.')
        if len(components) > 2:
            classname += '.' + '.'.join(components[1:-1])
        identities.append([classname, components[-1] + (separator + parameters if separator else '')])
    if not identities:
        raise RuntimeError('No required tests collected')
    inventory = EVIDENCE / 'final_collection.json'
    inventory.write_text(json.dumps({'collection_command': collect, 'nodeids': nodes,
                                    'junit_identities': identities}, indent=2) + '\n')
    command = [sys.executable, '-m', 'coverage', 'run', '--branch',
               '--source=src/event_validator,assurance', '-m', 'pytest', '-q',
               'test_suite.py', 'tests', '--hypothesis-seed=20261029',
               '--hypothesis-show-statistics', '--junitxml=continuation_evidence/final_suite.xml']
    started = datetime.now(timezone.utc).isoformat()
    tick = time.monotonic()
    with (EVIDENCE / 'final_suite.txt').open('w') as output:
        result = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                timeout=180, preexec_fn=process_limits)
    unchanged = before == snapshot()
    junit = EVIDENCE / 'final_suite.xml'
    record = {'command': command, 'started_at': started,
              'completed_at': datetime.now(timezone.utc).isoformat(),
              'wall_seconds': time.monotonic() - tick,
              'exit_code': result.returncode if unchanged else 1,
              'source_unchanged': unchanged, 'collected': len(nodes),
              'source_snapshot_sha256': sha(source_file),
              'collection_sha256': sha(inventory),
              'junit_sha256': sha(junit) if junit.is_file() else None}
    (EVIDENCE / 'final_test_run.json').write_text(json.dumps(record, indent=2) + '\n')
    subprocess.run([sys.executable, '-m', 'coverage', 'json',
                    '-o', 'continuation_evidence/final_coverage.json'], cwd=ROOT, check=True)
    print(json.dumps(record, indent=2))
    return record['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
