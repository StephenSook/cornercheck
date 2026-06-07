# Decisions log (ADR-lite)

One entry per spike verdict, frozen contract, or platform fact. Newest first within each stage.

## Stage 1 spikes

### 2026-06-07 - Spike A: Bolt Assistant over Socket Mode = WORKS

- Evidence (live CornerCheck sandbox): `assistant_thread_started` fired on 4/4 pane opens,
  handler latencies 0.445-0.607s; `user_message` echo round-trip 1.043s including
  `set_status` + `say` + `set_title`. All far under the 3s ceiling. Suggested prompts rendered
  and prompt-click sends the prompt text as a user message.
- Fix discovered: `features.app_home.messages_tab_enabled: true` is REQUIRED or the agent
  pane shows "Sending messages to this app has been turned off". Manifest patched (b9cb1b0).
- Surface confirmed by introspection (rule: installed package = truth): slack_bolt 1.28.0
  exports `Assistant`, `Say`, `SayStream`, `SetStatus`, `SetSuggestedPrompts`, `SetTitle`;
  Assistant decorators: `thread_started`, `user_message`, `thread_context_changed`, `bot_message`.
- Observation: the manifest `assistant_view.suggested_prompts` render in the pane; per-thread
  `set_suggested_prompts` from the handler coexists. Revisit which wins during Stage 5.

### 2026-06-07 - Platform fact: no assistant.search.* wrapper in slack_sdk 3.42.0 (latest)

- `WebClient` has no `assistant_search_context` / `assistant_search_info` methods even on the
  newest SDK (3.42.0 == PyPI latest). The RTS endpoints must be called raw via
  `client.api_call("assistant.search.context", json={...})`.
- Consequence for Stage 5: `search/rts.py` wraps the raw call behind our own typed client.

### 2026-06-07 - Spike B: RTS keyword search = WORKS

- **action_token location (the build-critical unknown): `body.event.assistant_thread.action_token`**,
  present on BOTH `assistant user_message` and `app_mention` events; 62-char ephemeral string,
  fresh per event; `assistant_thread` object contains only the token on these events.
- `assistant.search.context` (raw `api_call`, json body: query/limit/content_types/action_token)
  returns `ok=true` + real hits with rich metadata (`author_name`, `author_user_id`, `team_id`,
  `channel_id`, `channel_name`, `message_ts`, `content`).
- **Indexing lag is real: ~1-3 minutes.** Searches fired <1s after posting found 0 hits; the same
  query minutes later found 4. NOT a bot-author filter: bot-posted seeds ARE returned.
  Consequence: `seed_demo.py` posts seeds well before demo time; runbook gets a >=5 min buffer.
- `assistant.search.info` on this sandbox: `{"ok": true, "is_ai_search_enabled": true}`.
  AI search is ON: semantic mode may be available here (upside vs research expectation of
  keyword-only). Test semantic explicitly during Stage 5; keyword remains the designed floor.
- Intermittent `invalid_action_token` observed once on a later app_mention despite a
  fresh-extracted token (suspect single-use/short TTL or event redelivery). Stage 5 `rts.py`
  must degrade gracefully on token rejection (cached/fallback result + retry guidance), never crash.
- Fallback (conversations.history lexicon scan) NOT needed; primary path adopted.

### Spike C: Agent SDK stream -> say_stream - verdict pending

### Spike D: Data Table block - verdict pending
