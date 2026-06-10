"""Slack payload helpers shared across handler modules."""


def action_token(body: dict) -> str | None:
    """The ephemeral Real-Time Search action token, wherever this payload shape
    carries it: assistant message events, assistant-thread interactivity payloads, or
    message metadata. One helper instead of the two divergent copies the audit found."""
    return (
        body.get("event", {}).get("assistant_thread", {}).get("action_token")
        or body.get("assistant", {}).get("thread", {}).get("action_token")
        or body.get("message", {}).get("metadata", {}).get("event_payload", {}).get("action_token")
    )
