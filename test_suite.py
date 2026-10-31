"""Independent, specification-oriented verification for Structured Event Schema Validator.

Run from the application directory:
    python -m pytest -q test_suite.py
    python -m pytest -q test_suite.py -k 'not release_'

The second command is a diagnostic (non-release) profile ONLY: tests prefixed
``test_release_`` deliberately assert contract guarantees and MUST pass before
release. No application bug is marked xfail or concealed by a skip.

For full Hypothesis coverage: python -m pip install -e '.[test]'
Hypothesis tests are explicitly skipped if the optional dependency is missing;
the release gate below reports a failed dependency check instead.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import sqlite3
import subprocess
import sys
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parent
if not (ROOT / 'src' / 'event_validator').is_dir():
    raise RuntimeError('Place test_suite.py beside the application src/ and examples/ directories')
sys.path.insert(0, str(ROOT / 'src'))

from event_validator import Failure, load_matrix, validate, validate_many
from event_validator.matrix import ConfigError
from event_validator.models import MODEL_REGISTRY, OrderCreated
from event_validator.parser import ParseFault, tokenize
from event_validator.storage import IdempotencyConflict, SQLiteRepository
from event_validator.workflow import LocalStubSink, dispatch_once

try:
    from hypothesis import given, settings, strategies as st
    from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
except ImportError:
    HAS_HYPOTHESIS = False
else:
    HAS_HYPOTHESIS = True


@pytest.fixture(scope='session')
def cfg():
    return load_matrix(ROOT / 'examples' / 'matrix_v1.json')


@pytest.fixture(scope='session')
def valid_cases():
    return tuple(json.loads(s) for s in (ROOT / 'examples' / 'valid.jsonl').read_text(encoding='utf-8').splitlines())


@pytest.fixture(scope='session')
def invalid_cases():
    return tuple(json.loads(s) for s in (ROOT / 'examples' / 'invalid.jsonl').read_text(encoding='utf-8').splitlines())


@pytest.fixture()
def repo(tmp_path):
    instance = SQLiteRepository(tmp_path / 'verify.sqlite')
    instance.migrate()
    try:
        yield instance
    finally:
        instance.close()


def raw_field_replace(raw: str, name: str, value: str) -> str:
    """Change one lexer-level field without modifying unrelated data."""
    segments = raw.split(' | ')
    aliases = {'event_type': 'event', 'tenant_id': 'tenant', 'order_id': 'order'}
    keys = (name, aliases.get(name, name))
    matching = [i for i, s in enumerate(segments) if s.split('=', 1)[0] in keys]
    assert len(matching) == 1, (name, matching)
    i = matching[0]
    key = segments[i].split('=', 1)[0]
    segments[i] = f'{key}={value}'
    return ' | '.join(segments)


def reference_lexer_restricted(text: str) -> dict[str, str]:
    """Independent simple oracle VALID ONLY for unquoted ASCII key=value tokens."""
    result: dict[str, str] = {}
    for part in text.split(' | '):
        key, sep, value = part.partition('=')
        if not sep or not key or not value or key in result:
            raise ValueError('outside oracle domain')
        if not (key[0].isascii() and key[0].isalpha()):
            raise ValueError('outside oracle domain')
        if not key.replace('_', '').isascii() or not key.replace('_', '').isalnum():
            raise ValueError('outside oracle domain')
        if not value.isascii() or not value.isalnum():
            raise ValueError('outside oracle domain')
        result[key] = value
    return result


# -------------------- Deterministic contractual checks --------------------

def test_matrix_fingerprint_and_registry_binding(cfg):
    assert len(cfg.fingerprint) == 64
    assert cfg.fingerprint == load_matrix(ROOT / 'examples' / 'matrix_v1.json').fingerprint
    assert len(cfg.specs) == 5
    for spec in cfg.specs:
        assert spec['registry_key'] in MODEL_REGISTRY
        assert set(spec['required']).isdisjoint(spec['optional'])
        assert set(spec['field_types']) == set(MODEL_REGISTRY[spec['registry_key']].model_fields)
        assert spec['event_type'] == spec['matcher']['equals']


@pytest.mark.parametrize('position', range(5))
def test_each_example_valid_and_strictly_typed(cfg, valid_cases, position):
    raw = valid_cases[position]['raw']
    result = validate(raw, 'case', cfg, position)
    assert result.status == 'ACCEPTED', result.canonical()
    assert result.failure_category is None and result.errors == ()
    assert result.record is not None
    assert type(result.record) is MODEL_REGISTRY[cfg.specs[position]['registry_key']]
    assert result.record.event_type == result.event_type
    assert result.index == position and result.config_fingerprint == cfg.fingerprint
    assert result.input_sha256 == hashlib.sha256(raw.encode('utf-8')).hexdigest()
    assert result.record.occurred_at.utcoffset() is not None


@pytest.mark.parametrize('position,category', [
    (0, Failure.SCHEMA_VIOLATION), (1, Failure.PARSE_ERROR),
    (2, Failure.SCHEMA_VIOLATION), (3, Failure.SCHEMA_VIOLATION),
    (4, Failure.SCHEMA_VIOLATION), (5, Failure.SCHEMA_VIOLATION),
    (6, Failure.UNSUPPORTED_EVENT), (7, Failure.PARSE_ERROR),
    (8, Failure.PARSE_ERROR),
])
def test_each_golden_invalid_rejects(cfg, invalid_cases, position, category):
    result = validate(invalid_cases[position]['raw'], 'case', cfg, position)
    assert result.status == 'REJECTED'
    assert result.record is None and result.failure_category == category
    assert len(result.errors) >= 1
    assert all(err.code and err.rule_id for err in result.errors)


def test_batch_isolation_and_exact_output_count(cfg, valid_cases, invalid_cases):
    payload = [valid_cases[0]['raw'], invalid_cases[0]['raw'], valid_cases[1]['raw']]
    results = list(validate_many(payload, 'BATCH', cfg))
    assert len(results) == len(payload)
    assert [r.status for r in results] == ['ACCEPTED', 'REJECTED', 'ACCEPTED']
    assert [r.input_ref for r in results] == ['BATCH/00000000', 'BATCH/00000001', 'BATCH/00000002']
    assert [r.index for r in results] == [0, 1, 2]


def test_repeatability_and_permutation_metamorphic(cfg, valid_cases):
    for case in valid_cases:
        raw = case['raw']
        one = validate(raw, 'fixed', cfg)
        two = validate(raw, 'fixed', cfg)
        assert one.canonical() == two.canonical()
        permuted = ' | '.join(reversed(raw.split(' | ')))
        variant = validate(permuted, 'fixed', cfg)
        assert variant.status == one.status == 'ACCEPTED'
        assert variant.record == one.record


def test_no_guessing_missing_values(cfg, valid_cases):
    raw = valid_cases[1]['raw']
    candidate = ' | '.join(s for s in raw.split(' | ') if not s.startswith('payment_ref='))
    result = validate(candidate, 'missing', cfg)
    assert result.status == 'REJECTED' and result.failure_category == Failure.SCHEMA_VIOLATION
    assert result.record is None
    assert any(e.code == 'missing_field' for e in result.errors)


def test_alias_collision_and_exact_duplicate_reject(cfg, valid_cases):
    raw = valid_cases[1]['raw']
    assert validate(raw + ' | tenant_id=TEN-B', 'bad', cfg).failure_category == Failure.PARSE_ERROR
    assert validate(raw + ' | currency=USD', 'bad', cfg).failure_category == Failure.PARSE_ERROR


def test_no_secret_leak_in_errors_or_trace(cfg, invalid_cases):
    for case in invalid_cases:
        raw = case['raw'] + ' | payment_ref=VERY-PRIVATE-76543'
        result = validate(raw, 'secret', cfg)
        text = json.dumps([e.model_dump() for e in result.errors] + list(result.trace))
        assert 'VERY-PRIVATE-76543' not in text
        assert 'CUST-FAKE-11' not in text


@pytest.mark.parametrize('text', [
    '', 'a=x |', 'a=x | a=y', 'a=x extra', 'a=\\x', 'a="unterminated',
    'a=x | =y', 'a=', 'a=x | b="y"garbage',
])
def test_malformed_lexer_rejected_with_typed_fault(text):
    with pytest.raises(ParseFault):
        tokenize(text, 32)


def test_quoted_lexing_literal_delimiters():
    assert tokenize('a="x|y" | b="say \\"hi\\""', 10) == [('a', 'x|y'), ('b', 'say "hi"')]


def test_independent_restricted_lexer_differential():
    items = ('a=ALPHA', 'b=BRAVO', 'c=CHARLIE', 'z=ZULU')
    for size in range(1, 5):
        for arrangement in itertools.permutations(items, size):
            sample = ' | '.join(arrangement)
            assert dict(tokenize(sample, 32)) == reference_lexer_restricted(sample)


def test_oracle_must_detect_mutated_output():
    sample = 'a=ALPHA | b=BRAVO'
    expected = reference_lexer_restricted(sample)
    mutated = dict(tokenize(sample, 32))
    mutated['a'] = 'CORRUPTED'
    assert mutated != expected


def test_strict_pydantic_rejects_string_decimal_and_naive_datetime():
    record = dict(event_type='ORDER_CREATED', event_id='E1', tenant_id='T1', order_id='O1',
                  occurred_at=datetime.now().astimezone(), source='ERP',
                  customer_ref='C1', gross_amount='12.00', currency='USD')
    with pytest.raises(ValidationError):
        OrderCreated.model_validate(record, strict=True)
    record['gross_amount'] = Decimal('12.00')
    record['occurred_at'] = datetime(2026, 10, 29)
    with pytest.raises(ValidationError):
        OrderCreated.model_validate(record, strict=True)


@pytest.mark.parametrize('bad', ['0', '-1', '1000001', '1.5', '1e1', 'NaN', '+1'])
def test_quantity_boundary_rejects(cfg, valid_cases, bad):
    raw = raw_field_replace(valid_cases[2]['raw'], 'quantity', bad)
    assert validate(raw, 'quantity', cfg).status == 'REJECTED'


@pytest.mark.parametrize('good', ['1', '2', '1000000'])
def test_quantity_valid_boundaries(cfg, valid_cases, good):
    raw = raw_field_replace(valid_cases[2]['raw'], 'quantity', good)
    result = validate(raw, 'quantity', cfg)
    assert result.status == 'ACCEPTED'
    assert result.record.quantity == int(good)


@pytest.mark.parametrize('bad', ['0', '-1', '1.001', '1e2', 'NaN', 'Infinity', '+1', '999999999999999.99'])
def test_money_invalid_lexemes_or_bounds(cfg, valid_cases, bad):
    raw = raw_field_replace(valid_cases[1]['raw'], 'authorized_amount', bad)
    assert validate(raw, 'money', cfg).status == 'REJECTED'


@pytest.mark.parametrize('good', ['0.01', '1', '25.00', '9999999999999.99'])
def test_money_valid_boundaries(cfg, valid_cases, good):
    raw = raw_field_replace(valid_cases[1]['raw'], 'authorized_amount', good)
    result = validate(raw, 'money', cfg)
    assert result.status == 'ACCEPTED', result.canonical()
    assert result.record.authorized_amount == Decimal(good)


@pytest.mark.parametrize('bad', [
    '2026-10-29T14:00:00', '2026-13-29T14:00:00Z',
    '2026-10-29T14:00:00+15:00', '2026-10-29T14:00:00-05:99',
    '2026-02-29T14:00:00Z',
])
def test_timestamp_invalid_rejects(cfg, valid_cases, bad):
    raw = raw_field_replace(valid_cases[1]['raw'], 'occurred_at', bad)
    assert validate(raw, 'date', cfg).status == 'REJECTED'


@pytest.mark.parametrize('good', ['2024-02-29T14:00:00Z', '2026-10-29T14:00:00+14:00',
                                  '2026-10-29T14:00:00-05:00'])
def test_timestamp_valid_offsets(cfg, valid_cases, good):
    raw = raw_field_replace(valid_cases[1]['raw'], 'occurred_at', good)
    assert validate(raw, 'date', cfg).status == 'ACCEPTED'


def test_nested_duplicate_key_and_total_mismatch_reject(cfg, invalid_cases, valid_cases):
    assert validate(invalid_cases[5]['raw'], 'nested', cfg).status == 'REJECTED'
    base = valid_cases[0]['raw'].split(' | lines_json=')[0]
    nested = '[{"sku_code":"SKU-A","quantity":2,"quantity":2,"unit_price":"12.50"}]'
    escaped = nested.replace('"', r'\"')
    bad = base + ' | lines_json="' + escaped + '"'
    assert validate(bad, 'nested', cfg).status == 'REJECTED'


@pytest.mark.parametrize('raw', [None, 1, b'abc', {}, [], 'x'*4097])
def test_invalid_input_types_and_bytes_are_bounded(cfg, raw):
    result = validate(raw, 'bound', cfg)
    assert result.status == 'REJECTED'
    assert result.failure_category == Failure.INPUT_LIMIT


def test_config_unknown_registry_and_unsafe_matcher(tmp_path):
    source = json.loads((ROOT / 'examples/matrix_v1.json').read_text())
    for change in (('registry_key','arbitrary.module'), ('matcher', {'field': 'regex', 'equals':'.*', 'priority':10})):
        obj = deepcopy(source)
        obj['events'][0][change[0]] = change[1]
        p = tmp_path / 'bad.json'; p.write_text(json.dumps(obj))
        with pytest.raises(ConfigError):
            load_matrix(p)


def test_config_duplicate_keys_are_not_accepted(tmp_path):
    source = (ROOT / 'examples/matrix_v1.json').read_text()
    p = tmp_path / 'duplicate-key.json'
    p.write_text(source.replace('"version": "demo-v1",', '"version": "demo-v1", "version": "evil",', 1))
    with pytest.raises(ConfigError):
        load_matrix(p)


def test_config_boolean_budget_is_rejected(tmp_path):
    obj = json.loads((ROOT / 'examples/matrix_v1.json').read_text())
    obj['limits']['max_event_bytes'] = True
    p = tmp_path / 'boolean-budget.json';p.write_text(json.dumps(obj))
    with pytest.raises(ConfigError):
        load_matrix(p)


def test_ambiguity_fails_closed(tmp_path, valid_cases):
    obj = json.loads((ROOT / 'examples/matrix_v1.json').read_text())
    duplicate = deepcopy(obj['events'][0]);duplicate['schema_id'] += '_ALT'
    obj['events'].append(duplicate)
    p = tmp_path / 'ambiguous.json'; p.write_text(json.dumps(obj))
    config = load_matrix(p)
    assert validate(valid_cases[0]['raw'], 'ambiguous', config).failure_category == Failure.AMBIGUOUS_EVENT


def test_over_limit_batch_raises_without_truncation(cfg, valid_cases):
    from dataclasses import replace
    limited = replace(cfg, max_batch=2)
    generator = validate_many((valid_cases[0]['raw'] for _ in range(3)), 'limited', limited)
    assert next(generator).index == 0
    assert next(generator).index == 1
    with pytest.raises(ValueError, match='batch_limit'):
        next(generator)


# -------------------- SQLite and workflow contracts --------------------

def test_sqlite_atomic_persistence_and_quarantine(repo, cfg, valid_cases, invalid_cases):
    good = validate(valid_cases[0]['raw'], 'ref', cfg)
    bad = validate(invalid_cases[0]['raw'], 'ref2', cfg)
    assert repo.persist(good, 'TEN-ACME', 'EVT-001') == 'CREATED'
    assert repo.persist(good, 'TEN-ACME', 'EVT-001') == 'DUPLICATE'
    assert repo.persist(bad, 'REJECTED', 'bad-1') == 'CREATED'
    counts = repo.counts()
    assert counts['event_ingestion'] == counts['validation_result'] == counts['workflow_outbox'] == 2
    rows = repo.connection.execute('SELECT kind,state FROM workflow_outbox ORDER BY kind').fetchall()
    assert ('ACCEPTED_EVENT', 'PENDING') in rows
    assert ('QUARANTINE', 'QUARANTINED') in rows
    assert dispatch_once(repo, None) == 'DISABLED'
    sink = LocalStubSink()
    assert dispatch_once(repo, sink) == 'DONE'
    assert len(sink.delivered) == 1
    assert dispatch_once(repo, sink) == 'EMPTY'


def test_sqlite_idempotency_collision_rolls_back(repo, cfg, valid_cases):
    good = validate(valid_cases[1]['raw'], 'ref', cfg)
    changed = validate(raw_field_replace(valid_cases[1]['raw'], 'authorized_amount', '26.00'), 'ref', cfg)
    assert repo.persist(good, 'TEN-ACME', 'EVT-002') == 'CREATED'
    before = repo.counts().copy()
    with pytest.raises(IdempotencyConflict):
        repo.persist(changed, 'TEN-ACME', 'EVT-002')
    assert repo.counts() == before


def test_sqlite_foreign_key_enforced(repo):
    assert repo.connection.execute('PRAGMA foreign_keys').fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError):
        repo.connection.execute("INSERT INTO validation_error VALUES('error-id','missing-parent','path','code','safe')")


def test_workflow_retries_and_dead_letter(repo, cfg, valid_cases):
    good = validate(valid_cases[0]['raw'], 'ref', cfg)
    repo.persist(good, 'TEN-ACME', 'EVT-001')
    class RejectSink:
        def deliver(self, message):
            return False
    sink = RejectSink()
    for expected in ('RETRY', 'RETRY', 'DEAD_LETTER'):
        assert dispatch_once(repo, sink) == expected
        repo.connection.execute("UPDATE workflow_outbox SET next_attempt_at='2000-01-01T00:00:00+00:00'")
    assert dispatch_once(repo, sink) == 'EMPTY'


def test_persistence_rejects_duplicate_result_with_new_content(repo,cfg,valid_cases):
    r1 = validate(valid_cases[1]['raw'], 'i1', cfg)
    r2 = validate(valid_cases[1]['raw'].replace('PAY-FAKE-55','PAY-FAKE-56'),'i2',cfg)
    # Accepted events must be stored under the identity in their validated
    # record. The original suite's arbitrary 'same-ref' conflicts with the
    # separately verified cross-tenant/event identity security requirement.
    verified_event_ref = r1.record.event_id
    assert r2.record.event_id == verified_event_ref
    assert repo.persist(r1,'TEN-ACME',verified_event_ref) == 'CREATED'
    with pytest.raises(IdempotencyConflict):
        repo.persist(r2,'TEN-ACME',verified_event_ref)
    assert repo.counts()['event_ingestion'] == 1


def test_cli_complete_e2e(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / 'main.py'), '--matrix', str(ROOT / 'examples/matrix_v1.json'),
         '--input', str(ROOT / 'examples/replay.jsonl')],
        cwd=ROOT, env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')},
        capture_output=True, text=True, check=False, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    records = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert len(records) == 3
    assert [r['status'] for r in records] == ['ACCEPTED', 'REJECTED', 'ACCEPTED']
    assert all(r['config_fingerprint'] for r in records)


# -------------------- Release gates: real bugs must remain red --------------------

@pytest.mark.parametrize('position', range(5))
def test_release_serialization_must_preserve_all_event_fields(cfg, valid_cases, position):
    """Known SUT defect: ValidationResult.record typed as Common loses subclass fields."""
    result = validate(valid_cases[position]['raw'], 'release', cfg)
    assert result.status == 'ACCEPTED'
    wire = json.loads(result.canonical())['record']
    expected_fields = set(type(result.record).model_fields)
    assert set(wire) == expected_fields, f'{result.event_type}: fields lost in JSON: {sorted(expected_fields - set(wire))}'
    for key in wire:
        assert wire[key] is not None or key == 'lines_json'


@pytest.mark.parametrize('surrogate', ['\ud800', '\udfff'])
def test_release_invalid_unicode_must_not_crash(cfg, surrogate):
    """Known SUT defect: UTF-8 encoding raises UnicodeEncodeError for surrogates."""
    result = validate(surrogate, 'release', cfg)
    assert result.status == 'REJECTED'
    assert result.record is None


def test_release_cli_rejected_inputs_use_collision_safe_identity(tmp_path, invalid_cases):
    """Known SUT defect: default batch reference can collide across CLI invocations."""
    db = tmp_path / 'events.db'
    paths = []
    for i in (0, 2):
        path = tmp_path / f'in_{i}.jsonl'
        path.write_text(json.dumps({'raw': invalid_cases[i]['raw']}) + '\n', encoding='utf-8')
        paths.append(path)
    results = []
    for path in paths:
        completed = subprocess.run(
            [sys.executable, str(ROOT / 'main.py'), '--matrix', str(ROOT / 'examples/matrix_v1.json'),
             '--input', str(path), '--db', str(db)],
            cwd=ROOT, env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')},
            capture_output=True, text=True, check=False, timeout=15,
        )
        assert completed.returncode == 0, completed.stderr
        results.append(json.loads(completed.stdout.strip()))
    assert all(r.get('storage_state') == 'CREATED' for r in results), results



def test_release_malformed_field_type_matrix_is_typed_config_error(tmp_path):
    """Known SUT defect: list-valued field_types can escape with AttributeError."""
    obj = json.loads((ROOT / 'examples/matrix_v1.json').read_text())
    obj['events'][0]['field_types'] = list(obj['events'][0]['field_types'])
    p = tmp_path / 'malformed-field-types.json'; p.write_text(json.dumps(obj))
    with pytest.raises(ConfigError):
        load_matrix(p)


# -------------------- Actual Hypothesis properties/state machines --------------------

if HAS_HYPOTHESIS:
    @settings(max_examples=200, deadline=None, derandomize=True)
    @given(st.text(max_size=400))
    def test_hypothesis_unicode_never_crashes(cfg, sample):
        """Random Unicode includes invalid surrogates: do not hide product defects."""
        observed = validate(sample, 'fuzz', cfg)
        again = validate(sample, 'fuzz', cfg)
        assert observed.canonical() == again.canonical()

    @settings(max_examples=200, deadline=None, derandomize=True)
    @given(st.lists(st.tuples(st.sampled_from(('a', 'b', 'c', 'z')),
                              st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=12)),
                    min_size=1, max_size=4, unique_by=lambda kv: kv[0]))
    def test_hypothesis_differential_lexing_in_valid_domain(fields):
        sample = ' | '.join(f'{k}={v}' for k,v in fields)
        assert dict(tokenize(sample, 32)) == reference_lexer_restricted(sample)

    @settings(max_examples=150, deadline=None, derandomize=True)
    @given(st.lists(st.sampled_from(('event', 'tenant', 'order', 'source', 'event_id')),
                    min_size=2, max_size=12))
    def test_hypothesis_duplicate_keys_never_accepted(cfg, keys):
        if len(set(keys)) < len(keys):
            text = ' | '.join(f'{key}=SAFE' for key in keys)
            assert validate(text, 'fuzz', cfg).status == 'REJECTED'

    @settings(max_examples=150, deadline=None, derandomize=True)
    @given(st.integers(min_value=1, max_value=1_000_000),
           st.integers(min_value=1, max_value=999_999_999))
    def test_hypothesis_valid_inventory_quantity(cfg, valid_cases, quantity, identifier):
        raw = raw_field_replace(valid_cases[2]['raw'], 'quantity', str(quantity))
        raw = raw_field_replace(raw, 'event_id', f'E-{identifier}')
        result = validate(raw, 'fuzz', cfg)
        assert result.status == 'ACCEPTED', result.canonical()
        assert result.record.quantity == quantity

    class LexerStateMachine(RuleBasedStateMachine):
        def __init__(self):
            super().__init__()
            self.pieces: list[tuple[str, str]] = []
        @rule(key=st.sampled_from(('a','b','c')), value=st.text(alphabet='XYZ', min_size=1, max_size=5))
        def append(self, key, value):
            self.pieces.append((key,value))
        @invariant()
        def duplicate_rejects_or_unique_matches(self):
            if not self.pieces:
                return
            text = ' | '.join(f'{k}={v}' for k,v in self.pieces)
            if len(set(k for k,_ in self.pieces)) != len(self.pieces):
                with pytest.raises(ParseFault):
                    tokenize(text, 128)
            else:
                assert dict(tokenize(text,128)) == dict(self.pieces)
    TestLexerStateMachine = LexerStateMachine.TestCase
    TestLexerStateMachine.settings = settings(max_examples=35, stateful_step_count=25, deadline=None)

    class RepositoryStateMachine(RuleBasedStateMachine):
        def __init__(self):
            super().__init__()
            self.cfg = load_matrix(ROOT / 'examples/matrix_v1.json')
            self.base = json.loads((ROOT / 'examples/valid.jsonl').read_text().splitlines()[1])['raw']
            self.repo = SQLiteRepository(':memory:')
            self.repo.migrate()
            self.model: dict[str,str] = {}
        @rule(key=st.integers(min_value=0,max_value=5), cents=st.integers(min_value=1,max_value=9999))
        def insert(self, key, cents):
            event_ref = f'key-{key}'
            raw = raw_field_replace(self.base, 'authorized_amount', f'{cents//100}.{cents%100:02d}')
            raw = raw_field_replace(raw, 'event_id', event_ref)
            result = validate(raw, 'stateful', self.cfg)
            assert result.status == 'ACCEPTED'
            old = self.model.get(event_ref)
            if old is None:
                assert self.repo.persist(result, 'TEN-ACME', event_ref) == 'CREATED'
                self.model[event_ref] = result.input_sha256
            elif old == result.input_sha256:
                assert self.repo.persist(result, 'TEN-ACME', event_ref) == 'DUPLICATE'
            else:
                with pytest.raises(IdempotencyConflict):
                    self.repo.persist(result, 'TEN-ACME', event_ref)
        @invariant()
        def no_collisions_or_partial_writes(self):
            counts = self.repo.counts()
            assert counts['event_ingestion'] == len(self.model)
            assert counts['validation_result'] == len(self.model)
            assert counts['workflow_outbox'] == len(self.model)
        def teardown(self):
            self.repo.close()
    TestRepositoryStateMachine = RepositoryStateMachine.TestCase
    TestRepositoryStateMachine.settings = settings(max_examples=20, stateful_step_count=20, deadline=None)

else:
    @pytest.mark.skip(reason='Hypothesis missing: install application [test] extra')
    def test_hypothesis_not_available_in_local_runtime():
        pass


def test_release_hypothesis_dependency_must_be_installed():
    """An independent release gate is NOT green when fuzzing has not run."""
    assert HAS_HYPOTHESIS, "Hypothesis is missing: run `python -m pip install -e '.[test]'` and rerun"
