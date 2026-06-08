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

### 2026-06-07 - Spike C: Claude Agent SDK -> say_stream = WORKS

- Full brain pattern proven live in the sandbox: SDK session (claude-agent-sdk 0.2.93,
  model claude-opus-4-8) + in-process SDK-MCP tool + token streaming into the agent pane via
  `say_stream()` ChatStream (`append`/`stop`). Tool call rendered as a visible thinking line;
  final answer derived strictly from tool data.
- **The SDK ships a BUNDLED Claude Code CLI** (`claude_agent_sdk/_bundled/claude`): the Render
  worker needs NO separate CLI install. Deploy concern eliminated.
- Cost/latency on opus: $0.7298 for the query; 13.8s total, ~11s of it cold CLI boot.
  **Stage 4 design: persistent `ClaudeSDKClient` session per worker, never per-message
  `query()` cold boots.** Budget note: ~$0.73/verdict on opus is fine inside the
  $150-200 ceiling but smoke runs should count it.
- SDK defers MCP tools: the agent called ToolSearch to load `mcp__spike__lookup_fighter`
  before using it (one extra turn). Acceptable; revisit preloading in Stage 4.
- `say_stream` is injected via `context["say_stream"]` (AttachingConversationKwargs
  middleware); `ChatStream.stop(blocks=...)` can attach Block Kit at stream end - that is the
  verdict-card delivery mechanism for Stage 5.

### 2026-06-07 - Spike D: Data Table ("table") block = WORKS

- `chat.postMessage` with `type: "table"` block (rows of raw_text cells + column_settings)
  returned ok=true AND renders as a real table on desktop web AND iOS mobile
  (verified by Stephen, screenshots in session). Columns, alignment, wrapping all honored.
- Block schema per live docs: max 100 rows x 20 cells, raw_text/raw_number/rich_text cells,
  column align/is_wrapped. Adopted as the audit-ledger view for Stage 5;
  section-fields fallback not needed.

## Stage 4

### 2026-06-07 - FROZEN CONTRACTS (Stage 5 builds against these; changes require a new entry)

MCP server: ONE FastMCP stdio server named `cornercheck`
(`python -m cornercheck.mcp_server.server`). Tool surface (7 of max 12):

| Tool | Args | Returns |
|---|---|---|
| er_resolve_fighter | query | {status: CONFIRMED/AMBIGUOUS/NOT_FOUND, note, candidates[{fighter_id, full_name, weight_class, record, sport, jurisdiction, score}]} |
| er_fighter_details | fighter_id | {fighter{...}, suspensions[{type,start,end,indefinite,jurisdiction,reason,source_url}]} |
| rules_evaluate_clearance | fighter_id, on_date?, target_jurisdiction? | {decision, on_date, active[], applied_rules[], consultation_note} |
| rules_outcome_window | outcome(TKO/KO/KO_LOC), cause?, sparring? | {days, applied_rules[]} |
| ledger_record_clearance | thread_key, fighter_id, decision, on_date?, target_jurisdiction?, actor | {recorded, seq?, hash?, refusal_reason?} |
| ledger_recent_entries | limit=10 | {entries[...]} |
| ledger_verify_chain | - | {ok, checked, first_bad_seq, detail} |

Search/RTS is NOT an MCP tool: the Bolt layer (Stage 5) runs the RTS scan itself and
injects results as spotlighted untrusted data in the prompt. Keeps the action_token out
of LLM-visible space and untrusted content out of the tool-result channel (report 17).

**Fail-closed = three independent locks:**
1. IN-TOOL: ledger_record_clearance re-runs the rule engine server-side; a decision that
   contradicts the engine is refused AND the denied attempt is itself ledgered
   (action=clearance_write_denied: the attack becomes audit evidence).
2. PRETOOLUSE HOOK: denies ledger_record_clearance unless the SessionStore shows the
   thread confirmed this exact fighter_id AND the engine verdict recorded for that thread
   matches the decision being written.
3. SCHEMA: brain output is a Pydantic ClearanceVerdict; the Slack card renders from the
   deterministic pipeline result, never from LLM prose.

Brain: ONE persistent ClaudeSDKClient (bundled CLI subprocess), per-Slack-thread
`session_id`, asyncio loop in a daemon thread with a sync `ask()` facade for Bolt.
Deterministic pipeline (er.resolve -> SessionStore -> rules.evaluate -> ledger.append)
drives the clearance card; the agent narrates and handles free-form Q&A via the tools.

### 2026-06-07 - Stage 4 SHIPPED: results + adversarial-review hardening

- Live smoke (twice, pre and post hardening): agent loads the real stdio MCP server,
  calls er_resolve + rules_evaluate live, narrates with verbatim source URL + 6306(b)
  note, and says "not my judgment, engine's". Adversarial override attempt REFUSED with
  a correct explanation of the guards. ~$0.9/turn opus; 26s cold, 6s warm.
- Forced adversarial review (code-reviewer + silent-failure-hunter, both verified
  findings against installed SDK source) converged on one critical: the SDK client's
  receive stream is a single shared queue with NO per-session demux, so concurrent or
  timed-out asks bleed responses across threads. FIXED: whole query+receive span
  serialized by an asyncio.Lock created on the loop thread; timeout cancels the
  coroutine and poisons the client (next ask rebuilds it).
