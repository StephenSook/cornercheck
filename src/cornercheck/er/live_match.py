"""High-recall live retrieval: pg_trgm candidates re-scored with Jaro-Winkler.

Retrieve is deliberately loose (never miss a true match); the banding layer in
thresholds.py decides confirm/disambiguate/refuse.
"""

import jellyfish

from cornercheck.db.pool import get_pool
from cornercheck.er.thresholds import Candidate, ResolutionResult, band

_RETRIEVE_SQL = """
SELECT id, full_name, weight_class, wins, losses, draws, sport, primary_jurisdiction
FROM fighters
WHERE full_name %% %(q)s
   OR full_name ILIKE '%%' || %(q)s || '%%'
   OR lower(full_name) = lower(%(q)s)
LIMIT 25
"""


def _score(query: str, name: str) -> float:
    q, n = " ".join(query.lower().split()), " ".join(name.lower().split())
    if q == n:
        return 1.0
    return float(jellyfish.jaro_winkler_similarity(q, n))


def retrieve_candidates(query: str) -> list[Candidate]:
    with get_pool().connection() as conn:
        rows = conn.execute(_RETRIEVE_SQL, {"q": query}).fetchall()
    return [
        Candidate(
            fighter_id=str(r[0]),
            full_name=r[1],
            weight_class=r[2],
            record=f"{r[3]}-{r[4]}-{r[5]}",
            sport=r[6],
            jurisdiction=r[7],
            score=_score(query, r[1]),
        )
        for r in rows
    ]


def resolve(query: str) -> ResolutionResult:
    """Retrieve -> band. The caller (agent brain) must honor AMBIGUOUS/NOT_FOUND."""
    return band(retrieve_candidates(query))
