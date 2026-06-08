"""Shared fixtures. CI provides a postgres:16 service; locally use docker compose up -d.

Integration tests SKIP when Postgres is unreachable locally, but FAIL in CI
(CI must never silently skip the database suite).
"""

import os

import psycopg
import pytest

# Must land before the first get_settings() call anywhere in the test session.
os.environ.setdefault("CORNERCHECK_LEDGER_HMAC_KEY", "test-only-hmac-key-not-a-secret")

from cornercheck.config import get_settings

get_settings.cache_clear()


@pytest.fixture(scope="session")
def db() -> str:
    url = get_settings().database_url
    try:
        psycopg.connect(url, connect_timeout=3).close()
    except Exception as exc:
        if os.environ.get("CI"):
            raise RuntimeError(f"CI requires Postgres but it is unreachable: {exc}") from exc
        pytest.skip(f"Postgres unavailable at {url}: {exc}")
    from cornercheck.db.migrate import apply_migrations

    apply_migrations()
    return url


@pytest.fixture
def clean_ledger(db: str) -> None:
    """Reset the ledger between tests, bypassing the append-only triggers.

    session_replication_role=replica disables ordinary triggers; this is the same
    documented bypass the tamper demo uses, and exactly what the hash chain exists
    to catch.
    """
    from cornercheck.db.pool import get_pool

    with get_pool().connection() as conn:
        conn.execute("SET session_replication_role = replica")
        conn.execute("TRUNCATE ledger RESTART IDENTITY")
        conn.execute("SET session_replication_role = DEFAULT")
