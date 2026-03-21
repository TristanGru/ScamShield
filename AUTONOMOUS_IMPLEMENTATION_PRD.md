# AUTONOMOUS_IMPLEMENTATION_PRD.md

---

## 1. Title and One-Liner

**ScamShield** — A Raspberry Pi-powered device that listens to phone calls on speakerphone, detects scam patterns in real time using the Gemini API, alerts the caller via Google Nest TTS (ElevenLabs voice), sends an SMS to a family member via Twilio, and logs all events to a family-facing web dashboard secured by Auth0.

---

## 2. Executive Summary

- ScamShield protects elderly individuals from phone scams with zero required behavioral change — they simply put calls on speakerphone near the device.
- A Raspberry Pi 4B captures audio via a Logitech webcam mic and routes it through Whisper (local STT) for real-time transcription.
- Transcribed text is evaluated by the Gemini API for scam likelihood; a keyword fallback ensures detection even without API access.
- When a scam is detected (auto or manual button press), the Google Nest speaks a warning via ElevenLabs-generated audio, the Grove LED turns red, and the Grove Buzzer fires.
- Twilio sends an SMS alert to a pre-registered family member with flagged phrases and timestamp.
- A SenseCAP Indicator displays live transcription and detection status locally.
- A web dashboard (Next.js + Auth0) allows family members to view call logs, flagged events, and manage settings remotely.
- The project targets: Best Accessibility & Empowerment, Gemini API, ElevenLabs, Auth0, and GoDaddy Domain prize tracks.

---

## 3. Goals

- G1: Detect a scam call within 10 seconds of a triggering phrase being spoken.
- G2: Alert the elderly user via Google Nest audio within 3 seconds of detection.
- G3: Deliver Twilio SMS to family member within 5 seconds of detection trigger.
- G4: Log 100% of detected events with timestamps, flagged phrases, and full transcript to persistent storage.
- G5: Web dashboard loads and authenticates family member in under 3 seconds.
- G6: Manual Grove Button press triggers the same alert pipeline as auto-detection.
- G7: System operates fully offline for audio capture and keyword detection if cloud APIs are unavailable.

---

## 4. Non-Goals

- NG1: ScamShield does not intercept or block calls — it is advisory only.
- NG2: No mobile app — family interaction is web dashboard only.
- NG3: No support for non-speakerphone audio (earpiece, headset).
- NG4: No multi-language support at launch — English only.
- NG5: No integration with phone carriers or call metadata (caller ID lookup).
- NG6: No video recording or image capture.
- NG7: No cloud storage of raw audio — transcripts only.
- NG8: No admin panel for managing multiple households — single household per deployment.

---

## 5. Assumptions & Decisions

### 5.1 Assumptions (A-###)

- **A-001**: Phone calls are taken on speakerphone, placed within 1 meter of the Logitech webcam mic on the Pi.
- **A-002**: The Raspberry Pi 4B has internet connectivity via WiFi or Ethernet at the deployment location.
- **A-003**: The Google Nest and Raspberry Pi are on the same local network.
- **A-004**: ElevenLabs pre-generates the warning audio file at startup; the Pi caches it locally and plays it via `pychromecast` to the Nest.
- **A-005**: A single family member phone number is pre-registered in `.env`; no self-service registration UI needed for the hackathon.
- **A-006**: The Grove Sound Sensor is used as a voice activity detector (VAD) — transcription only begins when volume exceeds threshold, saving compute.
- **A-007**: The SenseCAP Indicator connects to the Pi via USB serial and displays data via a lightweight serial protocol.
- **A-008**: Whisper `tiny.en` model is used for STT — fast enough on Pi 4B, English-only, runs locally.
- **A-009**: The web dashboard is hosted on Vercel (free tier); the Pi backend server is accessible via a reverse tunnel (ngrok free tier) for the hackathon demo.
- **A-010**: Auth0 free tier (up to 7,000 MAU) is sufficient. Family member registers with email/password or Google OAuth.
- **A-011**: SQLite is used for local persistence on the Pi; the server syncs events to a lightweight Postgres instance on Railway (free tier).
- **A-012**: The 3D-printed phone stand is a physical prop — not software-implemented. No code needed.

### 5.2 Decisions (D-###)

- **D-001**: **Python on Pi** — EE-friendly, best library support for GPIO (Grove HAT), audio, and `pychromecast`. All Pi-side code is Python 3.11.
- **D-002**: **Next.js 14 (App Router) for dashboard** — Tristan's TypeScript comfort zone, fast to scaffold, Vercel deployment is trivial.
- **D-003**: **Gemini 1.5 Flash** — Fastest and cheapest Gemini model; sufficient for short transcript segments. Falls back to keyword list if API call fails.
- **D-004**: **ElevenLabs pre-generation** — Warning audio is generated once at Pi startup and cached as `warning.mp3`. Avoids latency during live detection.
- **D-005**: **pychromecast for Nest output** — Only Google-sanctioned way to push audio to Nest from a local device without needing Google Assistant SDK.
- **D-006**: **Twilio SMS over email** — SMS is more likely to be seen immediately by a family member during an active scam call.
- **D-007**: **SQLite on Pi + Postgres on Railway** — Pi stores events locally (resilient to internet outages); background sync pushes to cloud for dashboard access.
- **D-008**: **Whisper tiny.en** — Runs in ~real-time on Pi 4B, 75MB model, English-only. Acceptable WER for scam phrase detection.
- **D-009**: **Grove Base HAT** — Required adapter to use Grove components (LED, Buzzer, Button, Sound Sensor) with Pi GPIO. Must be sourced.
- **D-010**: **Auth0 for dashboard auth** — Satisfies MLH prize track, production-grade, free tier sufficient, easy Next.js SDK integration.

