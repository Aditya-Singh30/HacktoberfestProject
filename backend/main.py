from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import gemma
from normalize import WEEKDAYS, normalize_events
from parse_text import parse_event_caption, parse_schedule_text

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SKILLS = ROOT / "skills"
BUILDINGS_PATH = REPO / "frontend" / "src" / "data" / "buildings.json"
_STR = {"type": "string"}
_EVENT_PROPS = {"title": _STR, "building": _STR, "location": _STR, "date": _STR, "start": _STR, "end": _STR, "description": _STR}
EVENT_SCHEMA = {"type": "object", "properties": {"events": {"type": "array", "items": {"type": "object", "properties": _EVENT_PROPS, "required": ["title"]}}}, "required": ["events"]}
SCHEDULE_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {**_EVENT_PROPS, "days": {"anyOf": [{"type": "array", "items": _STR}, _STR]}},
                "required": ["title"],
            },
        }
    },
    "required": ["events"],
}

DEFAULT_EVENT_SKILL = """You extract campus events from an Instagram caption or flyer image.
Return JSON: {"events":[{"title","building","location","date","start","end","description"}]}.
Rules: date is YYYY-MM-DD; start/end are 24-hour HH:MM; use known building codes; never invent details.
If the range is like 6:00-7:00 PM, both times are PM.
"""
DEFAULT_SCHEDULE_SKILL = """You extract class meetings from pasted registrar/Brightspace text.
Return JSON: {"events":[{"title","days","building","location","start","end","description"}]}.
Rules: days is a list from Mon,Tue,Wed,Thu,Fri; M T W R F mean Mon Tue Wed Thu Fri; times are HH:MM; never invent classes.
Keep every lecture/lab line. Recitations are OK if they have a time.
"""


def load_campus_map():
    spec = importlib.util.spec_from_file_location("campus_map", REPO / "map.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("map.py is missing")
    module = importlib.util.module_from_spec(spec)
    sys.modules["campus_map"] = module
    spec.loader.exec_module(module)
    return module


campus_map = load_campus_map()


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


def render_skill(name: str, default: str, day: str, buildings: list[dict[str, Any]]) -> str:
    parsed = dt.date.fromisoformat(day)
    codes = ", ".join(f"{building['code']} ({building.get('name', '')})" for building in buildings) or "(none loaded)"
    return (
        load_skill(name, default)
        .replace("{{BUILDINGS}}", codes)
        .replace("{{DATE}}", day)
        .replace("{{WEEKDAY}}", WEEKDAYS[parsed.weekday()])
    )


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


class GeocodeIn(BaseModel):
    text: str
    campus: bool = True


class Waypoint(BaseModel):
    lat: float
    lon: float
    name: str | None = None


class RouteIn(BaseModel):
    waypoints: list[Waypoint] = Field(default_factory=list)


def check_date(day: str) -> dt.date:
    try:
        return dt.date.fromisoformat(day)
    except ValueError as exc:
        raise HTTPException(422, f"Bad date '{day}'. Use YYYY-MM-DD.") from exc


def extract_or_parse(*, skill: str, user_text: str, schema: dict[str, Any], images: list[str] | None, fallback: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    notes: list[str] = []
    raw: dict[str, Any] | None = None
    try:
        raw = gemma.extract(skill, user_text, schema, images)
    except gemma.GemmaError as exc:
        notes.append(str(exc))
        if images and not (fallback.get("events") or []):
            raise HTTPException(502, str(exc)) from exc
        notes.append("Used the local parser because Gemma was unavailable.")
        return fallback, notes
    if not isinstance(raw, dict) or not raw.get("events"):
        notes.append("Gemma returned no events; used the local parser.")
        return fallback if fallback.get("events") else raw or fallback, notes
    return raw, notes


def finish_events(raw: dict[str, Any], *, day: str, source: str, buildings: list[dict[str, Any]], default_minutes: int, weekday: str | None) -> tuple[list[dict[str, Any]], list[str]]:
    events, warnings = normalize_events(raw, day=day, source=source, buildings=buildings, default_minutes=default_minutes, weekday_filter=weekday)
    if weekday and not events:
        all_events, extra = normalize_events(raw, day=day, source=source, buildings=buildings, default_minutes=default_minutes, weekday_filter=None)
        warnings.extend(extra)
        if all_events:
            warnings.append(f"None of these classes meet on {weekday}. Showing every extracted meeting so you can review them.")
            events = all_events
    return events, warnings


app = FastAPI(title="SteamLine")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])


