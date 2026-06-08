"""Full-chain verification against the live database."""

from cornercheck.db.pool import get_pool
from cornercheck.ledger.chain import VerifyResult, verify_rows
from cornercheck.ledger.store import hmac_key


def verify_chain() -> VerifyResult:
    """Recompute every link in seq order; report the FIRST break point exactly."""
    with get_pool().connection() as conn:
        cur = conn.execute("SELECT seq, payload, prev_hash, hash FROM ledger ORDER BY seq")
        return verify_rows(hmac_key(), ((s, p, ph, h) for s, p, ph, h in cur))
