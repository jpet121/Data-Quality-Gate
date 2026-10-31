import json
from pathlib import Path
import pytest
from event_validator import load_matrix
ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture(scope='session')
def cfg():return load_matrix(ROOT/'examples/matrix_v1.json')
@pytest.fixture(scope='session')
def valid():return [json.loads(l)['raw'] for l in (ROOT/'examples/valid.jsonl').read_text().splitlines()]
@pytest.fixture(scope='session')
def invalid():return [json.loads(l)['raw'] for l in (ROOT/'examples/invalid.jsonl').read_text().splitlines()]
