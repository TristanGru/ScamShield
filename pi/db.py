"""
db.py — SQLite helpers for ScamShield local persistence.
SQLite is source of truth on the Pi. Postgres is a cloud mirror for the dashboard.

Usage:
    python db.py --init        # create DB and tables
    python db.py --seed        # insert 3 sample events (dev only)
"""

import sqlite3
import uuid
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import SQLITE_DB_PATH

logger = logging.getLogger(__name__)


def _get_connection() -> sqlite3.Connection:
    Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with _get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id           TEXT PRIMARY KEY,
                created_at   TEXT NOT NULL,
                trigger_type TEXT NOT NULL CHECK(trigger_type IN ('auto', 'manual')),
                scam_score   INTEGER,
                keywords     TEXT,
                transcript   TEXT,
                sms_sent     INTEGER NOT NULL DEFAULT 0,
                synced       INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_events_synced ON events(synced);
        """)
    logger.info("DB initialized at %s", SQLITE_DB_PATH)


def write_event(
    trigger_type: str,
    scam_score: Optional[int],
    keywords: list[str],
    transcript: str,
    sms_sent: bool = False,
) -> str:
    """Insert a new scam event. Returns the new event ID."""
    event_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO events (id, created_at, trigger_type, scam_score, keywords, transcript, sms_sent, synced)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                event_id,
                created_at,
                trigger_type,
                scam_score,
                json.dumps(keywords),
                transcript,
                1 if sms_sent else 0,
            ),
        )

    logger.info(
        "Event written",
        extra={
            "event_id": event_id,
            "trigger_type": trigger_type,
            "scam_score": scam_score,
            "keywords": keywords,
        },
    )
    return event_id


def get_events(limit: int = 50, offset: int = 0, trigger_type: Optional[str] = None) -> list[dict]:
    """Fetch paginated events, newest first."""
    with _get_connection() as conn:
        if trigger_type:
            rows = conn.execute(
                "SELECT * FROM events WHERE trigger_type = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (trigger_type, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()

    events = []
    for row in rows:
        e = dict(row)
        e["keywords"] = json.loads(e["keywords"]) if e["keywords"] else []
        events.append(e)
    return events


def count_events(trigger_type: Optional[str] = None) -> int:
    with _get_connection() as conn:
        if trigger_type:
            return conn.execute(
                "SELECT COUNT(*) FROM events WHERE trigger_type = ?", (trigger_type,)
            ).fetchone()[0]
        return conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]


def get_unsynced_events() -> list[dict]:
    """Return all events not yet synced to Postgres."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM events WHERE synced = 0 ORDER BY created_at ASC"
        ).fetchall()
    events = []
    for row in rows:
        e = dict(row)
        e["keywords"] = json.loads(e["keywords"]) if e["keywords"] else []
        events.append(e)
    return events


def delete_event(event_id: str) -> bool:
    """Delete an event by ID. Returns True if a row was deleted."""
    with _get_connection() as conn:
        cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    deleted = cursor.rowcount > 0
    if deleted:
        logger.info("Event deleted: %s", event_id)
    return deleted


def mark_synced(event_ids: list[str]) -> None:
    """Mark events as synced to Postgres."""
    if not event_ids:
        return
    placeholders = ",".join("?" * len(event_ids))
    with _get_connection() as conn:
        conn.execute(
            f"UPDATE events SET synced = 1 WHERE id IN ({placeholders})", event_ids
        )


def set_config(key: str, value: str) -> None:
    with _get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value)
        )


def get_config(key: str) -> Optional[str]:
    with _get_connection() as conn:
        row = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def _seed_dev_data() -> None:
    """Insert 3 sample events for dashboard UI testing."""
    samples = [
        {
            "trigger_type": "auto",
            "scam_score": 87,
            "keywords": ["IRS", "gift cards", "don't tell anyone"],
            "transcript": "This is the IRS. You owe $5,000 in back taxes and must pay immediately with gift cards. Don't tell anyone about this call.",
            "sms_sent": True,
        },
        {
            "trigger_type": "manual",
            "scam_score": None,
            "keywords": [],
            "transcript": "Something felt wrong about this call.",
            "sms_sent": True,
        },
        {
            "trigger_type": "auto",
            "scam_score": 78,
            "keywords": ["social security", "warrant", "arrest"],
            "transcript": "Your social security number has been suspended due to suspicious activity. There is a warrant out for your arrest.",
            "sms_sent": True,
        },
    ]
    for s in samples:
        write_event(**s)
    print(f"Seeded {len(samples)} sample events into {SQLITE_DB_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ScamShield DB utility")
    parser.add_argument("--init", action="store_true", help="Initialize DB schema")
    parser.add_argument("--seed", action="store_true", help="Seed dev sample data")
    args = parser.parse_args()

    if args.init:
        init_db()
        print(f"DB initialized at {SQLITE_DB_PATH}")
    if args.seed:
        init_db()
        _seed_dev_data()
