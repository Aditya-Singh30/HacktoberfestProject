from __future__ import annotations

from datetime import datetime, time
from typing import Any

import pandas as pd

from lib.buildings import known_codes
from lib.walking import walk_minutes

EVENT_COLUMNS = ["title", "source", "building", "date", "start", "end", "description"]


def empty_events() -> pd.DataFrame:
    return pd.DataFrame(columns=EVENT_COLUMNS)


def normalize_event(raw: dict[str, Any], default_date: str) -> dict[str, Any]:
    building = str(raw.get("building") or "").upper().strip()
    if building and building not in known_codes():
        building = "UNKNOWN"
    return {
        "title": str(raw.get("title") or "Untitled").strip(),
        "source": str(raw.get("source") or "manual").strip(),
        "building": building or "UNKNOWN",
        "date": str(raw.get("date") or default_date),
        "start": _as_hhmm(raw.get("start")),
        "end": _as_hhmm(raw.get("end")),
        "description": str(raw.get("description") or "").strip(),
    }


def _as_hhmm(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "00:00"
    text = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"):
        try:
            return datetime.strptime(text.upper().replace(".", ""), fmt).strftime("%H:%M")
        except ValueError:
            continue
    if isinstance(value, time):
        return value.strftime("%H:%M")
    return "00:00"


def events_for_day(frame: pd.DataFrame, day: str) -> pd.DataFrame:
    if frame.empty:
        return empty_events()
    day_frame = frame[frame["date"] == day].copy()
    if day_frame.empty:
        return empty_events()
    day_frame["_start"] = pd.to_datetime(day_frame["start"], format="%H:%M")
    day_frame["_end"] = pd.to_datetime(day_frame["end"], format="%H:%M")
    day_frame = day_frame.sort_values("_start").reset_index(drop=True)
    return day_frame


def with_gaps(day_frame: pd.DataFrame) -> pd.DataFrame:
    if day_frame.empty:
        return day_frame
    frame = day_frame.copy()
    prev_end = frame["_end"].shift(1)
    prev_building = frame["building"].shift(1)
    frame["gap_min"] = ((frame["_start"] - prev_end).dt.total_seconds() / 60).round()
    frame["prev_building"] = prev_building
    frame["walk_min"] = [
        walk_minutes(prev, cur) if pd.notna(prev) else None
        for prev, cur in zip(frame["prev_building"], frame["building"])
    ]
    frame["tight"] = frame.apply(_is_tight, axis=1)
    return frame


def _is_tight(row: pd.Series) -> bool:
    if pd.isna(row.get("gap_min")) or row.get("walk_min") is None:
        return False
    return float(row["walk_min"]) > float(row["gap_min"])


def warnings(day_frame: pd.DataFrame) -> list[str]:
    notes = []
    for row in day_frame.itertuples(index=False):
        if not getattr(row, "tight", False):
            continue
        gap = int(row.gap_min)
        walk = int(row.walk_min)
        notes.append(
            f"Tight: {gap} min gap, {walk} min walk from {row.prev_building} to {row.building} "
            f"before {row.title}."
        )
    unknown = day_frame[day_frame["building"] == "UNKNOWN"]
    for row in unknown.itertuples(index=False):
        notes.append(f"Unknown building for “{row.title}”. Use a code from buildings.csv.")
    return notes
