"""Every MCP tool exercised through a real fastmcp Client against the live server object
(in-process transport; same code path the stdio subprocess serves). No API key needed."""

import asyncio
import json
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

import pytest
from fastmcp import Client

from cornercheck.db.pool import get_pool
from cornercheck.mcp_server.server import mcp

PREFIX = "ZZ-MCPTest"


@pytest.fixture
def mcp_fixture(db: str) -> Iterator[dict[str, str]]:
    ids: dict[str, str] = {}
    with get_pool().connection() as conn:
        for key, name in {
            "clean": f"{PREFIX} Clean Fighter",
            "held": f"{PREFIX} Held Fighter",
        }.items():
            row = conn.execute(
                "INSERT INTO fighters (full_name, weight_class, wins, losses, draws, sport,"
                " source) VALUES (%s, 'Lightweight', 9, 0, 0, 'mma', 'mcp-test') RETURNING id",
                (name,),
            ).fetchone()
            assert row is not None
            ids[key] = str(row[0])
        conn.execute(
            "INSERT INTO suspensions (fighter_id, suspension_type, start_date, end_date,"
            " indefinite, jurisdiction, reason, source_url) VALUES"
            " (%s, 'KO', %s, %s, false, 'Nevada (test)', 'KO loss', 'https://example.test')",
            (ids["held"], date.today() - timedelta(days=5), date.today() + timedelta(days=55)),
        )
    yield ids
    with get_pool().connection() as conn:
        conn.execute("DELETE FROM fighters WHERE full_name LIKE %s", (f"{PREFIX} %",))


def _call(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    async def run() -> dict[str, Any]:
        async with Client(mcp) as client:
            result = await client.call_tool(tool, args)
            block = result.content[0]
            return json.loads(block.text)

    return asyncio.run(run())


def test_tool_surface_is_frozen_contract() -> None:
    async def run() -> list[str]:
        async with Client(mcp) as client:
            return sorted(t.name for t in await client.list_tools())

    assert asyncio.run(run()) == sorted(
        [
            "er_resolve_fighter",
            "er_fighter_details",
            "rules_evaluate_clearance",
            "rules_outcome_window",
            "ledger_record_clearance",
            "ledger_recent_entries",
            "ledger_verify_chain",
        ]
    )


def test_resolve_and_details(mcp_fixture: dict[str, str]) -> None:
    out = _call("er_resolve_fighter", {"query": f"{PREFIX} Clean Fighter"})
    assert out["status"] == "CONFIRMED"
    details = _call("er_fighter_details", {"fighter_id": mcp_fixture["clean"]})
    assert details["fighter"]["record"] == "9-0-0"
    assert details["suspensions"] == []


def test_evaluate_clearance_blocks_held_fighter(mcp_fixture: dict[str, str]) -> None:
    out = _call(
        "rules_evaluate_clearance",
        {"fighter_id": mcp_fixture["held"], "target_jurisdiction": "Texas"},
    )
    assert out["decision"] == "DO_NOT_CLEAR"
    assert out["active"][0]["source_url"] == "https://example.test"
    assert out["consultation_note"]


def test_outcome_window_with_overlay() -> None:
    out = _call("rules_outcome_window", {"outcome": "TKO", "cause": "head_shot_stoppage"})
    assert out["days"] == 45


def test_record_clearance_in_tool_guard_refuses_and_ledgers_the_attempt(
    mcp_fixture: dict[str, str],
) -> None:
    out = _call(
        "ledger_record_clearance",
        {
            "thread_key": "t-guard",
            "fighter_id": mcp_fixture["held"],
            "decision": "CLEAR",  # contradicts the engine: must refuse
        },
    )
    assert out["recorded"] is False
    assert "contradicts the rule engine" in out["refusal_reason"]
    recent = _call("ledger_recent_entries", {"limit": 1})
    assert recent["entries"][0]["action"] == "clearance_write_denied"


def test_record_clearance_accepts_engine_matching_decision(
    mcp_fixture: dict[str, str],
) -> None:
    out = _call(
        "ledger_record_clearance",
        {"thread_key": "t-ok", "fighter_id": mcp_fixture["held"], "decision": "DO_NOT_CLEAR"},
    )
    assert out["recorded"] is True and out["seq"] >= 1
    verify = _call("ledger_verify_chain", {})
    assert verify["ok"] is True