### 5.3 Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Pi mic doesn't pick up speakerphone clearly | High | High | Test mic placement at setup; fallback to Grove Sound Sensor level detection |
| Whisper too slow on Pi 4B for real-time | Medium | High | Use `tiny.en`, process in 3-second chunks, use VAD to skip silence |
| pychromecast can't find Google Nest on network | Medium | High | Pre-test network discovery; fallback to Grove Buzzer + LED only |
| Gemini API rate limit or quota exceeded | Low | Medium | Keyword fallback list handles detection without API |
| ElevenLabs API down at hackathon | Low | Medium | Pre-cache warning.mp3 at startup; Nest uses cached file |
| Grove Base HAT not available at hackathon | Medium | Medium | Wire Grove components directly to GPIO pins with jumper cables |
| ngrok tunnel drops during demo | Medium | High | Keep Pi dashboard backup running on local network; demo on LAN if needed |
| SenseCAP serial communication unstable | Low | Low | SenseCAP is enhancement only; system works without it |

---

## 6. Users, Personas, and Core Use Cases

### Personas

**Eleanor (Elderly User, 72)**
- Not tech-savvy. Uses a landline or basic smartphone.
- Will not install apps or change habits.
- Needs zero interaction with the device beyond putting calls on speaker.

**David (Family Member, 45)**
- Eleanor's son. Occasionally tech-savvy.
- Monitors the dashboard from his phone or laptop.
- Wants to know immediately if his mom is being targeted.

**Scammer (Adversary)**
- Uses IRS, Medicare, Social Security, gift card, or prize scams.
- Speaks in English. Uses urgency and secrecy tactics.

### Primary Flows (U-###)

**U-001: Auto Scam Detection**
1. Eleanor receives a call, puts it on speakerphone near the Pi.
2. Grove Sound Sensor detects voice activity; Pi begins transcription.
3. Whisper transcribes audio in 3-second chunks.
4. Each chunk is sent to Gemini API + keyword checker.
5. Score exceeds threshold → alert pipeline fires.
6. Google Nest says warning aloud. Grove LED turns red. Grove Buzzer sounds.
7. Twilio SMS sent to David with timestamp and flagged phrases.
8. Event logged to SQLite and synced to Postgres.
9. SenseCAP displays "SCAM DETECTED" in red.

**U-002: Manual Flag**
1. Eleanor feels something is wrong, presses the Grove Button.
2. Alert pipeline fires immediately, same as U-001 step 6–9.
3. SMS to David notes "Manually flagged by user."

**U-003: Family Dashboard Review**
1. David receives SMS alert.
2. Opens scamshield.app (GoDaddy domain).
3. Logs in via Auth0 (Google or email).
4. Sees event log: time, flagged phrases, full transcript, trigger type.
5. Calls Eleanor to check in.

**U-004: System Startup**
1. Pi boots, runs `startup.sh`.
2. Connects to WiFi, starts ngrok tunnel.
3. Pre-generates ElevenLabs warning audio.
4. Discovers Google Nest on local network via pychromecast.
5. Starts audio capture loop.
6. SenseCAP shows "ScamShield Ready" in green.

---

## 7. Requirements

### 7.1 Functional Requirements (FR-###)

| ID | Priority | Requirement |
|----|----------|-------------|
| FR-001 | P0 | System continuously captures audio from Logitech webcam mic when Grove Sound Sensor detects volume above threshold. |
| FR-002 | P0 | System transcribes audio in 3-second chunks using Whisper tiny.en locally on the Pi. |
| FR-003 | P0 | Each transcript chunk is evaluated by Gemini 1.5 Flash API for scam likelihood, returning a score 0–100. |
| FR-004 | P0 | A keyword fallback checker runs on every chunk regardless of Gemini availability, scanning for a predefined list of scam phrases. |
| FR-005 | P0 | When scam score exceeds threshold (≥70) OR ≥2 keywords match, alert pipeline fires. |
| FR-006 | P0 | Alert pipeline: plays ElevenLabs-generated warning audio on Google Nest via pychromecast. |
| FR-007 | P0 | Alert pipeline: turns Grove LED red. |
| FR-008 | P0 | Alert pipeline: activates Grove Buzzer for 2 seconds. |
| FR-009 | P0 | Alert pipeline: sends Twilio SMS to family number with timestamp, trigger type, and flagged phrases. |
| FR-010 | P0 | Alert pipeline: writes event record to local SQLite database. |
| FR-011 | P0 | Grove Button press triggers alert pipeline with trigger_type = "manual". |
| FR-012 | P1 | Background process syncs SQLite events to Postgres on Railway every 60 seconds. |
| FR-013 | P1 | Web dashboard displays paginated list of all events with timestamp, trigger type, flagged phrases, and transcript. |
| FR-014 | P1 | Web dashboard is protected by Auth0 — unauthenticated users are redirected to login. |
| FR-015 | P1 | SenseCAP Indicator displays live transcription text and status (Ready / Listening / SCAM DETECTED). |
| FR-016 | P1 | ElevenLabs warning audio is generated and cached to `warning.mp3` on Pi startup. |
| FR-017 | P1 | System recovers automatically if Gemini API call fails — keyword fallback is used and error is logged. |
| FR-018 | P2 | Dashboard shows a count of total alerts and most recent alert at top of page. |
| FR-019 | P2 | Dashboard allows family member to view full transcript of any event. |
| FR-020 | P2 | Grove LED returns to green (idle) 10 seconds after alert fires, unless another detection occurs. |

### 7.2 Non-Functional Requirements (NFR-###)

| ID | Requirement |
|----|-------------|
| NFR-001 | End-to-end latency from triggering phrase spoken to Nest audio playing: ≤10 seconds under normal WiFi conditions. |
| NFR-002 | Pi process must not crash on Gemini API timeout; timeout is set to 5 seconds with keyword fallback. |
| NFR-003 | SQLite on Pi must handle 1,000+ event records without degradation. |
| NFR-004 | Dashboard must load initial event list in under 3 seconds on a standard mobile connection. |
| NFR-005 | All API keys stored in `.env` files, never committed to git. |
| NFR-006 | Dashboard is mobile-responsive — readable on a 390px wide screen. |
| NFR-007 | System must continue detecting and alerting if Postgres sync fails — local SQLite is source of truth. |
| NFR-008 | Audio is never stored to disk — only transcripts are persisted. |

