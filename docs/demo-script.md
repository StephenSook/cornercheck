# CornerCheck demo video script

Target length: 2:45 to 3:00. Roughly 60 percent live screen demo, talking-head bookends.
Track: Slack Agent for Good. Live link shown on screen: https://cornercheck.onrender.com

Two recording modes, called out per beat:
- **[CAMERA]** = you on camera, talking head, looking into the lens.
- **[VOICEOVER]** = your voice over a screen recording, camera off.

Read the VO lines as written. They are AI-tone clean (no em-dashes, no filler). Natural
delivery beats polished delivery. Record each beat in a few takes; I assemble the best.

---

## Beat 0: Cold open  (0:00 to 0:15)  [CAMERA]

On camera, calm and direct. This is the human anchor; mean it.

> "In 2017, boxer Tim Hague died after a knockout in Edmonton. His medical suspension had
> lapsed days earlier, and he fought as a late replacement. The inquiry that followed called
> for a single registry of fighters' medical and bout histories. That registry still does not
> exist, and it is worse in the US, where suspensions do not reliably cross state lines. So I
> built the check, inside Slack, where fight operations already work."

Direction: hold eye contact with the lens on "He died." One beat of silence after it.

---

## Beat 1: Title  (0:15 to 0:18)  [TITLE CARD, no voice]

Full-screen card: **CornerCheck** / "Fighter-safety clearance, inside Slack" / Agent for Good.
(I generate this card.)

---

## Beat 2: What it is  (0:18 to 0:27)  [VOICEOVER over Slack]

Screen: the CornerCheck agent pane, empty, the intro message visible.

> "CornerCheck is a Slack agent. You ask whether a fighter is cleared to compete. It checks
> suspensions across jurisdictions, return-to-competition windows, and your team's own injury
> chatter. And it refuses to clear when it cannot be sure who the fighter is."

---

## Beat 3: A clean clearance  (0:27 to 0:38)  [VOICEOVER]

Screen: type `Is Merab Dvalishvili cleared?` Send. The green CLEAR card renders.

> "A clean fighter clears in seconds, with the date it is good as of, and an audit reference.
> Notice the footer: decision support, a human makes the final call. CornerCheck never
> pretends to be the doctor or the commission."

Direction: let the card sit on screen for a full second before cutting.

---

## Beat 4: The cross-jurisdiction catch  (0:38 to 1:08)  [VOICEOVER]

This is the headline. Screen: type `Is Junior dos Santos cleared in Texas?` Send. The red
DO NOT CLEAR card renders, with the CSAC suspension, the source link, the scales note, and
the workspace injury signal.

> "Now the one that matters. Is Junior dos Santos cleared to fight in Texas? No. There is an
> active, indefinite suspension from the California commission, pending neurological
> clearance after a knockout, and the source is cited right there. Texas and California are
> different commissions. For boxing, federal law requires them to consult each other first.
> For MMA, there is no such rule, and that is the gap CornerCheck closes by applying the same
> consult-first step. And look at the bottom: it found a warning in the team's own Slack,
> posted days earlier. That is the message that gets missed."

Direction: slow mouse-scroll down the card as you narrate each section. Pause on the source
link and on the "Workspace injury signal" line.

---

## Beat 5: Fail closed on identity  (1:08 to 1:35)  [VOICEOVER]

Screen: type `Is Bruno Silva cleared to fight?` Send. The disambiguation card renders with
the candidate list. Then click **Select** on the middleweight (record 23-9-0). The CLEAR
card renders inline.

> "Now watch it refuse. There are two professional fighters named Bruno Silva. Clearing the
> wrong one can be fatal, so CornerCheck will not guess. It shows you who it found, with
> weight class and record, and it asks a human to choose. I pick the middleweight, and now it
> clears that exact fighter, and writes that decision to the ledger."

Direction: hover the two identical "Bruno Silva" rows before clicking, so the viewer sees the
collision. This is the signature beat; give it room.

---

## Beat 6: It reasons  (1:35 to 1:55)  [VOICEOVER]

Screen: type `Why was Junior dos Santos refused?` Send. The agent's prose answer renders.

