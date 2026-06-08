# CornerCheck, Devpost submission

**Track:** Slack Agent for Good
**Live status:** https://cornercheck.onrender.com (the agent itself runs inside Slack; this page confirms it is up). To use it directly, request a sandbox invite.
**Code:** https://github.com/StephenSook/cornercheck

---

## Tagline

A Slack agent that catches the cross-jurisdiction medical suspension a fight team would
otherwise miss, and refuses to clear a fighter when it cannot be sure who they are.

## Inspiration

In 2017, boxer Tim Hague died after a knockout in Edmonton. His medical suspension had lapsed
only days earlier, and he fought as a late replacement. The 2024 fatality inquiry called for a
single registry of fighters' medical and bout histories, which still does not exist. The
problem is worse across US state lines, where medical suspensions do not reliably travel
between commissions. For professional boxing, federal law (15 U.S.C. 6306(b)) requires the
licensing commission to consult the suspending one first, a step that is rarely performed in
practice; for MMA there is no federal rule at all. Fight operations already coordinate in
Slack. So the check belongs there too.

## What it does

You ask CornerCheck whether a fighter is cleared to compete. It does four things:

1. **Catches cross-jurisdiction suspensions** against curated, source-cited public commission
   records. When the booking commission differs from the suspending one, it surfaces the
   consult-first step: a binding federal requirement for boxing (15 U.S.C. 6306(b)), and for
   MMA the same discipline applied where no federal rule exists.
2. **Enforces return-to-competition windows** from Association of Ringside Physicians and ABC
   guidance (30 days after a TKO, 60 after a KO, 90 after a KO with loss of consciousness),
   with stricter state overlays, encoded as data-driven decision tables.
3. **Surfaces injury signals from the team's own Slack** through the Real-Time Search API, with
   permalink citations, so a "he got rocked in sparring Tuesday" message does not get lost.
4. **Refuses to clear an ambiguous identity.** Two pro fighters share a name; CornerCheck shows
   the candidates and asks a human to pick. A wrong "cleared" can be fatal. A wrong "refused"
   costs a phone call.

Every answer is decision support. A human always makes the final call, and every decision
lands in a tamper-evident, hash-chained audit ledger.

## How we built it

CornerCheck uses all three Slack agent surfaces as load-bearing parts, not decoration. The
**Assistant** pane and **Block Kit** (verdict cards, a disambiguation picker, a Data Table
audit view) are the interface. A **Claude agent** orchestrates a single **Model Context
Protocol** server that exposes the clearance tools. **Real-Time Search** grounds the agent in
the workspace's own injury chatter. The cards are designed so the safest action is the easy
one: a verdict reads at a glance from color and a single headline, and when identity is
ambiguous the card stops you with a side-by-side picker (weight class, record) instead of a
guess you would have to catch yourself.

The decision itself is deliberately not the language model's job. CornerCheck is a
neurosymbolic system: the model perceives natural language and orchestrates tools, but a
deterministic symbolic core decides clearance, a YAML decision-table rule engine and
probabilistic entity resolution, and the language model is gated out of the verdict by a
server-side hook. The safety property of that core is checked by Z3: a proof that the
suspension-window logic is equivalent to an independent safety specification over every
possible date and suspension interval, so if a suspension is active, the engine can never
return CLEAR. The ledger is an HMAC-SHA256 hash chain, so a single edited past clearance breaks
verification at the exact entry. The data is real: 4,107 fighters from a public dataset and 15
suspension cases verified against their cited sources.

## Challenges we ran into

Real-Time Search is keyword-only, with no synonyms, so we built an explicit combat-sports
injury lexicon and seeded the demo workspace with the language teams actually use. The
fail-closed design forced one rule everywhere. Whether the failure is an ambiguous identity,
an unreachable database, or a timed-out reasoning step, the system resolves toward "not
cleared," never toward a silent clear. And the formal proof taught us a lesson: our first Z3 draft was a tautology that proved
nothing. Rewriting it as an equivalence check against an independent specification not only
made it real, it caught an actual fail-open bug, a malformed date range that would have
silently cleared a suspended fighter.

## Accomplishments that we are proud of

A judge can use the deployed agent end to end, with no laptop of ours in the loop. A clearance
core whose safety is machine-checked, not just tested. An adversarial review that found a real
bug we then fixed. And a product that takes responsible AI seriously: it is decision support,
it cites every source, and it shows its work in an audit trail that cannot be quietly altered.

## What we learned

That the hard part of a safety agent is not the happy path, it is every way the system can be
wrong. Fail-closed has to be a property you can point at, in code and in a proof, not a
sentence in a README.

## What is next for CornerCheck

Wider commission coverage, calibrated abstention on the entity-resolution step, and a path for
commissions to contribute records directly. The architecture already separates the proven
decision core from the conversational surface, so each of these is additive.

## Built with

Python, Slack Bolt (Assistant, Socket Mode), Block Kit, Real-Time Search, Claude Agent SDK,
FastMCP (Model Context Protocol), Postgres (pg_trgm, jellyfish entity resolution), Z3,
Hypothesis, HMAC-SHA256 hash-chain ledger, Render.
