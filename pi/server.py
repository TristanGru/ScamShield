"""
server.py — FastAPI REST server running on the Pi.

Endpoints:
  GET  /events   — paginated event list
  POST /events   — create event (for testing; pipeline writes directly via db.py)
  GET  /status   — system status
  GET  /health   — liveness check
  GET  /metrics  — Prometheus-format counters

LAN-only in production (accessed server-side by Next.js via ngrok).
No auth required — ngrok URL is kept server-side only (§16).
"""

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import db
import detection
import sync as sync_module
from config import WARNING_AUDIO_PATH

app = FastAPI(title="ScamShield Pi API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restricted to server-side Next.js calls in production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_start_time = time.time()
_listening = False
_nest_connected = False


# ── Models ────────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    trigger_type: str = Field(..., pattern="^(auto|manual)$")
    scam_score: Optional[int] = Field(None, ge=0, le=100)
    keywords: list[str] = Field(default_factory=list)
    transcript: str = ""


class EventResponse(BaseModel):
    id: str
    created_at: str
    trigger_type: str
    scam_score: Optional[int]
    keywords: list[str]
    transcript: str
    sms_sent: int
    synced: int


class EventsListResponse(BaseModel):
    events: list[EventResponse]
    total: int


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"ok": True}


@app.get("/warning.mp3")
def serve_warning_audio():
    """Serve the cached ElevenLabs warning MP3 to Chromecast/Nest devices."""
    if not os.path.exists(WARNING_AUDIO_PATH):
        raise HTTPException(status_code=404, detail="warning.mp3 not yet generated")
    return FileResponse(WARNING_AUDIO_PATH, media_type="audio/mpeg")


@app.get("/status")
def status():
    last_events = db.get_events(limit=1)
    last_event_at = last_events[0]["created_at"] if last_events else None
    return {
        "nest_connected": _nest_connected,
        "listening": _listening,
        "uptime_seconds": int(time.time() - _start_time),
        "last_event_at": last_event_at,
    }


@app.get("/events", response_model=EventsListResponse)
def get_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    trigger_type: Optional[str] = Query(default=None, pattern="^(auto|manual)$"),
):
    events = db.get_events(limit=limit, offset=offset, trigger_type=trigger_type)
    total = db.count_events(trigger_type=trigger_type)
    return {"events": events, "total": total}


@app.post("/events", status_code=201)
def create_event(payload: EventCreate):
    event_id = db.write_event(
        trigger_type=payload.trigger_type,
        scam_score=payload.scam_score,
        keywords=payload.keywords,
        transcript=payload.transcript,
        sms_sent=False,
    )
    events = db.get_events(limit=1, offset=0)
    if not events:
        raise HTTPException(status_code=500, detail="Event write failed")
    return events[0]


@app.get("/metrics")
def metrics():
    """Prometheus text-format metrics."""
    det = detection.get_metrics()
    syn = sync_module.get_metrics()
    total = db.count_events()

    lines = [
        f"# TYPE chunks_processed counter",
        f"chunks_processed {det['chunks_processed']}",
        f"# TYPE gemini_errors counter",
        f"gemini_errors {det['gemini_errors']}",
        f"# TYPE alerts_fired counter",
        f"alerts_fired {syn['alerts_fired']}",
        f"# TYPE sms_sent counter",
        f"sms_sent {syn['sms_sent']}",
        f"# TYPE sync_lag_events gauge",
        f"sync_lag_events {syn['sync_lag_events']}",
        f"# TYPE total_events counter",
        f"total_events {total}",
    ]
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(lines) + "\n")


# ── State setters (called by main.py) ─────────────────────────────────────────

def set_listening(value: bool) -> None:
    global _listening
    _listening = value


def set_nest_connected(value: bool) -> None:
    global _nest_connected
    _nest_connected = value
