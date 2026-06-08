"""Deterministic parse of a clearance request: fighter name, date, target jurisdiction.

Imperfect extraction is SAFE: the ER banding fails closed, so a rough name lands in the
disambiguation card rather than a wrong clearance. This keeps the core demo path free of
any LLM dependency (floor under flex)."""

import re
from dataclasses import dataclass
from datetime import date

# keyword -> clean jurisdiction token (rule engine does substring matching)
_JURISDICTIONS = {
    "texas": "Texas",
    "tdlr": "Texas",
    "nevada": "Nevada",
    "nsac": "Nevada",
    "vegas": "Nevada",
    "california": "California",
    "csac": "California",
    "new york": "New York",
    "nysac": "New York",
    "maryland": "Maryland",
    "new jersey": "New Jersey",
    "germany": "Germany",
}

_STOPWORDS = {
    "is",
    "are",
    "can",
    "could",
    "should",
    "will",
    "would",
    "does",
    "do",
    "clear",
    "cleared",
    "clearance",
    "check",
    "whether",
    "if",
    "the",
    "a",
    "an",
    "for",
    "on",
    "in",
    "to",
    "compete",
    "competing",
    "fight",
    "fighting",
    "fighter",
    "spar",
    "sparring",
    "bout",
    "card",
    "this",
    "that",
    "weekend",
    "week",
    "today",
    "tonight",
    "tomorrow",
    "saturday",
    "sunday",
    "friday",
    "ready",
    "safe",
    "his",
    "her",
    "show",
    "me",
    "about",
    "any",
    "and",
    "good",
    "go",
    "okay",
    "ok",
    "now",
    "us",
    "we",
}

_DAYS = "monday|tuesday|wednesday|thursday|friday|saturday|sunday"


@dataclass(frozen=True)
class ParsedRequest:
    fighter_query: str
    on_date: date | None
    target_jurisdiction: str | None


def parse_request(text: str, today: date | None = None) -> ParsedRequest:
    raw = text.strip()
    target = _find_jurisdiction(raw)
    on_date = _find_date(raw)

    cleaned = raw.lower()
    # strip an "in/for <jurisdiction>" trailing phrase
    for kw in _JURISDICTIONS:
        cleaned = re.sub(rf"\b(in|for|at)\s+{re.escape(kw)}\b", " ", cleaned)
        cleaned = cleaned.replace(kw, " ")
    cleaned = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", cleaned)
    cleaned = re.sub(rf"\b({_DAYS})('s)?\b", " ", cleaned)
    cleaned = re.sub(r"[^\w\s'.-]", " ", cleaned)

    tokens = [t for t in cleaned.split() if t not in _STOPWORDS and not t.isdigit()]
    # rebuild from the ORIGINAL casing where possible (names look right in the card)
    fighter_query = _restore_casing(raw, tokens)
    return ParsedRequest(fighter_query=fighter_query, on_date=on_date, target_jurisdiction=target)


def _find_jurisdiction(text: str) -> str | None:
    low = text.lower()
    for kw, canon in _JURISDICTIONS.items():
        if re.search(rf"\b{re.escape(kw)}\b", low):
            return canon
    return None


def _find_date(text: str) -> date | None:
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def _restore_casing(raw: str, lowered_tokens: list[str]) -> str:
    wanted = set(lowered_tokens)
    out = [w for w in re.findall(r"[\w'.-]+", raw) if w.lower() in wanted]
    return " ".join(out).strip()
