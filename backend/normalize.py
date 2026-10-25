"""Turn Gemma output into clean, UI-ready events."""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

DAY_ALIASES = {
    "m": "Mon", "mon": "Mon", "monday": "Mon",
    "t": "Tue", "tu": "Tue", "tue": "Tue", "tues": "Tue", "tuesday": "Tue",
    "w": "Wed", "wed": "Wed", "wednesday": "Wed",
    "r": "Thu", "th": "Thu", "thu": "Thu", "thur": "Thu", "thurs": "Thu", "thursday": "Thu",
    "f": "Fri", "fri": "Fri", "friday": "Fri",
    "sat": "Sat", "sa": "Sat", "saturday": "Sat", "sun": "Sun", "su": "Sun", "sunday": "Sun",
}
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_MONTHS = {name: index for index, name in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_MERIDIEM = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m?\.?", re.I)
_H24 = re.compile(r"(\d{1,2}):(\d{2})")
_BARE_HOUR = re.compile(r"^\s*(\d{1,2})\s*$")
_FUZZY_DATE = re.compile(
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s*((?:19|20)\d{2}))?",
    re.I,
)


def to_hhmm(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = _MERIDIEM.search(text)
    if match:
        hour, minute = int(match.group(1)), int(match.group(2) or 0)
        pm = match.group(3).lower() == "p"
        hour = 12 if hour == 12 and pm else 0 if hour == 12 else hour + 12 if pm else hour
    else:
        match = _H24.search(text) or _BARE_HOUR.match(text)
        if not match:
            return None
        hour, minute = int(match.group(1)), int(match.group(2) if match.lastindex == 2 else 0)
        if 1 <= hour <= 6:
            hour += 12
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return f"{hour:02d}:{minute:02d}"


def pair_times(start_raw: Any, end_raw: Any) -> tuple[str | None, str | None]:
    start_s, end_s = str(start_raw or "").strip(), str(end_raw or "").strip()
    if re.search(r"[p]\.?\s*m", end_s, re.I) and not re.search(r"[ap]\.?\s*m", start_s, re.I):
        start_s = f"{start_s} PM"
    elif re.search(r"[a]\.?\s*m", end_s, re.I) and not re.search(r"[ap]\.?\s*m", start_s, re.I):
        start_s = f"{start_s} AM"
    return to_hhmm(start_s), to_hhmm(end_s)


def _add_minutes(hhmm: str, minutes: int) -> str:
    hour, minute = map(int, hhmm.split(":"))
    total = min(hour * 60 + minute + minutes, 23 * 60 + 59)
    return f"{total // 60:02d}:{total % 60:02d}"


def to_iso_date(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = dt.date.fromisoformat(text[:10])
        base = dt.date.fromisoformat(fallback)
        if abs((parsed - base).days) <= 370:
            return parsed.isoformat()
    except (ValueError, TypeError):
        pass
    match = _FUZZY_DATE.search(text)
    if match:
        month = _MONTHS[match.group(1)[:3].lower()]
        year = int(match.group(3) or fallback[:4])
        try:
            return dt.date(year, month, int(match.group(2))).isoformat()
        except ValueError:
            pass
    if re.search(r"\b(tonight|today)\b", text, re.I):
        return fallback
    if re.search(r"\btomorrow\b", text, re.I):
        try:
            return (dt.date.fromisoformat(fallback) + dt.timedelta(days=1)).isoformat()
        except ValueError:
            return fallback
    return fallback


def normalize_days(value: Any) -> list[str]:
    if isinstance(value, str):
        compact = re.sub(r"[^A-Za-z]", "", value)
        if compact.lower() in {"tth", "tr", "tuth"}:
            values = ["Tue", "Thu"]
        else:
            values = re.split(r"[,/ \-]+", value)
    else:
        values = value or []
    output: list[str] = []
    for item in values:
        key = str(item).strip().lower().rstrip(".")
        if key in {"tu", "tue", "tues", "tuesday"}:
            output.append("Tue")
            continue
        if key in DAY_ALIASES:
            output.append(DAY_ALIASES[key])
        elif len(key) > 1 and all(char in "mtwrf" for char in key):
            output.extend(DAY_ALIASES[char] for char in key)
    return list(dict.fromkeys(output))


def match_building(value: Any, buildings: list[dict[str, Any]]) -> str:
    text = str(value or "").strip()
    if not buildings:
        return text.upper() if text else "unknown"
    upper = text.upper()
    for building in buildings:
        code = str(building.get("code", ""))
        if upper == code.upper() or re.search(rf"\b{re.escape(code.upper())}\b", upper):
            return code
    lower = text.lower()
    for building in buildings:
        name = str(building.get("name", "")).lower()
        if lower and name and (lower in name or name in lower):
            return building["code"]
    aliases = (("lawson", "LWSN"), ("beering", "BRNG"), ("armstrong", "ARMS"), ("stewart", "STEW"), ("memorial union", "PMU"), ("wilmeth", "WALC"))
    for needle, code in aliases:
        if needle in lower:
            return code
    return "unknown"


def normalize_events(raw: dict[str, Any], *, day: str, source: str, buildings: list[dict[str, Any]], default_minutes: int, weekday_filter: str | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    items = raw.get("events") if isinstance(raw, dict) else None
    if not isinstance(items, list):
        return [], ["Extractor returned no 'events' list."]
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        days = normalize_days(item.get("days"))
        if weekday_filter and days and weekday_filter not in days:
            continue
        start, end = pair_times(item.get("start"), item.get("end"))
        if not start:
            warnings.append(f"Skipped '{title}': no readable start time.")
            continue
        if not end or end <= start:
            end = _add_minutes(start, default_minutes)
        location = str(item.get("location") or item.get("building") or "").strip()
        description = str(item.get("description") or location).strip()
        events.append({
            "title": title,
            "source": source,
            "building": match_building(item.get("building") or location, buildings),
            "location": location,
            "description": description,
            "date": day if weekday_filter else to_iso_date(item.get("date"), day),
            "start": start,
            "end": end,
            "days": days,
        })
    events.sort(key=lambda event: (event["date"], event["start"]))
    return events, warnings
