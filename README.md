# Boilermaker Map 

An interactive campus map that helps Purdue students visualize their class schedules geographically.

## Overview

Boilermaker Map is a web application designed to help Purdue University students organize and visualize their classes on an interactive map of the West Lafayette campus.

Using the Geoapify mapping API, the application displays campus locations and allows students to add their courses, associate them with buildings, and view their schedules directly on the map.

Instead of relying solely on a traditional timetable, students can see where their classes take place and understand how their academic schedule fits into the physical campus.

## Features

Interactive Campus Map: Explore Purdue University's West Lafayette campus using Geoapify map tiles.

Class Management: Add classes with course names, building locations, meeting times, and days of the week.

Geographic Class Visualization: Display class locations as markers on the map.

Building Information: Select campus buildings and associate them with scheduled classes.

Class Details: Click map markers to view course information and meeting times.

Schedule Persistence: Save class schedules locally so they remain available between sessions.
=======
# SteamLine

One dynamic timeline and map for your Brightspace schedule and Instagram club posts. **Gemma 4** extracts events locally through Ollama. Your day never leaves the laptop.

Tan / orange / dark UI. Leaflet + OpenStreetMap (no map API key). FastAPI sits between the browser and Ollama so prompts, JSON schemas, and CORS stay in one place.

## Why Gemma 4

- **Structured output** — Ollama `format` forces a JSON schema so a small model returns events, not free text.
- **Vision** — upload a flyer screenshot; Gemma reads title, time, and place from the image.
- **Local and private** — Apache 2.0, on-device. Pitch line: *your schedule never leaves your machine.*
- **Ask SteamLine** — a chat box with the day’s events in the prompt (“Can I make the 6pm club meeting after my lab?”).

Instagram is an **ingestion** step (paste caption or screenshot). A production build would use an official feed or club-submitted posts. We do not scrape.

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | React + Vite, Tailwind, react-leaflet |
| Backend | FastAPI |
| Model | `gemma4:e4b` via Ollama (`gemma4:e2b` if the laptop is slow) |
| Storage | React state + `localStorage` |
| Skills | `backend/skills/schedule-extractor.md`, `event-extractor.md` |

## Run

```bash
# 1. Model
ollama pull gemma4:e4b
# fallback: ollama pull gemma4:e2b && export OLLAMA_MODEL=gemma4:e2b

# 2. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

If Wi-Fi or Gemma fails, click **Load demo data**. That path never calls the model.

## Layout

```
backend/
  main.py              # /extract/schedule, /extract/event, /ask
  gemma.py             # Ollama chat + JSON schema + one retry
  skills/              # short prompts for a small model
frontend/src/
  App.jsx
  components/          # AddSchedule, AddEvent, Timeline, MapView, GapBadge
  data/buildings.json  # Purdue codes + lat/lon
```

Walking time is straight-line distance ÷ **80 m/min**. Gap badges are green (`12 min gap, 5 min walk`) or red (`Tight: 4 min gap, 9 min walk`).

## Made for Hacktoberfest Hackathon. Held by Hello World @ Purdue University

## License

MIT
Geoapify
Folium
