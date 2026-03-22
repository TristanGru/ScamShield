"""
sync.py — Background worker that syncs unsynced SQLite events to Postgres.

Runs every 60 seconds in a daemon thread.
SQLite is always the source of truth; Postgres is the cloud mirror for the dashboard.
If Postgres is unreachable, events accumulate locally and are retried next cycle (BL-010).
"""

import logging
import threading
import time
from typing import Optional

import psycopg
import schedule

from config import POSTGRES_URL
from db import get_unsynced_events, mark_synced

logger = logging.getLogger(__name__)

_alerts_fired = 0
_sms_sent_count = 0
_sync_lag = 0


def _get_postgres_connection() -> Optional[psycopg.Connection]:
    if not POSTGRES_URL:
        logger.debug("POSTGRES_URL not set — skipping sync")
        return None
    try:
        conn = psycopg.connect(POSTGRES_URL, connect_timeout=5)
        return conn
    except Exception as exc:
        logger.warning("Postgres connection failed: %s", exc)
        return None


def _upsert_events(conn: psycopg.Connection, events: list[dict]) -> list[str]:
    """Upsert events to Postgres. Returns list of successfully synced IDs."""
    if not events:
        return []

    synced_ids = []
    with conn.cursor() as cur:
        for event in events:
            try:
                import json
                cur.execute(
                    """
                    INSERT INTO events (id, created_at, trigger_type, scam_score, keywords, transcript, sms_sent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        event["id"],
                        event["created_at"],
                        event["trigger_type"],
                        event["scam_score"],
                        json.dumps(event["keywords"]),
                        event["transcript"],
                        bool(event["sms_sent"]),
                    ),
                )
                synced_ids.append(event["id"])
            except Exception as exc:
                logger.error("Failed to upsert event %s: %s", event["id"], exc)
                conn.rollback()

    conn.commit()
    return synced_ids


def sync_once() -> None:
    """Run one sync cycle: fetch unsynced → upsert to Postgres → mark synced."""
    global _sync_lag
    unsynced = get_unsynced_events()
    _sync_lag = len(unsynced)

    if not unsynced:
        logger.debug("Sync: nothing to sync")
        return

    logger.info("Sync: %d unsynced events", len(unsynced))

    conn = _get_postgres_connection()
    if conn is None:
        logger.warning("Sync: Postgres unavailable — will retry next cycle (EC-010)")
        if _sync_lag > 50:
            logger.warning("SYNC_LAG_HIGH: %d unsynced events — check Postgres", _sync_lag)
        return

    try:
        synced_ids = _upsert_events(conn, unsynced)
        if synced_ids:
            mark_synced(synced_ids)
            logger.info("Sync: %d events synced to Postgres", len(synced_ids))
        _sync_lag = len(unsynced) - len(synced_ids)
    finally:
        conn.close()


def sync_loop() -> None:
    """Schedule sync_once every 60 seconds and run forever."""
    schedule.every(60).seconds.do(sync_once)
    logger.info("Sync worker started — running every 60s")
    # Run once immediately at startup
    sync_once()
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_sync_worker() -> threading.Thread:
    """Start the sync loop in a background daemon thread."""
    thread = threading.Thread(target=sync_loop, daemon=True, name="sync-worker")
    thread.start()
    return thread


def get_metrics() -> dict:
    return {
        "sync_lag_events": _sync_lag,
        "alerts_fired": _alerts_fired,
        "sms_sent": _sms_sent_count,
    }
