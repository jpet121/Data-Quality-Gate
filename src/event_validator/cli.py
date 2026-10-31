"""CLI: JSONL raw input or plain text; output JSONL with deterministic outcomes."""
from __future__ import annotations
import argparse,json,sys,sqlite3
from typing import Iterator, Any
from pathlib import Path
from .matrix import load_matrix,ConfigError
from .core import validate_many

def main(argv: list[str] | None = None) -> int:
    p=argparse.ArgumentParser(description='Strict versioned event validator, synthetic demo only')
    p.add_argument('--matrix',required=True)
    p.add_argument('--input',default='-',help='JSONL objects with raw key; - for stdin')
    p.add_argument('--db',default=None,help='Optional local SQLite path')
    p.add_argument('--batch-ref',default='batch')
    args=p.parse_args(argv)
    try:cfg=load_matrix(args.matrix)
    except ConfigError as ex:
        print(json.dumps({'status':'CONFIG_ERROR','reason':str(ex)}),file=sys.stderr);return 2
    def stream() -> Iterator[Any]:
        fh=sys.stdin if args.input=='-' else open(args.input,encoding='utf-8')
        try:
            for line in fh:
                try:x=json.loads(line);yield x['raw'] if isinstance(x,dict) else x
                except (json.JSONDecodeError,KeyError,TypeError):yield line.rstrip('\n')
        finally:
            if fh is not sys.stdin:fh.close()
    repo=None
    if args.db:
        from .storage import SQLiteRepository
        try:
            repo=SQLiteRepository(args.db);repo.migrate()
        except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
            if repo is not None: repo.close()
            print(json.dumps({'status':'STORAGE_ERROR','reason':type(exc).__name__}),file=sys.stderr)
            return 3
    storage_failed=False
    try:
        for r in validate_many(stream(),args.batch_ref,cfg):
            obj=json.loads(r.canonical())
            if repo:
                try:
                    # Invalid events have no verified business event_id. Bind their
                    # storage identity to the normalized batch position AND input
                    # digest, preventing distinct rejected payloads on separate
                    # invocations from sharing the default batch/00000000 key.
                    event_ref = (r.record.event_id if r.record else
                                 f'{r.input_ref}:{r.input_sha256}')
                    obj['storage_state'] = repo.persist(
                        r, tenant_id=r.record.tenant_id if r.record else 'REJECTED',
                        event_ref=event_ref)
                except Exception as ex:
                    storage_failed=True
                    obj['storage_state']='ERROR:'+type(ex).__name__
            print(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True))
    except ValueError as ex:
        print(json.dumps({'status':'INPUT_LIMIT','reason':str(ex)}),file=sys.stderr);return 2
    except (OSError, UnicodeError) as ex:
        print(json.dumps({'status':'INPUT_ERROR','reason':type(ex).__name__}),file=sys.stderr);return 2
    finally:
        if repo:repo.close()
    return 3 if storage_failed else 0
