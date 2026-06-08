"""Append-only ledger writes. Chain head is serialized with an advisory lock."""

from dataclasses import dataclass
from datetime import datetime

from psycopg.types.json import Jsonb

from cornercheck.config import get_settings
from cornercheck.db.pool import get_pool
from cornercheck.ledger.chain import GENESIS, link_hash

_CHAIN_LOCK = 815001  # project-unique advisory lock id for chain-head serialization


def hmac_key() -> bytes:
    key = get_settings().cornercheck_ledger_hmac_key
    if not key:
        raise RuntimeError("CORNERCHECK_LEDGER_HMAC_KEY is not set; refusing to write ledger")
    return key.encode()


@dataclass(frozen=True)
class LedgerEntry:
    seq: int
    ts: datetime
    actor: str
    action: str
    payload: dict
    prev_hash: str
    hash: str


def append_entry(actor: str, action: str, payload: dict) -> LedgerEntry:
    key = hmac_key()
    with get_pool().connection() as conn, conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (_CHAIN_LOCK,))
        row = conn.execute("SELECT hash FROM ledger ORDER BY seq DESC LIMIT 1").fetchone()
        prev_hash = row[0] if row else GENESIS
        entry_hash = link_hash(key, prev_hash, payload)
        out = conn.execute(
            "INSERT INTO ledger (actor, action, payload, prev_hash, hash)"
            " VALUES (%s, %s, %s, %s, %s) RETURNING seq, ts",
            (actor, action, Jsonb(payload), prev_hash, entry_hash),
        ).fetchone()
        if out is None:  # never an assert: this must survive python -O
            raise RuntimeError("ledger INSERT returned no row; write not confirmed")
    return LedgerEntry(out[0], out[1], actor, action, payload, prev_hash, entry_hash)
