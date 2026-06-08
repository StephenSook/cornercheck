"""Seed Postgres with real data: ~4,100 UFC fighters (MIT-licensed dataset) plus
15 verified, source-cited suspension cases (see seeds/data/curated_suspensions.json).

Dataset: github.com/KgKevin0/UFC-Stats UFC_fighters.csv, MIT license (verified
2026-06-07). Downloaded at seed time into seeds/data/downloads/ (gitignored),
never committed.

Run: uv run python seeds/seed_db.py [--force]
"""

import csv
import json
import sys
import urllib.request
from pathlib import Path

from cornercheck.db.migrate import apply_migrations
from cornercheck.db.pool import get_pool
from cornercheck.ledger.store import append_entry

DATA_DIR = Path(__file__).parent / "data"
DOWNLOADS = DATA_DIR / "downloads"
CSV_URL = "https://raw.githubusercontent.com/KgKevin0/UFC-Stats/main/UFC_fighters.csv"
CSV_PATH = DOWNLOADS / "UFC_fighters.csv"

# Stage 5 demo scenario mapping (every scenario = a named, really-seeded fighter)
DEMO_CLEAN_FIGHTER = "Merab Dvalishvili"  # CLEAR card
DEMO_CROSS_JX = "Julio Cesar Chavez Jr."  # cross-jurisdiction DO NOT CLEAR
DEMO_AMBIGUOUS = "Bruno Silva"  # two real UFC Bruno Silvas -> disambiguation
DEMO_ACTIVE_SUSPENSION = "Junior dos Santos"  # indefinite, active right now
DEMO_RTS_CHATTER = "Geoff Neal"  # injury-chatter seed messages reference him


def download_dataset() -> Path:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        print(f"downloading {CSV_URL} ...")
        urllib.request.urlretrieve(CSV_URL, CSV_PATH)
    return CSV_PATH


def seed(force: bool) -> None:
    apply_migrations()
    pool = get_pool()

    with pool.connection() as conn:
        count = conn.execute("SELECT count(*) FROM fighters").fetchone()
        assert count is not None
        if count[0] > 0:
            if not force:
                print(f"fighters table already has {count[0]} rows; use --force to reseed")
                return
            conn.execute("DELETE FROM suspensions")
            conn.execute("DELETE FROM fighters")

    path = download_dataset()
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    fighter_rows = [
        (
            f"{r['First Name']} {r['Last Name']}".strip(),
            r.get("Weight Class") or None,
            int(r["W"] or 0),
            int(r["L"] or 0),
            int(r["D"] or 0),
            "mma",
            "ufcstats.com via github.com/KgKevin0/UFC-Stats (MIT)",
        )
        for r in rows
        if f"{r['First Name']} {r['Last Name']}".strip()
    ]

    cases = json.loads((DATA_DIR / "curated_suspensions.json").read_text())["cases"]

    with pool.connection() as conn, conn.transaction():
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO fighters (full_name, weight_class, wins, losses, draws, sport,"
                " source) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                fighter_rows,
            )
        inserted_suspensions = 0
        for c in cases:
            row = conn.execute(
                "SELECT id FROM fighters WHERE lower(full_name) = lower(%s)"
                " ORDER BY created_at LIMIT 1",
                (c["fighter_name"],),
            ).fetchone()
            if row is None:
                row = conn.execute(
                    "INSERT INTO fighters (full_name, sport, source) VALUES (%s, %s, %s)"
                    " RETURNING id",
                    (c["fighter_name"], c["sport"], c["source_url"]),
                ).fetchone()
            assert row is not None
            conn.execute(
                "INSERT INTO suspensions (fighter_id, suspension_type, start_date, end_date,"
                " indefinite, jurisdiction, reason, source_url, source_quote)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    row[0],
                    c["suspension_type"],
                    c["start_date"],
                    c["end_date"],
                    c["indefinite"],
                    c["jurisdiction"],
                    c["reason"],
                    c["source_url"],
                    c["source_quote"],
                ),
            )
            inserted_suspensions += 1

    verify_demo_mapping()

    append_entry(
        "seed",
        "db_seeded",
        {"fighters": len(fighter_rows), "suspensions": inserted_suspensions, "source": CSV_URL},
    )
    print(f"seeded {len(fighter_rows)} fighters + {inserted_suspensions} cited suspensions")


def verify_demo_mapping() -> None:
    """Every Stage 5 demo scenario must map to a named, really-seeded fighter."""
    checks = {
        "CLEAR demo": DEMO_CLEAN_FIGHTER,
        "cross-jurisdiction demo": DEMO_CROSS_JX,
        "active-suspension demo": DEMO_ACTIVE_SUSPENSION,
        "RTS-chatter demo": DEMO_RTS_CHATTER,
    }
    with get_pool().connection() as conn:
        for label, name in checks.items():
            row = conn.execute(
                "SELECT count(*) FROM fighters WHERE lower(full_name) = lower(%s)", (name,)
            ).fetchone()
            assert row is not None and row[0] >= 1, f"{label}: {name} missing from seed"
            print(f"  {label}: {name} present ({row[0]} row(s))")
        amb = conn.execute(
            "SELECT count(*) FROM fighters WHERE lower(full_name) = lower(%s)",
            (DEMO_AMBIGUOUS,),
        ).fetchone()
        assert amb is not None and amb[0] >= 2, (
            f"disambiguation demo needs >=2 fighters named {DEMO_AMBIGUOUS}, found {amb}"
        )
        print(f"  disambiguation demo: {DEMO_AMBIGUOUS} present x{amb[0]}")
        sus = conn.execute("SELECT count(*) FROM suspensions").fetchone()
        assert sus is not None and sus[0] >= 10, f"need >=10 suspensions, found {sus}"
        print(f"  suspensions seeded: {sus[0]} (>=10 required)")


if __name__ == "__main__":
    seed(force="--force" in sys.argv)
