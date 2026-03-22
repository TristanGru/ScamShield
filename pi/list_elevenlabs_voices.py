#!/usr/bin/env python3
"""
List voices available to your ElevenLabs API key (GET /v1/voices).

Premade voices (category: premade) are included with all accounts and work on the free tier
for API text-to-speech. Voice Library / marketplace voices often return 402 on free plans.

Usage (from repo root or pi/):
  cd pi && python list_elevenlabs_voices.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def main() -> int:
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not key:
        print("Set ELEVENLABS_API_KEY in pi/.env", file=sys.stderr)
        return 1

    import httpx

    r = httpx.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": key},
        timeout=60.0,
    )
    r.raise_for_status()
    data = r.json()
    voices = data.get("voices") or []

    def sort_key(v: dict) -> tuple:
        return (v.get("category") or "", v.get("name") or "")

    print(f"{'voice_id':<26}  {'category':<12}  name")
    print("-" * 70)
    for v in sorted(voices, key=sort_key):
        vid = v.get("voice_id") or "?"
        cat = v.get("category") or "?"
        name = v.get("name") or "?"
        print(f"{vid:<26}  {cat:<12}  {name}")

    print(f"\nTotal: {len(voices)} voice(s). Prefer category=premade for free-tier API.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
