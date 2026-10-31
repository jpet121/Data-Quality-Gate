"""Deliberately local stub only; no outbound connector is implemented or enabled."""
from __future__ import annotations
from typing import Protocol, cast

class WorkflowRepository(Protocol):
    def claim(self) -> tuple[str, int, str | dict[str, object]] | None: ...
    def finish(self, work_id: str, success: bool, max_attempts: int = 3) -> str: ...

class Sink(Protocol):
    def deliver(self,message:dict[str, object])->bool:...

class LocalStubSink:
    def __init__(self) -> None:
        self.delivered: list[str] = []
    def deliver(self,message:dict[str, object])->bool:
        self.delivered.append(cast(str, message['result_id']));return True

def dispatch_once(repo:WorkflowRepository,sink:Sink|None=None)->str:
    # None deliberately prevents external work. Only explicit passed sink executes.
    if sink is None:return 'DISABLED'
    claim=repo.claim()
    if not claim:return 'EMPTY'
    import json
    item_id,attempts,raw=claim
    try:
        # psycopg decodes JSONB to a dict; SQLite returns serialized JSON.
        message = raw if isinstance(raw, dict) else json.loads(raw)
        ok=sink.deliver(message)
    except Exception:ok=False
    return repo.finish(item_id,bool(ok))
