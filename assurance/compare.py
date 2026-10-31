"""Explicit differential outcome taxonomy; missing oracles never establish agreement."""
from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class Observation:
    kind: str
    value: Any = None


def compare(reference: Observation | None, observed: Observation,
            valid: bool, repeat: Observation | None = None,
            comparator: Callable[[Any, Any], bool] = lambda a, b: a == b) -> str:
    if observed.kind == 'HARNESS_ERROR': return 'HARNESS_FAILURE'
    if repeat is not None and observed != repeat: return 'NONDETERMINISM'
    if observed.kind == 'TIMEOUT': return 'TIMEOUT'
    if observed.kind == 'RESOURCE': return 'RESOURCE_LIMIT'
    if observed.kind == 'EXCEPTION': return 'UNEXPECTED_CRASH'
    if observed.kind not in {'OK','REJECT'}: return 'HARNESS_FAILURE'
    if reference is None or reference.kind == 'UNCERTAIN': return 'ORACLE_UNCERTAINTY'
    if reference.kind not in {'OK','REJECT'} or observed.kind not in {'OK','REJECT'}:
        return 'HARNESS_FAILURE'
    try:
        equal = reference.kind == observed.kind and comparator(reference.value, observed.value)
    except Exception:
        return 'HARNESS_FAILURE'
    if equal:
        return 'VALID_AGREEMENT' if valid and observed.kind == 'OK' else 'PERMITTED_REJECTION_AGREEMENT' if not valid and observed.kind == 'REJECT' else 'ORACLE_UNCERTAINTY'
    return 'VALID_INPUT_DIVERGENCE' if valid else 'INVALID_INPUT_DIVERGENCE'
