"""Pure hash-chain logic (no database).

Payloads are floats-free JSON (str/int/bool/None/list/dict) so the canonical form
survives a Postgres jsonb round-trip byte-for-byte. Floats are rejected at append
time; verification recomputes the canonical form from what the database returns.
"""

import hashlib
import hmac
import json
from collections.abc import Iterable
from dataclasses import dataclass

GENESIS = "0" * 64


class UnsafePayloadError(ValueError):
    """Payload contains a value that does not survive a jsonb round-trip (e.g. float)."""


def _check_json_safe(value: object, path: str = "payload") -> None:
    if isinstance(value, float):
        raise UnsafePayloadError(f"{path}: floats are not allowed in ledger payloads")
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise UnsafePayloadError(f"{path}: non-string key {k!r}")
            _check_json_safe(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _check_json_safe(v, f"{path}[{i}]")
    elif value is not None and not isinstance(value, str | int | bool):
        raise UnsafePayloadError(f"{path}: unsupported type {type(value).__name__}")


def canonical(payload: dict) -> bytes:
    """Deterministic byte form of a payload: sorted keys, tight separators, UTF-8."""
    _check_json_safe(payload)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def link_hash(key: bytes, prev_hash: str, payload: dict) -> str:
    """HMAC-SHA256 over prev_hash || canonical(payload)."""
    return hmac.new(key, prev_hash.encode("ascii") + canonical(payload), hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    checked: int
    first_bad_seq: int | None
    detail: str


def verify_rows(key: bytes, rows: Iterable[tuple[int, dict, str, str]]) -> VerifyResult:
    """Walk (seq, payload, prev_hash, hash) rows in seq order; report the FIRST break."""
    expected_prev = GENESIS
    checked = 0
    for seq, payload, prev_hash, hash_ in rows:
        if prev_hash != expected_prev:
            return VerifyResult(False, checked, seq, f"prev_hash mismatch at seq {seq}")
        try:
            recomputed = link_hash(key, prev_hash, payload)
        except UnsafePayloadError as exc:
            return VerifyResult(False, checked, seq, f"unverifiable payload at seq {seq}: {exc}")
        if recomputed != hash_:
            return VerifyResult(False, checked, seq, f"hash mismatch at seq {seq}")
        expected_prev = hash_
        checked += 1
    return VerifyResult(True, checked, None, f"chain intact ({checked} entries)")
