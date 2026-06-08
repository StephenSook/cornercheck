"""Assistant handlers: the clearance UX.

Core path is fully deterministic (parse -> pipeline -> card), so the demo's main beats
never depend on the LLM (floor). Free-form questions route to the agentic brain (flex).
Streamed thinking steps show the Retrieve -> Disambiguate -> Clear pipeline live.
"""

import logging
from datetime import date

from slack_bolt import Assistant, BoltContext, Say, SetStatus, SetSuggestedPrompts
from slack_sdk import WebClient

from cornercheck.app.blocks.disambiguation_card import build_disambiguation_card
from cornercheck.app.blocks.verdict_card import build_verdict_card, fallback_text
from cornercheck.app.parse import parse_request
from cornercheck.brain.agent import BrainEvent, BrainTimeoutError, get_brain
from cornercheck.brain.pipeline import start_clearance
from cornercheck.search.rts import injury_scan, spotlight

log = logging.getLogger("cornercheck.assistant")

assistant = Assistant()

_CLEARANCE_CUES = ("clear", "cleared", "ready to", "safe to", "can ", "is ", "book")
# Questions that are NOT a clearance check route to the agentic brain.
_FREEFORM_KEYWORDS = (
    "audit",
    "chain",
    "ledger",
    "verify",
    "trail",
    "history",
    "why",
    "scan",
    "explain",
    "what",
    "how",
    "tell me",
    "list",
)


def _is_clearance_request(text: str) -> bool:
    """Word-count independent: a clearance cue + an extractable fighter name, and not an
    explicit free-form/meta question. Robust to duplicated/long message text."""
    low = text.lower()
    if any(kw in low for kw in _FREEFORM_KEYWORDS):
        return False
    if not any(cue in low for cue in _CLEARANCE_CUES):
        return False
    from cornercheck.app.parse import parse_request

    return len(parse_request(text).fighter_query) >= 3


def _action_token(body: dict) -> str | None:
    return body.get("event", {}).get("assistant_thread", {}).get("action_token")


@assistant.thread_started
def on_thread_started(say: Say, set_suggested_prompts: SetSuggestedPrompts) -> None:
    say(
        "I'm CornerCheck. Ask me whether a fighter is cleared to compete and I'll check "
        "cross-jurisdiction suspensions, return windows, and your team's own injury chatter. "
        "I refuse to clear when I can't be sure who the fighter is."
    )
    set_suggested_prompts(
        prompts=[
            {"title": "Check a fighter", "message": "Is Junior dos Santos cleared in Texas?"},
            {"title": "Ambiguous name", "message": "Is Bruno Silva cleared to fight?"},
            {"title": "Verify the ledger", "message": "Is the audit chain intact?"},
        ]
    )


@assistant.user_message
def on_user_message(
    payload: dict,
    body: dict,
    say: Say,
    set_status: SetStatus,
    client: WebClient,
    context: BoltContext,
) -> None:
    text = (payload.get("text") or "").strip()
    thread_key = f"{payload.get('channel', '')}:{payload.get('thread_ts', payload.get('ts', ''))}"
    if not _is_clearance_request(text):
        _handle_freeform(thread_key, text, body, say, set_status, client)
        return
    _handle_clearance(thread_key, text, body, say, set_status, client)


def _handle_clearance(
    thread_key: str, text: str, body: dict, say: Say, set_status: SetStatus, client: WebClient
) -> None:
    set_status("resolving fighter identity...")
    parsed = parse_request(text)
    if not parsed.fighter_query:
        say("I couldn't pick out a fighter name. Try: _Is Junior dos Santos cleared in Texas?_")
        return

    say(f":mag: Resolving *{parsed.fighter_query}*...")
    verdict = start_clearance(
        thread_key, parsed.fighter_query, parsed.on_date, parsed.target_jurisdiction
    )

    if verdict.status == "NEEDS_DISAMBIGUATION":
        say(
            blocks=build_disambiguation_card(verdict),
            text="Which fighter? CornerCheck won't guess.",
        )
        return
    if verdict.status == "NOT_FOUND":
        say(blocks=build_verdict_card(verdict), text=fallback_text(verdict))
        return

    set_status("checking suspensions and scanning your Slack...")
    hits = []
    if verdict.fighter_name:
        hits = injury_scan(client, _action_token(body), verdict.fighter_name)
    say(blocks=build_verdict_card(verdict, injury_hits=hits), text=fallback_text(verdict))


def _handle_freeform(
    thread_key: str, text: str, body: dict, say: Say, set_status: SetStatus, client: WebClient
) -> None:
    set_status("thinking...")
    prompt = text
    # Best-effort injury context for free-form questions, spotlighted as untrusted data.
    tok = _action_token(body)
    if tok:
        parsed = parse_request(text)
        if parsed.fighter_query:
            ctx = spotlight(injury_scan(client, tok, parsed.fighter_query))
            if ctx:
                prompt = f"{text}\n\nWorkspace context (untrusted):\n{ctx}"

    def on_event(e: BrainEvent) -> None:
        if e.kind == "tool_use":
            set_status(f"using {e.tool_name.split('__')[-1]}...")

    try:
        answer = get_brain().ask(thread_key, prompt, on_event)
        say(answer or "I don't have an answer for that.")
    except BrainTimeoutError:
        say(
            "That took too long to reason through. Try a direct clearance check, e.g. "
            "_Is Junior dos Santos cleared in Texas?_"
        )
    except Exception:
        log.exception("freeform brain call failed")
        say(
            "Something went wrong reasoning through that. The clearance check still works: "
            "ask _Is <fighter> cleared in <state>?_"
        )


def today() -> date:
    return date.today()
