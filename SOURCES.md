# Sources

This file records the main references, official documentation, and external services used while building ScamShield.

## How To Use This File

- Prefer official documentation links over blog posts or random tutorials.
- Add sources by feature area so future teammates can quickly find what informed a part of the project.
- If you use a tutorial, note what it helped with and keep the official docs next to it.
- Do not put secrets, API keys, or private dashboard links in this file.

## Project-Specific Internal References

- [README.md](README.md)
  Main project overview, setup steps, architecture, and environment variables.
- [docs/prds/scamshield-v1.0-prd.md](docs/prds/scamshield-v1.0-prd.md)
  Product requirements, flow, and feature expectations.
- [migrate.sql](migrate.sql)
  Database schema used for synced event storage.

## AI And Detection

- Google Gemini API docs
  https://ai.google.dev/gemini-api/docs
- Google Gen AI Python SDK
  https://googleapis.github.io/python-genai/
- Vosk speech recognition
  https://alphacephei.com/vosk/
- Vosk Python package
  https://pypi.org/project/vosk/

## Alerts, Messaging, And Audio

- ElevenLabs API docs
  https://elevenlabs.io/docs
- ElevenLabs Python SDK
  https://pypi.org/project/elevenlabs/
- Twilio Messaging docs
  https://www.twilio.com/docs/messaging
- Twilio Python SDK
  https://pypi.org/project/twilio/
- pychromecast
  https://pypi.org/project/PyChromecast/
- gTTS
  https://pypi.org/project/gTTS/

## Raspberry Pi, Hardware, And Device I/O

- Raspberry Pi documentation
  https://www.raspberrypi.com/documentation/
- rpi-lgpio
  https://pypi.org/project/rpi-lgpio/
- PyAudio
  https://people.csail.mit.edu/hubert/pyaudio/
- pyserial
  https://pyserial.readthedocs.io/en/latest/
- Seeed Studio Grove system
  https://wiki.seeedstudio.com/Grove_System/
- SenseCAP Indicator docs
  https://wiki.seeedstudio.com/SenseCAP_Indicator/

## Backend And Data

- FastAPI docs
  https://fastapi.tiangolo.com/
- Uvicorn docs
  https://www.uvicorn.org/
- Pydantic docs
  https://docs.pydantic.dev/
- aiosqlite
  https://pypi.org/project/aiosqlite/
- Psycopg 3 docs
  https://www.psycopg.org/psycopg3/docs/
- Schedule
  https://pypi.org/project/schedule/
- HTTPX docs
  https://www.python-httpx.org/
- Python dotenv
  https://pypi.org/project/python-dotenv/

## Frontend, Auth, And Hosting

- Next.js docs
  https://nextjs.org/docs
- React docs
  https://react.dev/
- Tailwind CSS docs
  https://tailwindcss.com/docs
- Auth0 Next.js SDK docs
  https://auth0.github.io/nextjs-auth0/
- Auth0 docs
  https://auth0.com/docs
- Vercel docs
  https://vercel.com/docs

## Tunneling And Deployment

- ngrok docs
  https://ngrok.com/docs
- pyngrok
  https://pyngrok.readthedocs.io/en/latest/

## Notes For Submission Or Demo

If you need a short “sources used” section for Devpost or a slide deck, a good condensed list is:

- Google Gemini API
- Vosk speech recognition
- ElevenLabs API
- Twilio API
- FastAPI
- Next.js
- Auth0
- Vercel
- ngrok
- Raspberry Pi / Grove / SenseCAP documentation
