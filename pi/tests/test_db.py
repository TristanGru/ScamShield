"""
test_db.py — Unit tests for SQLite persistence layer.
Uses a temp DB file so tests never touch the real database.
"""

import json
import os
import tempfile
import pytest


@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    """Redirect SQLITE_DB_PATH to a temp file for every test."""
    db_path = str(tmp_path / "test_scamshield.db")
    monkeypatch.setenv("SQLITE_DB_PATH", db_path)
    # Re-import config after env patch so the path is picked up
    import importlib
    import pi.config as cfg
    cfg.SQLITE_DB_PATH = db_path
    import pi.db as db_module
    db_module.SQLITE_DB_PATH = db_path
    db_module.init_db()
    return db_module


def test_init_creates_tables(temp_db):
    db = temp_db
    events = db.get_events()
    assert isinstance(events, list)
    assert len(events) == 0


def test_write_and_read_auto_event(temp_db):
    db = temp_db
    event_id = db.write_event(
        trigger_type="auto",
        scam_score=87,
        keywords=["IRS", "gift cards"],
        transcript="This is the IRS. Pay with gift cards.",
        sms_sent=True,
    )
    assert event_id is not None

    events = db.get_events()
    assert len(events) == 1
    e = events[0]
    assert e["id"] == event_id
    assert e["trigger_type"] == "auto"
    assert e["scam_score"] == 87
    assert "IRS" in e["keywords"]
    assert "gift cards" in e["keywords"]
    assert e["sms_sent"] == 1
    assert e["synced"] == 0


def test_write_manual_event_null_score(temp_db):
    db = temp_db
    event_id = db.write_event(
        trigger_type="manual",
        scam_score=None,
        keywords=[],
        transcript="Something felt wrong.",
        sms_sent=True,
    )
    events = db.get_events()
    assert len(events) == 1
    assert events[0]["scam_score"] is None
    assert events[0]["trigger_type"] == "manual"
    assert events[0]["keywords"] == []


def test_count_events(temp_db):
    db = temp_db
    assert db.count_events() == 0
    db.write_event("auto", 75, ["IRS"], "transcript", True)
    db.write_event("manual", None, [], "manual transcript", True)
    assert db.count_events() == 2
    assert db.count_events(trigger_type="auto") == 1
    assert db.count_events(trigger_type="manual") == 1


def test_get_unsynced_events(temp_db):
    db = temp_db
    id1 = db.write_event("auto", 80, ["IRS"], "t1", True)
    id2 = db.write_event("auto", 85, ["lottery"], "t2", True)

    unsynced = db.get_unsynced_events()
    assert len(unsynced) == 2

    db.mark_synced([id1])
    unsynced = db.get_unsynced_events()
    assert len(unsynced) == 1
    assert unsynced[0]["id"] == id2


def test_mark_synced_empty_list(temp_db):
    db = temp_db
    db.write_event("auto", 80, ["IRS"], "t1", True)
    db.mark_synced([])  # should not raise
    assert len(db.get_unsynced_events()) == 1


def test_config_set_and_get(temp_db):
    db = temp_db
    db.set_config("ngrok_url", "https://abc123.ngrok-free.app")
    val = db.get_config("ngrok_url")
    assert val == "https://abc123.ngrok-free.app"


def test_config_get_missing_key(temp_db):
    db = temp_db
    val = db.get_config("nonexistent_key")
    assert val is None


def test_pagination(temp_db):
    db = temp_db
    for i in range(5):
        db.write_event("auto", 70 + i, ["IRS"], f"transcript {i}", True)

    page1 = db.get_events(limit=3, offset=0)
    page2 = db.get_events(limit=3, offset=3)
    assert len(page1) == 3
    assert len(page2) == 2
    # newest first
    assert page1[0]["scam_score"] > page1[2]["scam_score"]


def test_trigger_type_filter(temp_db):
    db = temp_db
    db.write_event("auto", 80, ["IRS"], "auto transcript", True)
    db.write_event("manual", None, [], "manual transcript", False)

    auto_events = db.get_events(trigger_type="auto")
    manual_events = db.get_events(trigger_type="manual")
    assert len(auto_events) == 1
    assert len(manual_events) == 1
    assert auto_events[0]["trigger_type"] == "auto"
    assert manual_events[0]["trigger_type"] == "manual"
