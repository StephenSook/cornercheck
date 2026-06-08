"""App Home dashboard: recent clearance decisions + live chain integrity."""

import logging
from typing import Any

from slack_bolt import App
from slack_sdk import WebClient

from cornercheck.db.pool import get_pool
from cornercheck.ledger.verify import verify_chain

log = logging.getLogger("cornercheck.home")


def register_home(app: App) -> None:
    @app.event("app_home_opened")
    def on_home_opened(event: dict, client: WebClient) -> None:
        try:
            client.views_publish(user_id=event["user"], view=_home_view())
        except Exception:
            log.exception("views_publish failed")


def _home_view() -> dict[str, Any]:
    result = verify_chain()
    entries = _recent_decisions()
    integrity = ":lock: intact" if result.ok else ":rotating_light: BROKEN"
    blocks: list[dict[str, Any]] = [
        {"type": "header", "text": {"type": "plain_text", "text": "CornerCheck"}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Fighter-safety clearance for fight-operations teams. Cross-jurisdiction "
                    "suspensions, return windows, and your team's own injury chatter, with a "
                    "tamper-evident audit trail. *Decision support: a human makes the final call.*"
                ),
            },
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"Audit chain: {integrity} - {result.detail}"}],
        },
        {"type": "divider"},
        {"type": "header", "text": {"type": "plain_text", "text": "Recent decisions"}},
    ]
    if not entries:
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": "_No decisions recorded yet._"}}
        )
    for e in entries:
        p = e["payload"] or {}
        decision = p.get("decision", p.get("attempted_decision", "-"))
        emoji = (
            ":red_circle:"
            if "DO_NOT" in str(decision)
            else (":large_green_circle:" if decision == "CLEAR" else ":white_circle:")
        )
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{emoji} *{p.get('fighter_name', 'unknown')}* - {decision}\n"
                        f"seq {e['seq']} | {e['action']} | {e['ts'][:16].replace('T', ' ')}"
                    ),
                },
            }
        )
    return {"type": "home", "blocks": blocks}


def _recent_decisions() -> list[dict[str, Any]]:
    with get_pool().connection() as conn:
        rows = conn.execute(
            "SELECT seq, ts, action, payload FROM ledger"
            " WHERE action IN ('clearance_decision', 'clearance_write_denied')"
            " ORDER BY seq DESC LIMIT 8"
        ).fetchall()
    return [{"seq": r[0], "ts": r[1].isoformat(), "action": r[2], "payload": r[3]} for r in rows]
