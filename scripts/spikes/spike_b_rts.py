"""Spike B: Real-Time Search (assistant.search.context) keyword mode.

Verifies (Stage 1 gate):
1. an action_token arrives on assistant user_message events (payload/body introspection)
2. assistant.search.context (keyword mode) returns a freshly posted real message
3. assistant.search.info reports search capability (or is plan-gated; record either way)

slack_sdk 3.42.0 (latest) has no assistant.search.* wrapper, so calls go through
client.api_call() raw. See docs/decisions.md.

Run:  uv run python scripts/spikes/spike_b_rts.py
Then: 1) in the sandbox, run /invite @CornerCheck in #general
      2) message the CornerCheck agent anything (e.g. "scan")
"""

import json
import logging
import time

from slack_bolt import App, Assistant, BoltContext, Say, SetStatus
from slack_sdk import WebClient

from cornercheck.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("spike_b")

SEED_TEXT = (
    "Heads up: Dragan got rocked in sparring on Tuesday, we sat him down for the week. "
    "(spike B seed message)"
)
SEED_CHANNEL = "#general"

settings = get_settings()
app = App(token=settings.slack_bot_token)
assistant = Assistant()


def _redact(token: str | None) -> str:
    return f"{token[:12]}... ({len(token)} chars)" if token else "NONE"


def post_seed(client: WebClient) -> str:
    """Post the injury seed message; returns status string."""
    try:
        resp = client.chat_postMessage(channel=SEED_CHANNEL, text=SEED_TEXT)
        log.info("SPIKE-B seed posted to %s ts=%s", SEED_CHANNEL, resp["ts"])
        return "seed posted"
    except Exception as exc:
        log.warning("SPIKE-B seed post FAILED: %s", exc)
        return f"seed post failed: {exc}"


@assistant.thread_started
def on_thread_started(say: Say) -> None:
    say("Spike B (RTS) online. /invite @CornerCheck in #general, then send me any message.")


@assistant.user_message
def on_user_message(
    payload: dict,
    body: dict,
    client: WebClient,
    context: BoltContext,
    say: Say,
    set_status: SetStatus,
) -> None:
    t0 = time.monotonic()
    set_status("running RTS spike...")

    # 1. Hunt for the action_token in everything Bolt gives us
    token_locations = {
        "payload.action_token": payload.get("action_token"),
        "body.event.action_token": body.get("event", {}).get("action_token"),
        "body.action_token": body.get("action_token"),
        "context.action_token": context.get("action_token"),
    }
    found = {k: _redact(v) for k, v in token_locations.items() if v}
    log.info("SPIKE-B payload keys: %s", sorted(payload.keys()))
    log.info("SPIKE-B body keys: %s", sorted(body.keys()))
    log.info("SPIKE-B action_token locations: %s", found or "NOT FOUND ANYWHERE")
    action_token = next((v for v in token_locations.values() if v), None)

    # 2. Make sure the seed message exists (re-attempt every run; harmless duplicate)
    seed_status = post_seed(client)

    # 3. assistant.search.info
    try:
        info = client.api_call("assistant.search.info", json={})
        log.info("SPIKE-B search.info: %s", json.dumps(info.data))
        info_summary = json.dumps(info.data)
    except Exception as exc:
        log.warning("SPIKE-B search.info FAILED: %s", exc)
        info_summary = f"search.info failed: {exc}"

    # 4. assistant.search.context keyword query for the seed's lexicon word
    search_summary: str
    try:
        req: dict = {"query": "rocked sparring", "limit": 5}
        if action_token:
            req["action_token"] = action_token
        result = client.api_call("assistant.search.context", json=req)
        messages = (result.data.get("results") or {}).get("messages", [])
        log.info("SPIKE-B search.context ok=%s hits=%d", result.data.get("ok"), len(messages))
        for m in messages[:3]:
            log.info(
                "SPIKE-B hit: channel=%s ts=%s text=%r",
                m.get("channel_id"),
                m.get("message_ts"),
                (m.get("content") or "")[:120],
            )
        search_summary = f"{len(messages)} hit(s) for 'rocked sparring'"
        if messages:
            first = messages[0]
            search_summary += f"; first: {(first.get('content') or '')[:80]!r}"
    except Exception as exc:
        log.warning("SPIKE-B search.context FAILED: %s", exc)
        search_summary = f"search.context failed: {exc}"

    say(
        "Spike B results:\n"
        f"- action_token: {'FOUND ' + ', '.join(found) if found else 'NOT FOUND'}\n"
        f"- seed: {seed_status}\n"
        f"- search.info: {info_summary[:300]}\n"
        f"- search.context: {search_summary}\n"
        f"- total {time.monotonic() - t0:.2f}s"
    )
    log.info("SPIKE-B handler done in %.2fs", time.monotonic() - t0)


app.use(assistant)


if __name__ == "__main__":
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    log.info("SPIKE-B starting Socket Mode connection...")
    SocketModeHandler(app, settings.slack_app_token).start()
