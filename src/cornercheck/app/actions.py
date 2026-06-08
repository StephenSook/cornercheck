"""Block Kit interactivity: the disambiguation pick and the audit-trail button."""

import logging
from datetime import date

from slack_bolt import Ack, App, Say
from slack_sdk import WebClient

from cornercheck.app.blocks.audit_table import build_audit_table, fallback_text
from cornercheck.app.blocks.disambiguation_card import decode
from cornercheck.app.blocks.verdict_card import build_verdict_card
from cornercheck.app.blocks.verdict_card import fallback_text as verdict_fallback
from cornercheck.brain.pipeline import confirm_candidate
from cornercheck.db.pool import get_pool
from cornercheck.ledger.verify import verify_chain
from cornercheck.search.rts import injury_scan

log = logging.getLogger("cornercheck.actions")


def register_actions(app: App) -> None:
    @app.action("select_fighter")
    def on_select_fighter(ack: Ack, body: dict, say: Say, client: WebClient) -> None:
        ack()
        value = body["actions"][0]["value"]
        fighter_id, on_date_s, query = decode(value)
        thread_key = _thread_key(body)
        on_date = date.fromisoformat(on_date_s) if on_date_s else None
        # Re-derive the target jurisdiction from the original query text.
        from cornercheck.app.parse import parse_request

        target = parse_request(query).target_jurisdiction if query else None
        verdict = confirm_candidate(thread_key, fighter_id, query, on_date, target)
        if verdict is None:
            say("That selection didn't match a candidate I offered. Please re-run the check.")
            return
        action_token = body.get("assistant", {}).get("thread", {}).get("action_token") or body.get(
            "message", {}
        ).get("metadata", {}).get("event_payload", {}).get("action_token")
        hits = (
            injury_scan(client, action_token, verdict.fighter_name or "")
            if verdict.fighter_name
            else []
        )
        say(blocks=build_verdict_card(verdict, injury_hits=hits), text=verdict_fallback(verdict))

    @app.action("view_audit_trail")
    def on_view_audit(ack: Ack, say: Say) -> None:
        ack()
        entries = _recent_entries()
        result = verify_chain()
        say(
            blocks=build_audit_table(entries, result.ok, result.detail),
            text=fallback_text(result.ok),
        )


def _thread_key(body: dict) -> str:
    container = body.get("container", {})
    channel = container.get("channel_id", body.get("channel", {}).get("id", ""))
    thread_ts = container.get("thread_ts") or container.get("message_ts", "")
    return f"{channel}:{thread_ts}"


def _recent_entries() -> list[dict]:
    with get_pool().connection() as conn:
        rows = conn.execute(
            "SELECT seq, ts, actor, action, payload FROM ledger ORDER BY seq DESC LIMIT 20"
        ).fetchall()
    return [
        {"seq": r[0], "ts": r[1].isoformat(), "actor": r[2], "action": r[3], "payload": r[4]}
        for r in rows
    ]
