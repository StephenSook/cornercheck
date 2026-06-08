"""Banding logic: the fail-closed identity gate.

Hand-tuned thresholds (splink offline training deferred per plan's slip clause;
golden fixtures in tests pin the behavior either way):
- CONFIRMED only when the top score clears T_HIGH, beats the runner-up by MARGIN,
  and the name is unique among candidates
- identical normalized names ALWAYS disambiguate (two real UFC "Bruno Silva"s)
- below T_LOW: refuse (NOT_FOUND): never guess on a fatal-risk decision
"""

from dataclasses import dataclass, field
from typing import Literal

T_HIGH = 0.95
T_LOW = 0.82
MARGIN = 0.04
MAX_CANDIDATES = 5


@dataclass(frozen=True)
class Candidate:
    fighter_id: str
    full_name: str
    weight_class: str | None
    record: str
    sport: str
    jurisdiction: str | None
    score: float


@dataclass(frozen=True)
class ResolutionResult:
    status: Literal["CONFIRMED", "AMBIGUOUS", "NOT_FOUND"]
    candidates: list[Candidate] = field(default_factory=list)
    note: str = ""


def _norm(name: str) -> str:
    return " ".join(name.lower().split())


def band(candidates: list[Candidate]) -> ResolutionResult:
    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)[:MAX_CANDIDATES]
    if not ranked or ranked[0].score < T_LOW:
        return ResolutionResult(
            "NOT_FOUND",
            ranked,
            note="no candidate met the minimum match threshold; refusing to guess",
        )
    top = ranked[0]
    same_name = [c for c in ranked if _norm(c.full_name) == _norm(top.full_name)]
    if len(same_name) >= 2:
        return ResolutionResult(
            "AMBIGUOUS",
            ranked,
            note=f"{len(same_name)} fighters share the name {top.full_name!r}; human pick required",
        )
    runner_up_gap = top.score - ranked[1].score if len(ranked) > 1 else 1.0
    if top.score >= T_HIGH and runner_up_gap >= MARGIN:
        return ResolutionResult("CONFIRMED", [top], note="unique high-confidence match")
    return ResolutionResult("AMBIGUOUS", ranked, note="match confidence in the disambiguation band")
