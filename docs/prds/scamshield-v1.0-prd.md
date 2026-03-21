# ScamShield - Product Requirements Document (PRD)

## Requirements Description

### Background
- **Business Problem**: Elderly users are disproportionately targeted by phone scammers and often lack the technical awareness to identify fraudulent calls in real time. Family members cannot monitor calls remotely and are notified only after harm has occurred.
- **Target Users**: Primary — elderly individuals living independently or semi-independently. Secondary — trusted family members who oversee their safety.
- **Value Proposition**: Real-time, passive scam call detection using AI + hardware alerts that require zero technical literacy from the elderly user, with a remote family dashboard for oversight.

### Feature Overview
- **Core Features**:
  1. Passive audio monitoring via Logitech webcam microphone
  2. Chunked audio analysis (every 15–20 seconds) via Gemini API
  3. Hardware alerts: Red LED (danger) / Green LED (safe), SenseCAP display text
  4. Verbal alert via ElevenLabs TTS → Google Nest speaker
  5. Manual scam report button (elderly user presses if suspicious)
  6. Family notification via Twilio SMS + dashboard event log
  7. Auth0-protected family dashboard (Next.js, cloud-hosted)

- **Feature Boundaries**:
  - Does NOT intercept or block calls — passive listening only
  - Does NOT store raw audio — only transcripts/summaries
  - Does NOT require any interaction from elderly user beyond pressing a button
  - MVP: voice calls only (no SMS/email scam detection)

- **User Scenarios**:
  1. Elder receives call → puts on speaker → ScamShield auto-activates → Gemini flags scam mid-call → Red LED + SenseCAP warning + Nest verbal alert → Family gets SMS + dashboard log
  2. Elder suspects scam → presses button → manual report logged → same alert chain fires
  3. Family member logs into dashboard from anywhere → sees full history of calls, scam flags, manual reports

### Detailed Requirements

- **Input**: Continuous microphone stream (Logitech webcam) recorded in 15-second WAV chunks
- **Output**: Scam probability score + reason from Gemini; hardware + software alerts if threshold exceeded
- **User Interaction**:
  - Elderly: Physical button press to self-report; visual LED + SenseCAP text; verbal Nest announcement
  - Family: Auth0 login → dashboard showing call events, timestamps, scam reason, who triggered it
- **Data Requirements**:
  - Event log: timestamp, trigger (auto/manual), scam_reason, confidence_score, audio_chunk_id
  - No raw audio stored; only metadata
- **Edge Cases**:
  - False positive: Green LED + "Call seems safe" on SenseCAP by default; only escalate on high confidence
  - No internet: Queue alerts locally, flush when reconnected
  - Button pressed during non-scam: Still logged, family notified as manual report
  - Gemini API error: Fail safe (no alert), log error, retry next chunk

---

## Design Decisions

### Technical Architecture

```
[Logitech Webcam Mic]
        ↓ audio stream
[Raspberry Pi 4 - Python]
  ├── audio_capture.py   → records 15s WAV chunks
  ├── scam_detector.py   → sends chunks to Gemini API, parses result
  ├── hardware.py        → controls LEDs, reads button, writes SenseCAP
  ├── notifier.py        → calls backend API, triggers ElevenLabs + Nest
  └── main.py            → orchestration loop
        ↓ HTTPS POST (scam event)
[FastAPI Backend - Render/Railway]
  ├── Supabase           → event persistence
  └── Twilio             → SMS to family members
        ↓
[Next.js Dashboard - Vercel]
  └── Auth0              → family member login
```

### Key Components
- **Audio Capture**: PyAudio, 16kHz mono WAV, 15-second chunks
- **Scam Detection**: Gemini 1.5 Flash (multimodal, audio-capable), confidence threshold 0.75
- **Hardware**: RPi.GPIO for LEDs + button; Grove I2C for SenseCAP; Nest via pychromecast + ElevenLabs MP3
- **Backend**: FastAPI, Supabase (postgres + realtime), Twilio SMS
- **Frontend**: Next.js 14 App Router, Auth0, Supabase realtime subscription
- **Hosting**: Backend on Render (free tier), Frontend on Vercel (free tier)

### Constraints
- **Latency**: Alert must fire within 20 seconds of scam pattern detected
- **Cost**: Twilio trial credits sufficient for hackathon; Gemini free tier sufficient
- **Privacy**: No audio stored; transcripts optionally stored
- **Offline resilience**: Local SQLite queue as fallback

---

## Acceptance Criteria

### Functional Acceptance
- [ ] Audio recorded in 15-second chunks continuously while system is running
- [ ] Each chunk sent to Gemini API and scam score returned
- [ ] Red LED activates when confidence ≥ 0.75; Green LED otherwise
- [ ] SenseCAP displays "⚠️ SCAM DETECTED" or "✓ Call seems safe"
- [ ] Google Nest announces verbal warning via ElevenLabs TTS
- [ ] Physical button press triggers same alert chain as auto-detection
- [ ] Backend receives event, stores to Supabase, sends Twilio SMS to family
- [ ] Family dashboard loads with Auth0 login and shows event history
- [ ] Dashboard accessible from any device/location

### Quality Standards
- [ ] Gemini prompt tuned for elderly scam patterns (urgency, gift cards, IRS, lottery)
- [ ] No raw audio persisted anywhere
- [ ] Environment variables used for all API keys
- [ ] System recovers from Gemini API errors without crashing

---

## Execution Phases

### Phase 1: Raspberry Pi Core (Hours 1–6)
**Goal**: Working scam detection loop on Pi
- [x] Set up Python venv, install dependencies
- [x] `audio_capture.py`: record 15s WAV chunks from webcam mic (default `CHUNK_DURATION_SECONDS=15`)
- [x] `scam_detector.py`: Gemini transcript analysis, confidence (0–1) + reason (`pi/scam_detector.py`)
- [x] `hardware.py`: GPIO LED control, button interrupt, SenseCAP helpers (`pi/hardware.py`)
- [x] `main.py`: integrate all Pi modules into detection loop
- **Deliverables**: Pi detects scam audio and triggers LEDs

### Phase 2: Backend + Notifications (Hours 6–12)
**Goal**: Events logged and family notified
- [ ] FastAPI app with `/events` POST endpoint
- [ ] Supabase table: `scam_events`
- [ ] Twilio SMS on new scam event
- [ ] ElevenLabs TTS + pychromecast → Google Nest
- [ ] Pi `notifier.py` calls backend and Nest
- **Deliverables**: End-to-end alert chain working

### Phase 3: Family Dashboard (Hours 12–20)
**Goal**: Auth-protected family view
- [ ] Next.js app with Auth0
- [ ] Dashboard page: real-time event feed from Supabase
- [ ] Event cards: timestamp, trigger type, scam reason, confidence
- [ ] Deploy to Vercel
- **Deliverables**: Family can log in from phone and see alerts

### Phase 4: Polish + Demo Prep (Hours 20–24)
**Goal**: Demo-ready
- [ ] README with setup instructions
- [ ] .env.example with all required keys
- [ ] End-to-end demo run and bug fixes
- [ ] Record demo video if time permits

---

**Document Version**: 1.0
**Created**: 2026-03-21
**Clarification Rounds**: 2
**Quality Score**: 92/100
