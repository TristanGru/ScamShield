-- migrate.sql — Railway Postgres schema for ScamShield
-- Run once against the Railway Postgres instance.
-- Pi SQLite schema is created automatically by db.init_db().

CREATE TABLE IF NOT EXISTS events (
    id            TEXT        PRIMARY KEY,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trigger_type  TEXT        NOT NULL CHECK (trigger_type IN ('auto', 'manual')),
    scam_score    INTEGER     CHECK (scam_score >= 0 AND scam_score <= 100),
    keywords      TEXT        NOT NULL DEFAULT '[]',  -- JSON array
    transcript    TEXT        NOT NULL DEFAULT '',
    sms_sent      BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_events_created_at   ON events (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_trigger_type ON events (trigger_type);

-- Config table: stores ngrok URL, startup time, etc.
CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