- Also fixed from review: pipeline gate assert replaced with explicit fail-closed check
  (asserts vanish under -O); hook gate denies malformed payloads instead of passing;
  SessionStore.snapshot() so the gate never reads torn state; garbage fighter_id/date on
  the write tool returns a structured refusal that is ITSELF ledgered (probes leave a
  trace); denial-ledger failures surface as audit_warning instead of vanishing; every
  tool wrapped in a typed ERROR envelope that can never read as a clearance (system
  prompt rule 7 forbids inferring anything from ERROR).
- 74 tests green including regression tests pinning every review finding.

## Stage 3

### 2026-06-07 - Rule engine + entity resolution = SHIPPED, live-smoked on real data

- Rules are DATA: arp_base.yaml (ABC minimums TKO=30/KO=60; ARP KO_LOC=90) +
  state_overlays.yaml (ABC BSI head-shot overlay) + sparring overlay explicitly attributed
  to CornerCheck/ARP guidance, never to the ABC. Longest-rule-wins. A test proves a YAML
  override changes outcomes with zero Python edits.
- portion interval algebra for suspension windows (indefinite = right-open to infinity;
  overlaps union). Cross-jurisdiction active suspension attaches the 15 U.S.C. §6306(b)
  consultation note (enforce-the-law framing).
- ER: pg_trgm high-recall retrieve + Jaro-Winkler re-score + banding
  (T_HIGH=0.95, MARGIN=0.04, T_LOW=0.82; identical normalized names ALWAYS disambiguate;
  below T_LOW refuses). splink offline training deferred per plan slip clause; golden
  fixtures pin behavior; revisit in Stage 7.
- Live real-data smoke (2026-06-07): Bruno Silva -> AMBIGUOUS with BOTH real UFC Bruno
  Silvas at score 1.00; Dvalishvili -> CONFIRMED; dos Santos -> DO_NOT_CLEAR (indefinite
  CSAC, §6306 note vs Texas, source cited); Chavez Jr -> CLEAR today but DO_NOT_CLEAR
  back-dated to 2012-12-01 (time-travel demo beat); Diaz -> DO_NOT_CLEAR until 2026-11-12.
- 48 tests green: rule matrix, Hypothesis "CLEAR iff no active suspension" +
  "every blocking suspension is cited", ER banding goldens, live-Postgres ER fixtures
  (ZZ-Test throwaway fighters work on empty CI DB and seeded local DB alike).

## Stage 2

### 2026-06-07 - Seed data: dataset + 15 verified suspension cases

- **Fighters dataset: github.com/KgKevin0/UFC-Stats UFC_fighters.csv, MIT license (verified),
  4,107 real fighters.** Downloaded at seed time into gitignored seeds/data/downloads/, never
  committed. Backup option: fivethirtyeight undefeated-boxers (CC-BY-4.0). Skipped:
  Greco1899/scrape_ufc_stats (GPL-3.0; MIT alternative is cleaner for an Apache-2.0 repo).
- **15 suspension cases, every one source-cited and adversarially verified** (workflow
  wf_eb8d2099-8f9: 3 finder agents + per-case verifier agents fetching each source URL;
  1 case honestly rejected when its source supported the death narrative but not a formal
  suspension record). Manual spot-checks on the anchors: Santillan (BDB no-fight order until
  Jul 31, fought Jul 20 in Argentina) and Chavez Jr (NSAC 9 months, $900k) re-verified by hand.
- Coverage: 6 jurisdictions (CSAC, TDLR, NSAC, NYSAC, Maryland, German BDB), boxing + MMA,
  KO/TKO/medical/administrative. **Four suspensions genuinely active as of 2026-06-07**
  (dos Santos indefinite, Diaz to 2026-11-12, Brahimaj/Coria indefinite, Strickland indefinite):
  live real-data demo material, zero mocking.
- Demo scenario mapping asserted by seed_db.py on every run: CLEAR=Merab Dvalishvili;
  cross-jurisdiction=Julio Cesar Chavez Jr.; active suspension=Junior dos Santos;
  RTS chatter=Geoff Neal; disambiguation=Bruno Silva (TWO real UFC fighters share the name).

### 2026-06-07 - Ledger + environment facts

- Tamper-evidence demo verified end to end on real Postgres: INTACT -> forge seq 4 via
  session_replication_role=replica bypass -> verify reports BROKEN at exactly seq 4 -> reset.
- Local docker Postgres maps host port 5433 (system Postgres owns 5432 on this machine).
- psycopg3 runs param-less execute() over the simple protocol, so multi-statement migration
  files apply fine from the python runner; CI applies the same files via psql.
- **Local pytest leaves test-keyed ledger rows** (integration suite truncates/appends with the
  conftest test key). After running pytest locally: `verify_chain_demo.py reset` +
  `seed_db.py --force`. Future hardening: dedicated cornercheck_test database.
- Ledger payloads are floats-free JSON by design (jsonb round-trip determinism); enforced by
  UnsafePayloadError at append and covered by Hypothesis properties.

### STAGE 1 GATE: PASSED 2026-06-07

All four spikes WORKS on their primary paths; zero pre-chosen fallbacks adopted.
Completed in one evening vs the planned Jun 8-12 window. Stage 2 (data foundation +
hash-chain ledger) unblocked ~4 days ahead of schedule.
