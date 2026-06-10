// Beat timeline for the CornerCheck demo, mirrors docs/demo-script.md v2.1 exactly.
// All times in seconds at 30 fps. STRICT ceiling 3:00; target cut 2:50-2:55.

export const FPS = 30;

export type Beat = {
  id: string;
  title: string;
  from: number; // seconds
  to: number; // seconds
  mode: "camera" | "voiceover" | "card";
  // Filename inside public/footage/ once recorded; undefined renders the placeholder.
  footage?: string;
  // Voiceover audio inside public/vo/ once recorded.
  vo?: string;
  script: string;
};

export const BEATS: Beat[] = [
  {
    id: "beat0",
    title: "Cold open",
    from: 0,
    to: 22,
    mode: "camera",
    footage: "camera-beat0.mp4",
    script:
      "In 2017, fighter Tim Hague died after a knockout in a boxing match. His medical suspension had lapsed days earlier, and he fought as a late replacement. Nobody re-checked. The records existed. Nothing forced the check. So I built it, inside Slack, where fight operations already work.",
  },
  {
    id: "beat1",
    title: "Title card",
    from: 22,
    to: 25,
    mode: "card",
    script: "",
  },
  {
    id: "beat2",
    title: "The whole card, at once",
    from: 25,
    to: 48,
    mode: "voiceover",
    footage: "beat2.mp4",
    script:
      "Clear a whole lineup at once. Green: no recorded suspension matched. Red: blocked, with the reason cited underneath. And the yellow one says NEEDS PICK, because it refuses to guess who that fighter even is. Every verdict on this board just landed in a tamper-evident audit ledger.",
  },
  {
    id: "beat3",
    title: "The cross-jurisdiction catch",
    from: 48,
    to: 72,
    mode: "voiceover",
    footage: "beat3.mp4", // RETAKE PENDING: missing the RTS injury-warning line (re-seed first)
    vo: "beat3.m4a",
    script:
      "The catch that matters. Blocked: an active indefinite suspension from the California commission, pending neurological clearance after a knockout. Source cited right there. Texas is a different commission, and that gap is what CornerCheck closes. At the bottom, a warning surfaced from the team's own Slack messages. And the footnote: identity confirmed by a calibrated statistical gate.",
  },
  {
    id: "beat4",
    title: "Fail closed on identity",
    from: 72,
    to: 90,
    mode: "voiceover",
    footage: "beat4.mp4",
    vo: "beat4.m4a",
    script:
      "Two professional fighters are named Bruno Silva. Clearing the wrong one can be fatal, so it will not guess. It shows both, with weight class and record, and a human picks. The pick itself is written to the ledger.",
  },
  {
    id: "beat5",
    title: "A second source that can only tighten",
    from: 90,
    to: 107,
    mode: "voiceover",
    footage: "beat5.mp4", // RETAKE PENDING: clip ends on the picker; needs pick + CLEAR card w/ live line
    vo: "beat5.m4a",
    script:
      "Boxing verdicts get corroborated against a live record feed. That line is his actual professional record from the live source. The rule is one-way: live data can tighten a verdict. Nothing it says can ever loosen one.",
  },
  {
    id: "beat6",
    title: "The proof, in the product",
    from: 107,
    to: 125,
    mode: "voiceover",
    footage: "beat6.mp4", // trim to end ON the PROVEN section (tail drifts)
    vo: "beat6.m4a",
    script:
      "Every card carries this button. Click it, and the Z3 theorem prover re-proves, right then, that an active suspension can never come out cleared, across every possible date. The second line is a deliberately broken version that must fail. No rubber stamps.",
  },
  {
    id: "beat7",
    title: "An audit you can hand to a commission",
    from: 125,
    to: 140,
    mode: "voiceover",
    footage: "beat7.mp4",
    vo: "beat7.m4a",
    script:
      "Every decision, hash-chained and append-only. Edit one past entry and verification names it. One click exports the whole trail to a Canvas you can hand to a promoter or a commission.",
  },
  {
    id: "beat8",
    title: "It watches the roster on its own",
    from: 140,
    to: 153,
    mode: "voiceover",
    footage: "beat8.mp4",
    vo: "beat8.m4a",
    script:
      "And it does not wait to be asked. A daily digest: windows about to lapse, windows just lapsed, new blocks. Deterministic triggers only. Quiet days send nothing.",
  },
  {
    id: "beat9",
    title: "Run the proof yourself",
    from: 153,
    to: 163,
    mode: "voiceover",
    footage: "beat9.mp4",
    vo: "beat9.m4a",
    script:
      "All of it is live right now. Real numbers from the real database, and that proof button works for you too. Milliseconds.",
  },
  {
    id: "beat10",
    title: "Close",
    from: 163,
    to: 173,
    mode: "camera",
    footage: "camera-beat10.mp4",
    script:
      "CornerCheck is one cross-check, where fight teams already work, between a fighter and the worst day of someone's life. Thank you for watching.",
  },
];

export const TOTAL_SECONDS = 173; // 2:53
export const TOTAL_FRAMES = TOTAL_SECONDS * FPS;
