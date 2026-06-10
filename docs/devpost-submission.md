# CornerCheck, Devpost submission (v2)

**Track:** Slack Agent for Good
**Live:** https://cornercheck.onrender.com (the live public dashboard: real database stats,
the audit chain verified at page load, and the Z3 safety proof anyone can run in
milliseconds; the agent itself runs inside Slack). Judge sandbox access provided per the
submission requirements.
**Code:** https://github.com/StephenSook/cornercheck

---

## Tagline

The agent that refuses to guess: fail-closed fighter-safety clearance inside Slack, with a
formally proven rule core, statistically certified identity, and an audit trail you can hand
to a commission.

## Inspiration

In 2017, fighter Tim Hague died after a knockout in a boxing match in Edmonton. His medical
suspension had lapsed only days earlier, and he fought as a late replacement. The 2024
fatality inquiry called for a single registry of fighters' medical and bout histories, which
still does not exist. The problem is worse across US state lines, where medical suspensions
do not reliably travel between commissions. For professional boxing, federal law
(15 U.S.C. 6306(b)) requires the licensing commission to consult the suspending one first;
for MMA there is no federal rule at all. Fight operations already coordinate in Slack. So the
check belongs there too.

## What it does

**Ask about one fighter, or paste a whole fight card.** Every bout lands on one board, banded
CLEAR, DO NOT CLEAR, or NEEDS PICK, with the blocking record cited. Underneath that surface:

1. **Catches cross-jurisdiction suspensions** against 54 curated, source-cited commission
   cases across 10 athletic commissions (every case adversarially verified against its
   source).
   When the booking commission differs from the suspending one, it surfaces the consult-first
   step: binding federal law for boxing, the same discipline applied for MMA where no federal
   rule exists.
2. **Enforces return-to-competition windows** from Association of Ringside Physicians and ABC
   guidance, encoded as data-driven decision tables.
3. **Refuses to clear an ambiguous identity.** Two pro fighters named Bruno Silva is not an
   edge case here; it is the point. The match threshold is conformally calibrated on 4,203
   query variants built from the real fighter table: when two candidates are statistically
   plausible, the math itself forces a human pick.
4. **Corroborates against a live second source, one-way.** Boxing verdicts check the live
   boxing-data.com record. A disagreement tightens the verdict; nothing the live source says
   can ever loosen one. API down means annotated, never blocked, never loosened.
5. **Watches the roster on its own.** A daily monitor re-checks every suspension window (the
   Hague failure was a lapsed window nobody re-verified) and posts a deterministic digest to
   an ops channel. No model decides or phrases an alert. Quiet days send nothing.
6. **Surfaces injury signals from the team's own Slack** via Real-Time Search, with permalink
   citations, so a "got rocked in sparring Tuesday" message does not get lost.
7. **Proves itself in the product.** Every verdict card carries a "See the safety proof"
   button that runs the actual Z3 equivalence proof live, plus a non-vacuity control that
   must fail, showing the prover is no rubber stamp. The same proof runs on the public
   dashboard for anyone, in milliseconds.
8. **Exports the audit trail to a Canvas**, chain-verified at the moment of export, ready to
   hand to a promoter or commission.

Every answer is decision support. A human always makes the final call, and every decision,
every alert, and every refusal lands in a tamper-evident, hash-chained audit ledger.

## How we built it

Slack platform surfaces are load-bearing, not decoration: the **Assistant** pane, **Block
Kit** (verdict cards, the whole-card Data Table board, a disambiguation picker, the audit
table, the live proof button), one **Model Context Protocol** server a **Claude agent**
orchestrates, **Real-Time Search** for the injury signal, **Canvas** for the exportable audit
trail, and **Incoming Webhooks** for the daily roster digest.

The decision itself is deliberately not the language model's job. CornerCheck is
neurosymbolic: the model perceives language and orchestrates tools; a deterministic symbolic
core decides; a server-side hook gates the model out of the verdict. Both halves of the
fail-closed claim carry formal backing:

- **The rules half is proven.** Z3 checks the suspension-window logic for equivalence with an
  independently written safety specification over all dates and intervals: an active
  suspension can never produce CLEAR. The proof is non-vacuous (a deliberately broken variant
  must yield a counterexample) and it earned its keep by catching a real fail-open bug, a
  malformed date range that silently cleared a suspended fighter, before launch.
- **The identity half is certified.** Split conformal prediction calibrates the match
  threshold on 4,203 query variants built from the real fighter table (95% coverage,
  holdout-checked). A confirmation requires a singleton prediction set; a statistically
  plausible runner-up demotes to a human pick. The exact quantile is about fifty auditable
  lines, no ML library required.

The design follows one rule: the safest action is always the easy one. A whole fight card
reads at a glance from three color bands; ambiguity is an interaction (a side-by-side picker
with weight class and record), not an error message; the formal proof is a button on the
card, not a paper; and when anything is unavailable, the surface says so plainly instead of
pretending. The public dashboard applies the same honesty: every number on it comes from the
production database at request time.

The composition rule everywhere is tighten-only: live corroboration, the conformal gate, and
the monitor can each block or annotate, and none of them can ever loosen a verdict. The
ledger is an HMAC-SHA256 hash chain; editing one past entry breaks verification at that exact
entry. The data is real: 4,100+ fighters from a public dataset and 54 suspension cases
verified against their cited sources, with honesty stated in-product: a CLEAR means no
recorded suspension matched, and commissions remain the source of truth.

## Challenges we ran into

Real-Time Search is keyword-only, so we built a combat-sports injury lexicon. Fail-closed
forced one rule everywhere: ambiguous identity, unreachable database, timed-out reasoning,
all resolve toward "not cleared," never a silent clear. Our first Z3 draft was a tautology
that proved nothing; rewriting it as an equivalence check against an independent spec made it
real and caught an actual bug. And our own adversarial review process kept earning its keep:
it found a retrieval gap that could certify a same-name impostor as unique, a markdown
injection that could forge rows in the exported audit document, and a monitoring watermark
with a permanent blind spot. Each one was demonstrated, fixed, and pinned with a regression
test before it shipped.

## Accomplishments we are proud of

A judge can use everything live, with no laptop of ours in the loop: the Slack agent, the
proof button, the Canvas export, the daily digest, and a public dashboard whose numbers come
from the production database at request time. A clearance core whose safety is
machine-checked and whose identity gate carries a statistical guarantee. 251 tests, an
append-only audit ledger, and a review process that treats "plausible" as the enemy.

## What we learned

The hard part of a safety agent is not the happy path, it is every way the system can be
wrong. Fail-closed has to be a property you can point at, in code, in a proof, and in a
calibration artifact, not a sentence in a README.

## What is next for CornerCheck

Wider commission coverage, a path for commissions to contribute records directly, and richer
workflow automation inside Slack. The architecture already separates the proven decision core
from the conversational surface, so each of these is additive.

## Built with

Python, Slack Bolt (Assistant, Socket Mode), Block Kit, Real-Time Search, Canvas API,
Incoming Webhooks, Claude Agent SDK, FastMCP (Model Context Protocol), Postgres (pg_trgm,
jellyfish entity resolution), Z3 theorem prover, split conformal prediction, Hypothesis,
HMAC-SHA256 hash-chain ledger, boxing-data.com API, Render.
