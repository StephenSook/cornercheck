"""Ledger against real Postgres: append, verify, tamper detection, append-only guards."""

import psycopg
import pytest

from cornercheck.db.pool import get_pool
from cornercheck.ledger.store import append_entry
from cornercheck.ledger.verify import verify_chain


@pytest.mark.usefixtures("clean_ledger")
def test_append_and_verify_intact() -> None:
    for i in range(5):
        append_entry("test", "clearance_decision", {"fighter": f"F{i}", "decision": "CLEAR"})
    result = verify_chain()
    assert result.ok and result.checked == 5


@pytest.mark.usefixtures("clean_ledger")
def test_tamper_is_reported_at_exact_seq() -> None:
    for i in range(5):
        append_entry("test", "clearance_decision", {"fighter": f"F{i}", "n": i})
    # Privileged bypass of the append-only triggers: exactly the attack the chain catches.
    with get_pool().connection() as conn:
        conn.execute("SET session_replication_role = replica")
        conn.execute("UPDATE ledger SET payload = jsonb_set(payload, '{n}', '999') WHERE seq = 3")
        conn.execute("SET session_replication_role = DEFAULT")
    result = verify_chain()
    assert not result.ok
    assert result.first_bad_seq == 3
    assert "seq 3" in result.detail


@pytest.mark.usefixtures("clean_ledger")
def test_update_blocked_by_trigger() -> None:
    append_entry("test", "clearance_decision", {"fighter": "F0"})
    with get_pool().connection() as conn, pytest.raises(psycopg.errors.RaiseException) as exc:
        conn.execute("UPDATE ledger SET actor = 'evil' WHERE seq = 1")
    assert "append-only" in str(exc.value)


@pytest.mark.usefixtures("clean_ledger")
def test_delete_blocked_by_trigger() -> None:
    append_entry("test", "clearance_decision", {"fighter": "F0"})
    with get_pool().connection() as conn, pytest.raises(psycopg.errors.RaiseException) as exc:
        conn.execute("DELETE FROM ledger WHERE seq = 1")
    assert "append-only" in str(exc.value)


def test_least_privilege_roles_exist(db: str) -> None:
    with get_pool().connection() as conn:
        rows = conn.execute(
            "SELECT rolname FROM pg_roles"
            " WHERE rolname IN ('cornercheck_app', 'cornercheck_reader')"
        ).fetchall()
    assert {r[0] for r in rows} == {"cornercheck_app", "cornercheck_reader"}