### 7.3 Out of Scope Requirements

- Caller ID lookup or phone number metadata
- Multi-user / multi-household support
- Native mobile app
- Audio recording or playback
- Non-English language detection
- Admin interface

---

## 8. Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Scam detection rate (demo) | 100% of scripted scam phrases detected | Run 5 scripted test calls during demo |
| False positive rate | <1 false alert per 10 minutes of normal speech | Run 10-minute normal conversation test |
| Alert latency | ≤10 seconds end-to-end | Stopwatch from phrase spoken to Nest audio |
| SMS delivery | <5 seconds after detection | Twilio delivery log timestamp |
| Dashboard load time | <3 seconds | Browser DevTools network tab |
| Uptime during 24hr hackathon | 100% — no crashes | Manual monitoring |

---

## 9. System Architecture

### 9.1 High-Level Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PHYSICAL LAYER (Pi 4B)                      │
│                                                                 │
│  [Phone on Speaker] ──audio──► [Logitech Webcam Mic]           │
│                                        │                        │
│  [Grove Sound Sensor] ──VAD──► [Audio Capture Loop]            │
│                                        │                        │
│                              [Whisper tiny.en STT]              │
│                                        │                        │
│                              [Detection Engine]                 │
│                             /          │         \              │
│               [Gemini API]   [Keyword List]  [Grove Button]     │
│                             \          │         /              │
│                              [Alert Pipeline]                   │
│                    /          /        │        \               │
│         [pychromecast]  [Grove LED] [Buzzer]  [Twilio SMS]      │
│               │                        │                        │
│        [Google Nest]           [SQLite DB]                      │
│        (speaks warning)               │                         │
│                              [SenseCAP Display]                 │
└───────────────────────────────────────┼─────────────────────────┘
                                        │ sync every 60s
                                        ▼
                              ┌─────────────────┐
                              │  Postgres (Railway) │
                              └────────┬────────┘
                                       │ REST API
                                       ▼
                              ┌─────────────────┐
                              │  Next.js Dashboard │
                              │  (Vercel)          │
                              │  Auth0 protected    │
                              └─────────────────┘
                                       ▲
                              [Family Member Browser]