@app.post("/extract/schedule")
def extract_schedule(body: ScheduleIn) -> dict[str, Any]:
    parsed_day = check_date(body.date)
    if not body.text.strip():
        raise HTTPException(400, "Paste your schedule text first.")
    buildings = load_buildings()
    fallback = parse_schedule_text(body.text)
    raw, notes = extract_or_parse(
        skill=render_skill("schedule-extractor", DEFAULT_SCHEDULE_SKILL, body.date, buildings),
        user_text=f"{context_block(body.date, buildings)}\n\nSchedule text:\n{body.text}",
        schema=SCHEDULE_SCHEMA,
        images=None,
        fallback=fallback,
    )
    if notes and "local parser" in " ".join(notes).lower() and fallback.get("events"):
        raw = fallback
    weekday = WEEKDAYS[parsed_day.weekday()] if parsed_day.weekday() < 5 else None
    if weekday is None:
        notes.append("Weekend date — showing every extracted meeting. Switch to a weekday to keep only classes that meet that day.")
    events, warnings = finish_events(raw, day=body.date, source="schedule", buildings=buildings, default_minutes=50, weekday=weekday)
    if not events and fallback.get("events"):
        events, warnings = finish_events(fallback, day=body.date, source="schedule", buildings=buildings, default_minutes=50, weekday=weekday)
        notes.append("Gemma's JSON did not map to classes; used the local parser.")
    return {"events": events, "warnings": notes + warnings}


@app.post("/extract/event")
def extract_event(body: EventIn) -> dict[str, Any]:
    check_date(body.date)
    if not body.caption.strip() and not body.images:
        raise HTTPException(400, "Paste a caption or upload a screenshot.")
    buildings = load_buildings()
    fallback = parse_event_caption(body.caption, body.date)
    raw, notes = extract_or_parse(
        skill=render_skill("event-extractor", DEFAULT_EVENT_SKILL, body.date, buildings),
        user_text=f"{context_block(body.date, buildings)}\n\nInstagram post:\n{body.caption.strip() or '(read the attached flyer image)'}",
        schema=EVENT_SCHEMA,
        images=body.images or None,
        fallback=fallback,
    )
    if notes and "local parser" in " ".join(notes).lower() and fallback.get("events"):
        raw = fallback
    events, warnings = finish_events(raw, day=body.date, source="instagram", buildings=buildings, default_minutes=60, weekday=None)
    if not events and fallback.get("events"):
        events, warnings = finish_events(fallback, day=body.date, source="instagram", buildings=buildings, default_minutes=60, weekday=None)
        notes.append("Gemma's JSON did not map to an event; used the local parser.")
    return {"events": events, "warnings": notes + warnings}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": gemma.OLLAMA_MODEL}


@app.get("/buildings")
def buildings() -> list[dict[str, Any]]:
    return load_buildings()


def known_place(text: str, buildings: list[dict[str, Any]]) -> dict[str, Any] | None:
    needle = text.strip().lower()
    if not needle:
        return None
    for building in buildings:
        code = str(building.get("code", ""))
        name = str(building.get("name", ""))
        hay = f"{code} {name}".lower()
        if needle == code.lower() or needle == name.lower() or needle in hay or code.lower() in needle.split() or name.lower() in needle:
            return {"name": f"{name} ({code})" if name else code, "lat": building["lat"], "lon": building["lon"]}
    return None


@app.post("/geocode")
def geocode_place(body: GeocodeIn) -> dict[str, Any]:
    if not body.text.strip():
        raise HTTPException(400, "Enter a place to search.")
    local = known_place(body.text, load_buildings())
    if local:
        return local
    try:
        return campus_map.geocode(body.text, campus=body.campus)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Geocoding failed: {exc}") from exc


@app.post("/route")
def walking_route(body: RouteIn) -> dict[str, Any]:
    if len(body.waypoints) < 2:
        raise HTTPException(400, "Need at least two waypoints.")
    points = [point.model_dump() for point in body.waypoints]
    try:
        return campus_map.route_waypoints(points)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Routing failed: {exc}") from exc


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
