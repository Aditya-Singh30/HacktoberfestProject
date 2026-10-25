from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import gemma
from normalize import WEEKDAYS, normalize_events

ROOT = Path(__file__).resolve().parent
SKILLS = ROOT / "skills"
BUILDINGS_PATH = ROOT.parent / "frontend" / "src" / "data" / "buildings.json"
_STR = {"type": "string"}
_EVENT_PROPS = {"title": _STR, "building": _STR, "location": _STR, "date": _STR, "start": _STR, "end": _STR}
EVENT_SCHEMA = {"type": "object", "properties": {"events": {"type": "array", "items": {"type": "object", "properties": _EVENT_PROPS, "required": ["title", "start"]}}}, "required": ["events"]}
SCHEDULE_SCHEMA = {"type": "object", "properties": {"events": {"type": "array", "items": {"type": "object", "properties": {**_EVENT_PROPS, "days": {"type": "array", "items": _STR}}, "required": ["title", "days", "start"]}}}, "required": ["events"]}

DEFAULT_EVENT_SKILL = """You extract campus events from an Instagram caption or flyer image.
Return JSON: {\"events\":[{\"title\",\"building\",\"location\",\"date\",\"start\",\"end\"}]}.
Rules: date is YYYY-MM-DD; start/end are 24-hour HH:MM; use known building codes; never invent details.
"""
DEFAULT_SCHEDULE_SKILL = """You extract class meetings from pasted registrar/Brightspace text.
Return JSON: {\"events\":[{\"title\",\"days\",\"building\",\"location\",\"start\",\"end\"}]}.
Rules: days is a list from Mon,Tue,Wed,Thu,Fri; M T W R F mean Mon Tue Wed Thu Fri; times are HH:MM; never invent classes.
"""


def load_skill(name: str, default: str) -> str:
    path = SKILLS / f"{name}.md"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return default


def load_buildings() -> list[dict[str, Any]]:
    try:
        data = json.loads(BUILDINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def context_block(day: str, buildings: list[dict[str, Any]]) -> str:
    parsed = dt.date.fromisoformat(day)
    codes = ", ".join(f"{building['code']} ({building.get('name', '')})" for building in buildings)
    return f"Today's date: {dt.date.today().isoformat()}\nDate being planned: {day} ({WEEKDAYS[parsed.weekday()]})\nValid building codes: {codes}"


class ScheduleIn(BaseModel):
    text: str = ""
    date: str


class EventIn(BaseModel):
    caption: str = ""
    date: str
    images: list[str] = Field(default_factory=list)


class AskIn(BaseModel):
    question: str
    events: list[dict[str, Any]] = Field(default_factory=list)
    date: str | None = None


def check_date(day: str) -> None:
    try:
        dt.date.fromisoformat(day)
    except ValueError as exc:
        raise HTTPException(422, f"Bad date '{day}'. Use YYYY-MM-DD.") from exc


app = FastAPI(title="SteamLine")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])


@app.post("/extract/schedule")
def extract_schedule(body: ScheduleIn) -> dict[str, Any]:
    check_date(body.date)
    if not body.text.strip():
        raise HTTPException(400, "Paste your schedule text first.")
    buildings = load_buildings()
    try:
        raw = gemma.extract(load_skill("schedule-extractor", DEFAULT_SCHEDULE_SKILL), f"{context_block(body.date, buildings)}\n\nSchedule text:\n{body.text}", SCHEDULE_SCHEMA)
    except gemma.GemmaError as exc:
        raise HTTPException(502, str(exc)) from exc
    weekday = WEEKDAYS[dt.date.fromisoformat(body.date).weekday()]
    events, warnings = normalize_events(raw, day=body.date, source="class", buildings=buildings, default_minutes=50, weekday_filter=weekday)
    return {"events": events, "warnings": warnings}


@app.post("/extract/event")
def extract_event(body: EventIn) -> dict[str, Any]:
    check_date(body.date)
    if not body.caption.strip() and not body.images:
        raise HTTPException(400, "Paste a caption or upload a screenshot.")
    buildings = load_buildings()
    try:
        raw = gemma.extract(load_skill("event-extractor", DEFAULT_EVENT_SKILL), f"{context_block(body.date, buildings)}\n\nInstagram post:\n{body.caption.strip() or '(read the attached flyer image)'}", EVENT_SCHEMA, body.images or None)
    except gemma.GemmaError as exc:
        raise HTTPException(502, str(exc)) from exc
    events, warnings = normalize_events(raw, day=body.date, source="instagram", buildings=buildings, default_minutes=60)
    return {"events": events, "warnings": warnings}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": gemma.OLLAMA_MODEL}


@app.get("/buildings")
def buildings() -> list[dict[str, Any]]:
    return load_buildings()


@app.post("/ask")
def ask_steamline(body: AskIn) -> dict[str, str]:
    if not body.question.strip():
        raise HTTPException(400, "Ask a question.")
    day = body.date or dt.date.today().isoformat()
    lines = [f"Today is {day}. Events in order:"]
    lines.extend(
        f"- {event.get('start')}-{event.get('end')} {event.get('title')} @ {event.get('building')} ({event.get('source')})"
        for event in body.events
    )
    if len(lines) == 1:
        lines.append("(no events yet)")
    system = (
        "You are SteamLine, a campus day planner. Answer in 3 short sentences. "
        "Walking speed is 80 meters per minute, straight line. "
        "If a walk needs more minutes than the gap, say they will not make it."
    )
    try:
        answer = gemma.ask(system, "\n".join(lines) + "\n\nQuestion: " + body.question.strip())
    except gemma.GemmaError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"answer": answer}
