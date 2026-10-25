"""Deterministic extractors used when Gemma is down or returns nothing."""
from __future__ import annotations

import re
from typing import Any

COURSE_TITLE = re.compile(r"^[A-Z]{2,6}\s+\d{3,5}[A-Z0-9]?\b.*$")
MEETING = re.compile(
    r"(?:(?P<kind>Lecture|Lab|Recitation|Studio|Prelab|PSO|Discussion)\s+)?"
    r"(?P<building>[A-Z]{2,6})\s+(?P<room>[A-Z]?\d[\w-]*)\s+"
    r"(?P<days>(?:Tu|Th|Sa|Su|[MTWRF])+)\s+"
    r"(?P<start>\d{1,2}(?::\d{2})?\s*(?:[AaPp]\.?\s*[Mm]\.?)?)\s*"
    r"[–\-to]+\s*"
    r"(?P<end>\d{1,2}(?::\d{2})?\s*(?:[AaPp]\.?\s*[Mm]\.?)?)",
    re.I,
)
INLINE = re.compile(
    r"(?P<title>[A-Z]{2,6}\s+\d{3,5}[A-Z0-9]?(?:[^\n|]*?))?\s*[|\-]+\s*"
    r"(?P<days>(?:Tu|Th|[MTWRF])+)\s*[|\-]+\s*"
    r"(?P<start>\d{1,2}(?::\d{2})?\s*(?:[AaPp]\.?\s*[Mm]\.?)?)\s*"
    r"[–\-]\s*"
    r"(?P<end>\d{1,2}(?::\d{2})?\s*(?:[AaPp]\.?\s*[Mm]\.?)?)\s*[|\-]+\s*"
    r"(?P<building>[A-Z]{2,6})(?:\s+(?P<room>[\w-]+))?",
    re.I,
)
TIME_RANGE = re.compile(
    r"(?P<start>\d{1,2}(?::\d{2})?\s*(?:[AaPp]\.?\s*[Mm]\.?)?)\s*[–\-]\s*"
    r"(?P<end>\d{1,2}(?::\d{2})?\s*(?:[AaPp]\.?\s*[Mm]\.?)?)",
    re.I,
)
SINGLE_TIME = re.compile(r"\b(\d{1,2}(?::\d{2})?\s*[AaPp]\.?\s*[Mm]\.?)\b")
CODE = re.compile(r"\b([A-Z]{2,6})\s+\d")
HANDLE = re.compile(r"^@?[A-Za-z0-9._]{3,30}$")


def parse_schedule_text(text: str) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    title = ""
    for raw_line in text.splitlines():
        line = raw_line.strip().replace("\u00a0", " ")
        if not line:
            continue
        inline = INLINE.search(line)
        if inline and inline.group("days") and inline.group("start"):
            events.append(
                {
                    "title": (inline.group("title") or title or "Class").strip(" -|"),
                    "days": inline.group("days"),
                    "building": inline.group("building").upper(),
                    "location": " ".join(part for part in [inline.group("building"), inline.group("room")] if part),
                    "start": inline.group("start"),
                    "end": inline.group("end"),
                    "description": line,
                }
            )
            continue
        if COURSE_TITLE.match(line) and MEETING.search(line) is None:
            title = line
            continue
        meeting = MEETING.search(line)
        if meeting and title:
            kind = (meeting.group("kind") or "Class").title()
            building = meeting.group("building").upper()
            room = meeting.group("room")
            events.append(
                {
                    "title": title,
                    "days": meeting.group("days"),
                    "building": building,
                    "location": f"{building} {room}",
                    "start": meeting.group("start"),
                    "end": meeting.group("end"),
                    "description": f"{kind} · {building} {room}",
                }
            )
    return {"events": events}


def parse_event_caption(caption: str, day: str) -> dict[str, Any]:
    text = (caption or "").strip()
    if not text:
        return {"events": []}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = next((line for line in lines if not HANDLE.match(line) and not re.match(r"^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", line, re.I)), lines[0])
    title = re.sub(r"[\U00010000-\U0010ffff]", "", title).strip(" ·-|")
    start = end = None
    ranged = TIME_RANGE.search(text)
    if ranged:
        start, end = ranged.group("start"), ranged.group("end")
    else:
        found = SINGLE_TIME.search(text)
        if found:
            start = found.group(1)
    code = None
    code_match = CODE.search(text)
    if code_match:
        code = code_match.group(1)
    location = ""
    for line in lines:
        if code and code in line:
            location = line
            break
        if re.search(r"\b(hall|union|center|building|lawson|beering|stewart)\b", line, re.I):
            location = line
    if not start:
        return {"events": []}
    return {
        "events": [
            {
                "title": title or "Campus event",
                "building": code or location,
                "location": location or code or "",
                "date": text,
                "start": start,
                "end": end or "",
                "description": next((line for line in lines if "snack" in line.lower() or "welcome" in line.lower() or "free" in line.lower()), location),
            }
        ]
    }