> "And it reasons. Ask why, and the agent walks back through the rule it applied, the
> suspension, the cited source, and it points medical questions to a ringside physician. The
> cards come from a deterministic engine. The agent explains around them. It never overrides
> them."

---

## Beat 7: Tamper-evident audit  (1:55 to 2:12)  [VOICEOVER]

Screen: click **View audit trail** on a card. The audit Data Table renders, "chain intact".

> "Every decision lands in a tamper-evident, hash-chained ledger. If anyone edits a past
> clearance, verification reports the exact entry that broke. In a sport where a missed
> suspension can end a life, you need a record that cannot be quietly changed."

---

## Beat 8: Formally verified  (2:12 to 2:33)  [VOICEOVER over a terminal]

Screen: a clean terminal. Run `uv run python scripts/z3_proof_demo.py`. The PROVEN lines and
the COUNTEREXAMPLE line print.

> "The part that decides clearance is formally verified. Z3 proves, across every possible
> date and suspension, that if a suspension is active, the engine can never return cleared.
> And it is not just a green checkmark. Plant a bug, and it hands you the exact fighter the
> broken logic would have cleared. Writing this proof caught a real bug, and we fixed it."

Direction: let the terminal output appear at a readable speed. If it runs too fast, I slow it
in the edit.

---

## Beat 9: How it works  (2:33 to 2:43)  [VOICEOVER over architecture diagram]

Screen: the architecture diagram (I generate it).

> "Under the hood: three Slack surfaces, Assistant, Block Kit, and Real-Time Search, a Claude
> agent driving a Model Context Protocol server, and a neurosymbolic core where the language
> model perceives, but a proven symbolic engine decides."

---

## Beat 10: Close  (2:43 to 2:58)  [CAMERA]

Back on camera. Warm, certain.

> "CornerCheck is live right now, and you can use it. It is one cross-check, in the place
> fight teams already coordinate, between a fighter and the worst day of someone's life.
> Thank you for watching."

End card: **cornercheck.onrender.com** + the GitHub repo + "Slack Agent for Good".

---

## What to record, and how

### Screen capture (Screen Studio)
- Use the **deployed** agent (the sandbox CornerCheck app), not your laptop's local copy.
- Open a **clean New Chat** before each beat so the thread is fresh.
- **Dismiss the bottom Slack banner** ("Slackbot, Enterprise search...") with its X before recording.
- Hide the browser bookmarks bar and close unrelated tabs, or record a clean browser window.
- Zoom the Slack pane (Cmd +) until card text is comfortably readable at video size.
- **Pre-warm every beat once** right before the real take: run each query so caches are warm
  and the RTS injury index is populated. The injury signal needs the seeded messages indexed
  (run `seeds/seed_demo.py` about three minutes before recording).
- Record each beat as its own clip. Do not try to do the whole demo in one take.

### Talking head (camera, beats 0 and 10 only)
- Eye-level camera, lens at your eye line, not below.
- Soft front light, plain or softly-blurred background.
- Look **into the lens**, not at your screen.
- Record the open and the close several times each. These two bookends carry the emotion.

### Voiceover (beats 2 through 9)
- Separate audio pass, quiet room, consistent distance from the mic.
- Read the lines naturally, conversational pace, slight emphasis on the bold-feeling words
  ("No.", "refuse", "cannot be quietly changed", "caught a real one").
- A pop filter helps. If you flub a line, pause and re-read the whole sentence so I can cut cleanly.

### What I assemble
VO timed to the screen action, talking-head open and close, title and architecture cards,
auto-captions (whisper), a music bed ducked under your voice, loudness normalized to -16 LUFS,
denoise on the VO, sub-three-minute final cut. Upload unlisted first for your review, then public.

### Pre-flight checklist (run right before recording)
1. Deployed agent responding (open the app, send one test query, delete that chat).
2. `seeds/seed_demo.py` run ~3 min prior so the RTS injury beat lands.
3. Bottom Slack banner dismissed; clean browser; Slack pane zoomed.
4. Terminal ready in the repo for the Z3 beat (`uv run python scripts/z3_proof_demo.py`).
5. One full dry run of all ten beats, no recording, to confirm nothing errors.
