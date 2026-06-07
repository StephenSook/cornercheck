# CornerCheck

A Slack-native AI agent that helps fight-operations teams, matchmakers, and athletic commissions confirm whether a combat-sports athlete is safe and cleared to compete.

Built for the Slack Agent Builder Challenge, **Slack Agent for Good** track.

## The problem

Medical suspensions in boxing and MMA do not reliably cross jurisdictions. A fighter knocked out in one state can be booked in another before the mandatory medical hold expires, because the consultation step required by federal law (15 U.S.C. §6306) goes unperformed in practice. Fighters have died this way. The 2024 Tim Hague fatality inquiry explicitly recommended a single cross-commission view of fighters' medical and match histories. CornerCheck implements that recommendation where fight operations already coordinate: Slack.

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
- **Verification**: pytest + Hypothesis property tests, a Z3 proof that no input clears a suspended or unconfirmed fighter, CI on every push, and live smoke tests against the deployed instance

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
