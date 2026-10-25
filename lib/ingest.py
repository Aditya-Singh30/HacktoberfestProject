from __future__ import annotations

import csv
import io
from datetime import date

import pandas as pd

from lib.events import normalize_event

SAMPLE_SCHEDULE_EVENTS = [
    {
        "title": "CS 25100 Data Structures",
        "source": "schedule",
        "building": "LWSN",
        "start": "08:30",
        "end": "09:20",
        "description": "Lecture · LWSN B155",
    },
    {
        "title": "PHYS 17200 Modern Mechanics",
        "source": "schedule",
        "building": "PHYS",
        "start": "09:30",
        "end": "10:20",
        "description": "Lecture · PHYS 112",
    },
    {
        "title": "ENGR 13100 Innovation Lab",
        "source": "schedule",
        "building": "ARMS",
        "start": "10:30",
        "end": "11:20",
        "description": "Lab · ARMS 1028",
    },
    {
        "title": "COM 11400 Speech",
        "source": "schedule",
        "building": "BRNG",
        "start": "11:30",
        "end": "12:20",
        "description": "Lecture · BRNG 2280",
    },
    {
        "title": "MA 26100 Multivariate Calculus",
        "source": "schedule",
        "building": "MATH",
        "start": "13:30",
        "end": "14:20",
        "description": "Lecture · MATH 175",
    },
]

SAMPLE_INSTAGRAM_EVENT = {
    "title": "Hack Club Meeting",
    "source": "instagram",
    "building": "BRNG",
    "start": "18:00",
    "end": "19:00",
    "description": "Build, hang out, and ship something small. Free snacks.",
}


def sample_day_events(day: str) -> list[dict]:
    events = [{**item, "date": day} for item in SAMPLE_SCHEDULE_EVENTS]
    events.append({**SAMPLE_INSTAGRAM_EVENT, "date": day})
    return [normalize_event(item, day) for item in events]


def parse_csv(file_bytes: bytes, day: str) -> list[dict]:
    text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    events = []
    for row in reader:
        events.append(normalize_event({**row, "source": row.get("source") or "csv"}, day))
    return events


def dataframe_from_events(events: list[dict]) -> pd.DataFrame:
    if not events:
        return pd.DataFrame()
    return pd.DataFrame(events)


def today_iso() -> str:
    return date.today().isoformat()