```

### 9.2 Component Responsibilities

| Component | Purpose | Inputs | Outputs | Dependencies |
|-----------|---------|--------|---------|--------------|
| Audio Capture Loop (`audio_capture.py`) | Reads mic, chunks audio when VAD fires | Grove Sound Sensor level, Webcam mic stream | 3-second WAV chunks | PyAudio, Grove HAT |
| STT Engine (`stt.py`) | Transcribes WAV chunks | WAV chunks | Text strings | openai-whisper |
| Detection Engine (`detection.py`) | Scores transcript for scam likelihood | Text string | Score 0–100, matched keywords | Gemini API, keyword list |
| Alert Pipeline (`alert.py`) | Executes all alert actions | Score + keywords + trigger_type | Nest audio, LED, Buzzer, SMS, DB write | pychromecast, RPi.GPIO, Twilio, SQLite |
| Sync Worker (`sync.py`) | Background sync of SQLite to Postgres | SQLite events table | Postgres rows | psycopg2, schedule |
| SenseCAP Serial (`sensecap.py`) | Sends display commands over USB serial | Status string, transcript text | Serial bytes to SenseCAP | pyserial |
| API Server (`server.py`) | Exposes REST endpoints for dashboard | HTTP requests | JSON responses | FastAPI, SQLite/Postgres |
| Next.js Dashboard | Family-facing web UI | Auth0 session, API responses | HTML/CSS rendered events | Next.js, Auth0, Tailwind |

### 9.3 Runtime Model

**Pi startup sequence:**
1. `startup.sh` → sets env vars, activates venv
2. Generate ElevenLabs warning audio → `warning.mp3`
3. Start ngrok tunnel → capture public URL → write to Postgres `config` table
4. Discover Google Nest via pychromecast → store Nest IP
5. Launch FastAPI server (port 8000) as background process
6. Launch sync worker as background thread
7. Start audio capture loop (main thread)
8. Grove Button interrupt registered on GPIO pin

**Audio processing loop (runs continuously):**
- Poll Grove Sound Sensor every 100ms
- If level > VAD_THRESHOLD: accumulate 3 seconds of audio → write to temp WAV
- Pass WAV to Whisper → get transcript string
- Pass transcript to Detection Engine (Gemini + keyword)
- If score ≥ 70 or keywords ≥ 2 → fire Alert Pipeline
- Clear temp WAV buffer, resume listening

**Alert Pipeline (triggered on detection or button press):**
- Concurrent execution of: Nest TTS, LED set red, Buzzer 2s, Twilio SMS
- Write event to SQLite
- Send transcript + status to SenseCAP
- After 10s: LED set green

### 9.4 Error Handling Strategy

| Error | Handling |
|-------|---------|
| Gemini API timeout/error | Log error, use keyword-only score, continue |
| pychromecast Nest not found | Log warning, skip Nest, continue with LED/Buzzer/SMS |
| Twilio SMS failure | Log error with full event, retry once after 5s |
| Whisper OOM / crash | Restart audio capture loop, log crash |
| Postgres sync failure | Log failure, keep SQLite as truth, retry next cycle |
| ElevenLabs generation failure | Log error, use Nest's built-in TTS as fallback via cast |
| Grove HAT GPIO error | Log and skip GPIO actions, continue software pipeline |

---

## 10. Tech Stack

### 10.1 Selected Stack

| Layer | Choice |
|-------|--------|
| Pi OS | Raspberry Pi OS Lite (64-bit, Bookworm) |
| Pi Language | Python 3.11 |
| STT | openai-whisper (tiny.en, local) |
| LLM / Scam Detection | Google Gemini 1.5 Flash API |
| Voice Alert | ElevenLabs API (pre-generated MP3) |
| Smart Speaker | Google Nest via pychromecast |
| SMS | Twilio Python SDK |
| GPIO / Grove | RPi.GPIO + Grove Base HAT Python library |
| Serial (SenseCAP) | pyserial |
| Pi API Server | FastAPI + uvicorn |
| Local DB | SQLite (aiosqlite) |
| Cloud DB | Postgres on Railway |
| Dashboard Framework | Next.js 14 (App Router, TypeScript) |
| Dashboard Auth | Auth0 (next-auth v5 + Auth0 provider) |
| Dashboard Styling | Tailwind CSS |
| Dashboard Hosting | Vercel |
| Domain | GoDaddy (scamshield.app or similar .app domain) |
| Tunnel (hackathon) | ngrok free tier |
| Package management (Pi) | pip + venv |
| Package management (Dashboard) | npm |

### 10.2 Why This Stack

- **Python on Pi**: Grove HAT SDK, pychromecast, RPi.GPIO, and Whisper are all Python-native. EE teammate is comfortable here.
- **Whisper tiny.en local**: No STT API cost, no network dependency for core function, runs in ~real-time on Pi 4B for short chunks.
- **FastAPI**: Async, fast to write, automatic OpenAPI docs, TypeScript-friendly JSON responses.
- **Next.js + Auth0**: Tristan's comfort zone, Auth0 SDK is best-in-class for Next.js, satisfies MLH prize track.
- **SQLite + Postgres dual-write**: Pi works offline; family dashboard gets cloud data.

### 10.3 Alternatives Considered

- **Google STT API**: Rejected — adds latency, cost, and network dependency for core function.
- **Flask over FastAPI**: Rejected — FastAPI's async support better for concurrent Pi tasks.
- **Supabase over Railway Postgres**: Both viable; Railway chosen for simpler connection string setup.

---

## 11. Data Design

### 11.1 Entities and Schemas

**Table: `events`**
```sql
CREATE TABLE events (
    id             TEXT PRIMARY KEY,          -- UUID v4
    created_at     DATETIME NOT NULL,         -- ISO8601, UTC
    trigger_type   TEXT NOT NULL,             -- 'auto' | 'manual'
    scam_score     INTEGER,                   -- 0-100, NULL if manual
    keywords       TEXT,                      -- JSON array of matched keywords
    transcript     TEXT,                      -- Full transcript of the chunk(s)
    sms_sent       INTEGER NOT NULL DEFAULT 0, -- 0 | 1
    synced         INTEGER NOT NULL DEFAULT 0  -- 0 | 1 (synced to Postgres)
);
```

**Table: `config`** (Pi-side, single row)
```sql
CREATE TABLE config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
-- Rows: ngrok_url, nest_ip, startup_time
```

**Postgres schema**: Identical `events` table, without `synced` column.

### 11.2 Migrations and Seeding Plan

- Pi: Run `init_db.py` on first boot — creates SQLite file at `/data/scamshield.db`, runs CREATE TABLE statements.
- Postgres: Run `migrate.sql` via Railway CLI or psql on first deploy.
- Seed data: 3 sample events seeded in dev mode for dashboard UI testing.

### 11.3 Example Records

```json
{
  "id": "a3f1c2d4-7e89-4b10-b123-abc123def456",
  "created_at": "2025-03-21T14:32:10Z",
  "trigger_type": "auto",
  "scam_score": 87,
  "keywords": ["IRS", "gift cards", "don't tell anyone"],
  "transcript": "This is the IRS. You owe back taxes and must pay immediately with gift cards. Don't tell anyone about this call.",
  "sms_sent": 1,
  "synced": 1
}
```

```json
{
  "id": "b9e2d1f5-1234-4c20-c456-def456abc789",
  "created_at": "2025-03-21T15:10:44Z",
  "trigger_type": "manual",
  "scam_score": null,
  "keywords": [],
  "transcript": "Something felt wrong about this call.",
  "sms_sent": 1,
  "synced": 1
}
```

---

## 12. API and Interface Contracts

### 12.1 Authentication & Authorization Model

| Role | Access |
|------|--------|
| Family Member (authenticated) | Read all events, view transcripts |
| Unauthenticated | Redirect to Auth0 login |
| Pi server (internal) | Write events via internal FastAPI (no auth — LAN only) |

The Next.js dashboard calls the Pi's FastAPI server (via ngrok URL) only from server-side components — the ngrok URL is stored server-side in an environment variable, never exposed to the browser.

### 12.2 FastAPI Endpoints (Pi Server)

---

**GET /events**
- Auth: None (LAN-only, accessed server-side by Next.js)
- Query params: `limit` (default 50), `offset` (default 0), `trigger_type` (optional filter)
- Response:
```json
{
  "events": [{ ...event object }],
  "total": 42
}
```
- Errors: `500` on DB read failure

---

**POST /events**
- Internal use only (alert pipeline writes via Python directly, but endpoint available for testing)
- Request body:
```json
{
  "trigger_type": "auto",
  "scam_score": 87,
  "keywords": ["IRS"],
  "transcript": "..."
}
```
- Response: `201` with created event object
- Errors: `422` on validation failure

---

**GET /status**
- Returns current system status
- Response:
```json
{
  "nest_connected": true,
  "listening": true,
  "uptime_seconds": 3610,
  "last_event_at": "2025-03-21T14:32:10Z"
}
```

---

**GET /health**
- Returns `200 {"ok": true}` — used by dashboard to check Pi connectivity.

---

### 12.3 Next.js API Routes

**GET /api/events**
- Auth: Auth0 session required (middleware enforced)
- Fetches from Pi FastAPI via ngrok URL (server-side)
- Query params: `page` (default 1), `limit` (default 20)
- Response: same shape as FastAPI `/events`

**GET /api/status**
- Auth: Auth0 session required
- Proxies to Pi FastAPI `/status`

### 12.4 Rate Limiting

- Gemini API calls: max 1 call per 3-second audio chunk — naturally rate-limited by chunk cadence.
- Twilio: no more than 1 SMS per 60 seconds per phone number (debounce in `alert.py`).
- Next.js API routes: no additional rate limiting needed for hackathon demo.

### 12.5 Pagination

- Events are paginated: `page` and `limit` query params. Default 20 per page.
- Dashboard displays most recent events first.

---

## 13. Business Logic Rules

| ID | Rule |
|----|------|
| BL-001 | Alert pipeline fires if AND ONLY IF: `scam_score >= 70` OR `len(matched_keywords) >= 2`. |
| BL-002 | Keyword matching is case-insensitive. Partial word matches are NOT counted (e.g., "history" does not match "his"). |
| BL-003 | Grove Button press ALWAYS fires alert pipeline regardless of score or keywords. trigger_type = "manual". |
| BL-004 | Twilio SMS is debounced: if an SMS was sent in the last 60 seconds, skip SMS but still do Nest/LED/Buzzer/DB. |
| BL-005 | ElevenLabs warning.mp3 is generated ONCE at startup. If generation fails, Pi uses Nest's native TTS with a plain text string as fallback. |
| BL-006 | Audio is NEVER written to disk. Only transcript strings are persisted. Temp WAV buffers are in-memory only. |
| BL-007 | Scam score from Gemini is parsed from response JSON. If response cannot be parsed as integer 0–100, score defaults to 0 and keyword fallback takes over. |
| BL-008 | Grove LED: GREEN = idle/ready, RED = scam detected, YELLOW (if supported) = currently listening/transcribing. |
| BL-009 | After alert fires, system continues listening — it does not pause or require reset. |
| BL-010 | If Postgres sync fails, SQLite events with `synced = 0` are retried in the next sync cycle. |

### Scam Keyword List (initial set)

```python
SCAM_KEYWORDS = [
    "IRS", "internal revenue", "social security", "medicare", "medicaid",
    "gift card", "wire transfer", "bitcoin", "cryptocurrency",
    "warrant", "arrest", "lawsuit", "deportation",
    "don't tell anyone", "keep this confidential", "act now", "immediately",
    "prize", "lottery", "you've won", "claim your reward",
    "tech support", "virus", "infected", "remote access",
    "grandchild", "bail", "jail", "accident",
    "refund", "overpaid", "send money"
]
```

---

## 14. Edge Cases

| ID | Edge Case | Related FR | Handling |
|----|-----------|-----------|---------|
| EC-001 | Gemini API returns non-JSON or malformed response | FR-003 | Log raw response, default score to 0, keyword fallback proceeds |
| EC-002 | Google Nest not found on network at startup | FR-006 | Log warning, mark nest_connected = false, skip Nest in alert pipeline |
| EC-003 | Grove Button pressed during active alert (within 10s of prior alert) | FR-011 | Fire alert pipeline again; SMS debounce may suppress SMS |
| EC-004 | Whisper crashes mid-transcription | FR-002 | Catch exception, discard chunk, restart capture loop |
| EC-005 | Twilio account out of credits | FR-009 | Log error; all other alert actions still execute |
| EC-006 | Very loud background noise triggers VAD constantly | FR-001 | Raise VAD_THRESHOLD in config; add minimum duration check (>1s of sustained noise) |
| EC-007 | Pi loses internet mid-call | FR-003, FR-009 | Keyword fallback handles detection; SMS fails gracefully; SQLite still writes |
| EC-008 | Multiple scam phrases in rapid succession | FR-005 | Each chunk is evaluated independently; SMS debounce prevents spam |
| EC-009 | Auth0 session expired on dashboard | FR-014 | next-auth middleware redirects to login automatically |
| EC-010 | Postgres unreachable for >5 sync cycles | FR-012 | Log persistent sync failure; SQLite continues accumulating; alert on status endpoint |
| EC-011 | ElevenLabs rate limit at startup | FR-016 | Retry once after 5s; if still failing, use Nest native TTS fallback |
| EC-012 | SenseCAP not connected on USB | FR-015 | Log warning, skip SenseCAP output, all other functions unaffected |

---

## 15. Observability

### 15.1 Logging

All Pi-side logs use Python `logging` module with structured fields. Log to stdout + `/var/log/scamshield.log`.

```python
# Structured log format
{
  "timestamp": "2025-03-21T14:32:07Z",
  "level": "INFO",
  "module": "detection",
  "event": "scam_detected",
  "scam_score": 87,
  "keywords": ["IRS", "gift cards"],
  "trigger_type": "auto"
}
```

Log every: audio chunk processed, Gemini API call (success/fail), alert fired, SMS sent/failed, sync cycle result, startup sequence steps.

### 15.2 Metrics

| Metric | Type | Notes |
|--------|------|-------|
| `chunks_processed` | Counter | Total audio chunks transcribed |
| `alerts_fired` | Counter | Total alert pipeline executions |
| `gemini_errors` | Counter | Gemini API failures |
| `sms_sent` | Counter | Successful Twilio sends |
| `sync_lag_events` | Gauge | Count of unsynced SQLite events |
| `detection_latency_ms` | Histogram | Time from chunk ready to alert fired |

Metrics exposed at `/metrics` on FastAPI server (Prometheus text format).

### 15.3 Alerts

- If `gemini_errors` > 5 in 5 minutes: log `CRITICAL` — likely API key issue.
- If `sync_lag_events` > 50: log `WARNING` — Postgres sync likely broken.

---

## 16. Security and Privacy

- **Secrets**: All API keys in `.env` files. `.env` is in `.gitignore`. `.env.example` has placeholder values only.
- **Audio privacy**: Raw audio is NEVER written to disk or transmitted. Only text transcripts persist.
- **Transcript storage**: Transcripts stored in SQLite (local) and Postgres (cloud). Postgres on Railway uses TLS in transit.
- **Auth**: Dashboard protected by Auth0. No unauthenticated access to event data.
- **ngrok tunnel**: Pi FastAPI is only called server-side from Next.js — ngrok URL never exposed to browser clients.
- **Input validation**: FastAPI uses Pydantic models for all request validation. SQL queries use parameterized statements only — no string interpolation.
- **Dependency security**: Pin all dependency versions in `requirements.txt` and `package-lock.json`.
- **PII**: Family phone number stored only in `.env` on Pi. Not stored in DB. Transcripts may contain PII spoken during calls — treat as sensitive; do not log to external services.
- **Threat model highlights**:
  - Local network attacker could call Pi FastAPI directly — acceptable for hackathon; production would add API key header.
  - Transcript data in Postgres is plaintext — acceptable for hackathon; production would encrypt at rest.

---

## 17. Repository Blueprint

### 17.1 Folder Structure

```
scamshield/
├── pi/
│   ├── audio_capture.py        # Mic input loop + VAD using Grove Sound Sensor
│   ├── stt.py                  # Whisper tiny.en transcription
│   ├── detection.py            # Gemini API + keyword scam scoring
│   ├── alert.py                # Alert pipeline: Nest, LED, Buzzer, Twilio, DB
│   ├── sensecap.py             # Serial output to SenseCAP Indicator
│   ├── sync.py                 # SQLite → Postgres background sync worker
│   ├── db.py                   # SQLite init, read, write helpers
│   ├── server.py               # FastAPI REST server
│   ├── startup.py              # Startup sequence: ElevenLabs, Nest discovery, ngrok
│   ├── config.py               # Loads .env, defines constants (VAD_THRESHOLD, etc.)
│   ├── keywords.py             # SCAM_KEYWORDS list
│   ├── main.py                 # Entry point: wires all components, starts loops
│   ├── requirements.txt        # Pinned Python dependencies
│   ├── .env.example            # Env var template
│   └── tests/
│       ├── test_detection.py
│       ├── test_alert.py
│       └── test_db.py
├── dashboard/
│   ├── app/
│   │   ├── layout.tsx          # Root layout, Auth0 provider
│   │   ├── page.tsx            # Redirect to /dashboard
│   │   ├── dashboard/
│   │   │   └── page.tsx        # Main event log page
│   │   ├── api/
│   │   │   ├── events/
│   │   │   │   └── route.ts    # Proxy to Pi FastAPI /events
│   │   │   └── status/
│   │   │       └── route.ts    # Proxy to Pi FastAPI /status
│   │   └── auth/
│   │       └── [...nextauth]/
│   │           └── route.ts    # Auth0 handler
│   ├── components/
│   │   ├── EventTable.tsx      # Paginated event list
│   │   ├── EventRow.tsx        # Single event row with expand
│   │   ├── StatusBadge.tsx     # Online/offline Pi status indicator
│   │   └── AlertBanner.tsx     # Most recent alert summary at top
│   ├── lib/
│   │   └── api.ts              # Fetch helpers for Pi API
│   ├── middleware.ts            # Auth0 session enforcement
│   ├── .env.local.example      # Dashboard env var template
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
├── sensecap/
│   └── firmware/
│       └── display.ino         # Arduino sketch for SenseCAP serial display
├── .gitignore
└── README.md
```

### 17.2 File Responsibilities

| File | Purpose |
|------|---------|
| `pi/main.py` | Wires audio capture, STT, detection, alert, and GPIO interrupt into a single running process |
| `pi/audio_capture.py` | Opens PyAudio stream on webcam mic device, polls Grove Sound Sensor, buffers 3s WAV chunks to queue |
| `pi/stt.py` | Loads Whisper model once at startup, exposes `transcribe(wav_bytes) -> str` |
| `pi/detection.py` | `score_transcript(text) -> (score, keywords)` — calls Gemini, falls back to keyword match |
| `pi/alert.py` | `fire_alert(trigger_type, score, keywords, transcript)` — concurrent execution of all alert actions |
| `pi/server.py` | FastAPI app with `/events`, `/status`, `/health`, `/metrics` routes |
| `pi/sync.py` | `sync_loop()` — runs every 60s, finds unsynced SQLite rows, upserts to Postgres, marks synced |
| `pi/startup.py` | `run_startup()` — generates ElevenLabs audio, discovers Nest, starts ngrok, updates config table |
| `pi/sensecap.py` | Opens serial port, exposes `set_status(status, text)` sending simple protocol to SenseCAP |
| `dashboard/middleware.ts` | next-auth middleware that enforces Auth0 session on all `/dashboard/*` routes |
| `dashboard/app/dashboard/page.tsx` | Fetches and renders event list; polls `/api/status` every 30s |

### 17.3 Environment Variables

**`pi/.env.example`**
```env
# Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here

# Twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
TWILIO_TO_NUMBER=+1XXXXXXXXXX

# Database
SQLITE_DB_PATH=/data/scamshield.db
POSTGRES_URL=postgresql://user:password@host:5432/scamshield

# ngrok
NGROK_AUTHTOKEN=your_ngrok_authtoken_here

# Audio
AUDIO_DEVICE_INDEX=0
VAD_THRESHOLD=500
CHUNK_DURATION_SECONDS=3

# Grove HAT GPIO Pins
GPIO_LED_PIN=18
GPIO_BUZZER_PIN=23
GPIO_BUTTON_PIN=24
GPIO_SOUND_SENSOR_PIN=0

# SenseCAP
SENSECAP_SERIAL_PORT=/dev/ttyUSB0
SENSECAP_BAUD_RATE=115200

# Detection
SCAM_SCORE_THRESHOLD=70
SCAM_KEYWORD_MIN_MATCHES=2
SMS_DEBOUNCE_SECONDS=60
```

**`dashboard/.env.local.example`**
```env
# Auth0
AUTH0_SECRET=your_auth0_secret_here
AUTH0_BASE_URL=https://scamshield.app
AUTH0_ISSUER_BASE_URL=https://your-tenant.auth0.com
AUTH0_CLIENT_ID=your_auth0_client_id_here
AUTH0_CLIENT_SECRET=your_auth0_client_secret_here

# Pi API (server-side only — never exposed to browser)
PI_API_URL=https://your-ngrok-subdomain.ngrok-free.app
```

### 17.4 Commands and Scripts

**Pi:**
```bash
# Install
cd pi && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -c "import whisper; whisper.load_model('tiny.en')"  # pre-download model

# Initialize DB
python db.py --init

# Run (production / hackathon)
python main.py

# Run FastAPI server standalone (for testing)
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest tests/ -v

# Lint
flake8 . && black --check .
```

**Dashboard:**
```bash
# Install
cd dashboard && npm install

# Dev
npm run dev

# Build
npm run build

# Start (production)
npm start

# Lint
npm run lint

# Type check
npx tsc --noEmit
```

**Database:**
```bash
# Pi SQLite init
python pi/db.py --init

# Postgres migrate (run once on Railway)
psql $POSTGRES_URL -f migrate.sql
```

---

## 18. Testing Plan

### 18.1 Test Strategy

| Layer | Type | Tool |
|-------|------|------|
| Pi detection logic | Unit | pytest |
| Pi alert pipeline | Unit + Mock | pytest + unittest.mock |
| Pi DB operations | Integration | pytest + temp SQLite |
| Pi FastAPI endpoints | Integration | pytest + httpx TestClient |
| Dashboard components | Unit | Not required for hackathon |
| Dashboard API routes | Integration | Not required for hackathon |
| End-to-end scam detection | Manual acceptance test | Scripted test call |

### 18.2 Minimum Test Coverage Requirements

- `detection.py`: 100% of scoring logic paths (Gemini success, Gemini failure, keyword only, no match)
- `alert.py`: All branches mocked — Nest connected, Nest absent, SMS debounce active, SMS debounce inactive
- `db.py`: Write event, read events, mark synced
- `server.py`: GET /events, GET /status, GET /health — all return correct shapes

### 18.3 Acceptance Tests (AT-###)

**AT-001: Auto scam detection end-to-end**
1. Start Pi system (`python main.py`)
2. Confirm Grove LED is green, SenseCAP shows "ScamShield Ready"
3. Place phone on speakerphone near Pi
4. Play recorded audio: "This is the IRS. You owe $5,000 in back taxes. Pay with gift cards immediately. Don't tell anyone."
5. Within 10 seconds: Google Nest speaks warning aloud ✓
6. Grove LED turns red ✓
7. Grove Buzzer sounds for ~2 seconds ✓
8. Family member phone receives Twilio SMS with "IRS" and "gift cards" listed ✓
9. SQLite has 1 new event record with trigger_type="auto" ✓
10. Dashboard shows the event after next sync cycle ✓

**AT-002: Manual button trigger**
1. System is running and idle
2. Press Grove Button
3. Within 3 seconds: Nest speaks warning, LED red, Buzzer fires, SMS sent with trigger_type="manual" ✓
4. SQLite event has `trigger_type = "manual"` and `scam_score = null` ✓

**AT-003: SMS debounce**
1. Fire AT-001
2. Immediately fire AT-002 (within 60 seconds)
3. Second alert: Nest/LED/Buzzer fire ✓, SMS is NOT sent ✓ (debounce active)

**AT-004: Gemini API failure fallback**
1. Set `GEMINI_API_KEY=invalid` in .env
2. Run AT-001 with same audio
3. Scam still detected via keyword fallback ✓
4. Error logged to scamshield.log ✓

**AT-005: Dashboard authentication**
1. Open `https://scamshield.app/dashboard` while logged out
2. Redirected to Auth0 login ✓
3. Log in with valid credentials
4. Redirected back to dashboard, events visible ✓

**AT-006: False positive test**
1. Play 10 minutes of normal conversation audio (no scam keywords)
2. Confirm zero alerts fired ✓
3. Confirm LED remains green ✓

---

## 19. Implementation Plan

### Phase 1: Scaffold & Foundations

**Goals**: Repo structure, dependency install, DB init, env loading, Grove HAT GPIO confirmed working.

**Deliverables**:
- Git repo initialized with folder structure from §17.1
- `pi/requirements.txt` with all pinned deps installed in venv
- `pi/config.py` loading .env with validation
- `pi/db.py` with SQLite init and basic CRUD
- `pi/keywords.py` with initial keyword list
- `dashboard/` Next.js app scaffolded with Auth0 configured
- Grove LED toggles green/red from a test script
- Grove Button interrupt fires a print statement

**Files to create**: All scaffold files, `.gitignore`, `.env.example`, `requirements.txt`, `package.json`

**Tests**: `test_db.py` — write and read one event

**Exit criteria**: `python db.py --init` succeeds; LED blinks on `test_gpio.py`; `npm run dev` loads dashboard login page.

---

### Phase 2: Core Data + Core APIs

**Goals**: Audio capture → STT → Detection pipeline working. FastAPI server live. Sync worker functional.

**Deliverables**:
- `audio_capture.py`: reads webcam mic, VAD via sound sensor, emits WAV chunks to queue
- `stt.py`: Whisper tiny.en loaded, `transcribe()` returns text string
- `detection.py`: `score_transcript()` calls Gemini, parses score, runs keyword check, returns tuple
- `server.py`: FastAPI with `/events`, `/status`, `/health` routes
- `sync.py`: background thread syncing SQLite to Postgres
- `pi/tests/test_detection.py`: all scoring branches covered
- `pi/tests/test_db.py`: full CRUD coverage

**Files to create**: `audio_capture.py`, `stt.py`, `detection.py`, `server.py`, `sync.py`

**Tests**: `test_detection.py` with mocked Gemini responses

**Exit criteria**: Pipe a pre-recorded WAV file through `stt.py` + `detection.py` and get a score ≥ 70 for scam audio, ≤ 30 for normal audio.

---

### Phase 3: Core UI + Core Workflows

**Goals**: Alert pipeline fully functional. Dashboard displays real events. End-to-end AT-001 passing.

**Deliverables**:
- `alert.py`: all alert actions wired — Nest (pychromecast), LED, Buzzer, Twilio, DB write, SenseCAP
- `startup.py`: ElevenLabs generation, Nest discovery, ngrok startup
- `main.py`: full event loop wiring audio_capture → stt → detection → alert + GPIO interrupt for button
- `sensecap.py`: serial protocol sending status strings
- `sensecap/firmware/display.ino`: SenseCAP firmware parsing serial commands
- `dashboard/app/dashboard/page.tsx`: event table with pagination
- `dashboard/components/EventTable.tsx`, `EventRow.tsx`, `AlertBanner.tsx`
- `dashboard/app/api/events/route.ts`: server-side proxy to Pi API

**Files to create**: `alert.py`, `startup.py`, `main.py`, `sensecap.py`, all dashboard components

**Tests**: `test_alert.py` with all external calls mocked

**Exit criteria**: AT-001 and AT-002 pass manually.

---

### Phase 4: Edge Cases + Security + Performance

**Goals**: All edge cases from §14 handled. Secrets confirmed out of git. Debounce working. Fallbacks tested.

**Deliverables**:
- Gemini failure fallback tested (AT-004)
- SMS debounce implemented and tested (AT-003)
- Nest-not-found graceful degradation
- All `.env` values validated at startup with clear error messages if missing
- `middleware.ts` enforcing Auth0 on all dashboard routes (AT-005)
- False positive test passing (AT-006)
- Audio never written to disk — confirmed via code review

**Files to modify**: `detection.py`, `alert.py`, `startup.py`, `config.py`, `dashboard/middleware.ts`

**Tests**: Add edge case branches to existing test files

**Exit criteria**: All 6 acceptance tests pass.

---

### Phase 5: Observability + Polish + Final QA

**Goals**: Logging structured, `/metrics` live, dashboard polished, README complete, demo rehearsed.

**Deliverables**:
- Structured logging in all Pi modules
- `/metrics` endpoint on FastAPI (Prometheus format)
- `dashboard/components/StatusBadge.tsx` showing Pi online/offline
- GoDaddy domain pointed to Vercel deployment
- Auth0 production tenant configured with correct callback URLs
- `README.md` with setup instructions, hardware wiring diagram, and team info
- 3D print phone stand designed (non-code — physical prop)
- Demo script rehearsed: scripted scam call → live Nest audio → SMS on judge's phone

**Files to create/modify**: All logging additions, `README.md`

**Exit criteria**: Full demo run in under 5 minutes with no failures. All checklist items below satisfied.

---

## 20. Final Checklist

```
[ ] Grove LED turns green on startup
[ ] Grove Button press fires alert pipeline
[ ] Audio capture starts automatically on boot
[ ] Whisper transcribes audio within 3s of chunk completion
[ ] Gemini API returns scam score for test transcript
[ ] Keyword fallback fires correctly when Gemini is disabled
[ ] Alert threshold (score ≥70 OR keywords ≥2) is correctly enforced
[ ] Google Nest plays ElevenLabs warning audio on detection
[ ] Grove Buzzer fires for 2 seconds on detection
[ ] Grove LED turns red on detection, green after 10s
[ ] Twilio SMS received on family number with correct content
[ ] SMS debounce prevents duplicate SMS within 60s
[ ] SQLite event written for every alert
[ ] Postgres sync runs every 60s and marks events as synced
[ ] FastAPI /events returns correct paginated JSON
[ ] FastAPI /health returns 200
[ ] Dashboard loads and requires Auth0 login
[ ] Dashboard displays event list with correct data
[ ] Dashboard shows most recent alert in banner
[ ] SenseCAP shows live status and transcript
[ ] ngrok tunnel stable and dashboard reachable remotely
[ ] GoDaddy domain resolves to Vercel dashboard
[ ] No API keys committed to git
[ ] .env.example has all required keys documented
[ ] AT-001 through AT-006 all pass
[ ] README complete with wiring diagram and setup steps
[ ] Gemini API prize track: Gemini used for scam detection ✓
[ ] ElevenLabs prize track: ElevenLabs voice used for Nest warning ✓
[ ] Auth0 prize track: Auth0 used for dashboard login ✓
[ ] GoDaddy prize track: Domain registered and live ✓
[ ] Accessibility & Empowerment: project narrative prepared for judges ✓
```

---

## 21. Open Questions

- **OQ-001**: Does the hackathon's Grove Base HAT fit the Pi 4B kit provided, or does a separate HAT need to be sourced? Verify before the event.
- **OQ-002**: What is the exact USB serial port path for the SenseCAP Indicator on Pi OS (`/dev/ttyUSB0` vs `/dev/ttyACM0`)? Confirm after first connection.
- **OQ-003**: Does the hackathon WiFi block mDNS/local discovery? If so, pychromecast Nest discovery may need the Nest's static IP hardcoded in `.env`.
- **OQ-004**: Is a GoDaddy `.app` TLD available for the chosen name, or is a different TLD needed? Confirm at domain registration.
