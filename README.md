# CornerCheck

A Slack-native AI agent that helps fight-operations teams, matchmakers, and athletic commissions confirm whether a combat-sports athlete is safe and cleared to compete.

Built for the Slack Agent Builder Challenge, **Slack Agent for Good** track.

## The problem

Medical suspensions in boxing and MMA do not reliably cross jurisdictions. A fighter knocked out under one commission can be booked under another before the mandatory medical hold expires. For professional boxing, federal law (15 U.S.C. §6306(b)) requires the licensing commission to consult the suspending one first; in practice that step is often skipped, and MMA has no federal equivalent at all. In 2017, boxer Tim Hague died after a knockout in Edmonton; his prior medical suspension had lapsed days earlier and he fought as a late replacement. The 2024 fatality inquiry called for a single registry of fighters' medical and bout histories. CornerCheck brings that consult-first discipline to where fight operations already coordinate: Slack.

## What it does

- **Catches cross-jurisdiction medical suspensions** against curated, source-cited public commission records
- **Enforces return-to-competition windows** from the Association of Ringside Physicians / ABC guidelines (TKO 30 days, KO 60 days, KO with loss of consciousness 90 days, plus stricter state overlays), encoded as data-driven decision tables
- **Surfaces injury signals from the team's own Slack** via the Real-Time Search API, with permalink citations
- **Refuses to clear when fighter identity is ambiguous.** The pipeline is Retrieve, then Disambiguate (a human picks from candidates shown with DOB, weight class, record, last bout, jurisdiction), then Clear. Ambiguity fails closed. A wrong "cleared" can be fatal; a wrong "refused" costs a phone call.

CornerCheck is decision support. A human always makes the final call, and every decision lands in a tamper-evident, hash-chained audit ledger.

## Architecture (overview)

- **Slack surface**: Bolt for Python, Assistant middleware, Socket Mode; Block Kit verdict cards, disambiguation picker, audit Data Table, App Home
- **Agent brain**: Claude Agent SDK orchestrating one modular FastMCP server (ledger, rules, and search tool groups); a deterministic PreToolUse hook makes the fail-closed guarantee code, not a model decision
- **Computational core**: probabilistic entity resolution (splink offline, jellyfish + pg_trgm live), a YAML decision-table rule engine, and an HMAC-SHA256 hash-chained Postgres audit ledger
- **Verification**: pytest + Hypothesis property tests, and **Z3 machine-checked verification** that the engine's suspension-window logic is equivalent to an independently-written safety specification over all dates and suspension intervals (if a suspension is active on the date, the engine can never return CLEAR), which no finite test suite can cover. The verification is not a tautology (an in-suite mutation test proves it catches engine corruption), and it earned its keep: it surfaced a real fail-open bug, a malformed `end < start` date range that silently cleared a suspended fighter, now fixed to fail closed. CI on every push; live smoke tests against the deployed instance.

CornerCheck is a **neurosymbolic system**: the LLM perceives natural language and orchestrates tools, but the clearance decision itself comes from a deterministic symbolic core (rule engine + entity resolution) whose safety invariant is formally verified. The model proposes; the proven symbolic core disposes. That separation is what lets a fail-closed guarantee be code, not a prompt.

Run the proof yourself: `uv run python scripts/z3_proof_demo.py`. It proves the invariant, then deletes a safety guard and watches Z3 produce the exact fighter the broken logic would wrongly clear.

Full diagram: `docs/architecture.md` (in progress).

## Status

Under active build for the July 13, 2026 submission. See commit history for progress.

## Development

```bash
uv sync                  # install
docker compose up -d     # local Postgres
uv run pytest            # tests (live-marked tests excluded by default)
uv run ruff check .      # lint
uv run mypy src tests    # types
```

## License

Apache-2.0. See `LICENSE`.
