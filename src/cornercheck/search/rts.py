"""Real-Time Search injury scan.

Runs in the Bolt process: the ephemeral action_token (from
body.event.assistant_thread.action_token, verified spike B) is passed straight to the
Slack API and NEVER enters LLM-visible space. Degrades gracefully: any error returns no
hits (verified-real intermittent invalid_action_token must never crash the verdict).
"""

import logging
from dataclasses import dataclass

from slack_sdk import WebClient

from cornercheck.search.lexicon import mentions_injury

log = logging.getLogger("cornercheck.rts")


@dataclass(frozen=True)
class InjuryHit:
    permalink: str
    channel_id: str
    message_ts: str
    snippet: str
    author: str


def _last_name(full_name: str) -> str:
    parts = full_name.split()
    return parts[-1] if parts else full_name


def injury_scan(
    client: WebClient, action_token: str | None, fighter_full_name: str, limit: int = 10
) -> list[InjuryHit]:
    """Keyword-search the workspace for the fighter's name, keep only injury-mentioning
    messages, resolve permalinks. Returns [] on any failure."""
    if not action_token:
        return []
    last = _last_name(fighter_full_name)
    try:
        result = client.api_call(
            "assistant.search.context",
            json={
                "query": last,
                "action_token": action_token,
                "content_types": ["messages"],
                "limit": limit,
            },
        )
    except Exception as exc:
        # warning, not info: a persistent RTS outage would otherwise be invisible in prod.
        log.warning("RTS injury_scan failed (non-fatal, no injury hits shown): %s", exc)
        return []
    data = result.data if isinstance(result.data, dict) else {}
    messages = (data.get("results") or {}).get("messages", [])
    hits: list[InjuryHit] = []
    for m in messages:
        content = m.get("content") or ""
        if not mentions_injury(content):
            continue
        channel_id = m.get("channel_id", "")
        ts = m.get("message_ts", "")
        permalink = _permalink(client, channel_id, ts)
        hits.append(
            InjuryHit(
                permalink=permalink,
                channel_id=channel_id,
                message_ts=ts,
                snippet=content[:180],
                author=m.get("author_name", "unknown"),
            )
        )
    return hits


def _permalink(client: WebClient, channel_id: str, ts: str) -> str:
    try:
        resp = client.chat_getPermalink(channel=channel_id, message_ts=ts)
        return str(resp.get("permalink", ""))
    except Exception:
        return ""


def _defang(text: str) -> str:
    """Neutralize angle brackets so untrusted content cannot forge the closing delimiter
    and escape the spotlight envelope (review finding F2). Replaces ASCII < > with the
    single-pointing-angle look-alikes U+2039 / U+203A."""
    return text.replace("<", "‹").replace(">", "›")


def spotlight(hits: list[InjuryHit]) -> str:
    """Wrap untrusted workspace text for safe inclusion in an LLM prompt (report 17).
    The model is instructed to treat anything in this block as DATA, never instructions."""
    if not hits:
        return ""
    lines = "\n".join(f"- [{_defang(h.author)}] {_defang(h.snippet)}" for h in hits)
    return f"<untrusted-slack-content>\n{lines}\n</untrusted-slack-content>"
