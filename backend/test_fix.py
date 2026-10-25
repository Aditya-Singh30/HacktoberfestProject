from unittest import mock

from fastapi.testclient import TestClient

import gemma
import main
from normalize import pair_times, to_hhmm, to_iso_date
from parse_text import parse_event_caption, parse_schedule_text

client = TestClient(main.app)
main.load_buildings = lambda: [
    {"code": "BRNG", "name": "Beering Hall"},
    {"code": "LWSN", "name": "Lawson Computer Science Building"},
    {"code": "PHYS", "name": "Physics Building"},
    {"code": "ARMS", "name": "Armstrong Hall"},
    {"code": "MATH", "name": "Mathematical Sciences Building"},
]

raw_event = {"events": [
    {"title": "Hack Club Meeting", "building": "Lawson Computer Science Building", "date": "2024-03-01", "start": "6 PM", "end": ""},
    {"title": "Free pizza", "building": "Room B222, BRNG", "date": "2026-10-29", "start": "6:30pm", "end": "7:15 PM"},
    {"title": "No time event", "start": "soon"},
    "garbage",
]}
with mock.patch.object(gemma, "extract", return_value=raw_event):
    response = client.post("/extract/event", json={"caption": "x", "date": "2026-10-27", "images": []})
assert response.status_code == 200
assert response.json()["events"][0]["start"] == "18:00"

raw_schedule = {"events": [
    {"title": "CS 18000", "days": ["M", "W", "F"], "building": "LWSN", "start": "10:30 AM", "end": "11:20 AM"},
    {"title": "MA 26100", "days": ["TR"], "building": "BRNG", "start": "1:30", "end": "2:45 PM"},
]}
with mock.patch.object(gemma, "extract", return_value=raw_schedule):
    assert len(client.post("/extract/schedule", json={"text": "x", "date": "2026-10-26"}).json()["events"]) == 1
    assert len(client.post("/extract/schedule", json={"text": "x", "date": "2026-10-27"}).json()["events"]) == 1
    sunday = client.post("/extract/schedule", json={"text": "x", "date": "2026-10-25"}).json()
    assert len(sunday["events"]) == 2
    assert any("weekend" in note.lower() or "review" in note.lower() for note in sunday["warnings"])

assert client.post("/extract/event", json={"caption": "", "date": "2026-10-27", "images": []}).status_code == 400

sample = """CS 25100 Data Structures and Algorithms
Lecture  LWSN B155  MWF  8:30 AM – 9:20 AM

PHYS 17200 Modern Mechanics
Lecture  PHYS 112  MWF  9:30 AM – 10:20 AM

ENGR 13100 Transforming Ideas to Innovation
Lab  ARMS 1028  MW  10:30 AM – 11:20 AM
"""
with mock.patch.object(gemma, "extract", side_effect=gemma.GemmaError("Cannot reach Ollama")):
    fallback = client.post("/extract/schedule", json={"text": sample, "date": "2026-10-26"})
assert fallback.status_code == 200
assert len(fallback.json()["events"]) == 3
assert fallback.json()["events"][0]["start"] == "08:30"

caption = """hackclubpurdue
Oct 26
Hack Club Meeting tonight
Monday Oct 26 · 6:00–7:00 PM
Beering Hall BRNG 1268
Free snacks. All majors welcome.
"""
with mock.patch.object(gemma, "extract", side_effect=gemma.GemmaError("Cannot reach Ollama")):
    event_resp = client.post("/extract/event", json={"caption": caption, "date": "2026-10-26"})
assert event_resp.status_code == 200
got = event_resp.json()["events"][0]
assert got["start"] == "18:00"
assert got["end"] == "19:00"
assert got["building"] == "BRNG"

assert pair_times("8:00", "9:00 PM") == ("20:00", "21:00")
assert to_hhmm("11:24 AM") == "11:24"
assert to_iso_date("Oct 26", "2026-10-25") == "2026-10-26"
assert len(parse_schedule_text(sample)["events"]) == 3
assert parse_event_caption(caption, "2026-10-26")["events"][0]["title"].startswith("Hack Club")

with mock.patch.object(main.campus_map, "geocode", return_value={"name": "Lawson", "lat": 40.42, "lon": -86.91}):
    geo = client.post("/geocode", json={"text": "Lawson"})
assert geo.status_code == 200
assert geo.json()["lat"] == 40.42

with mock.patch.object(main.campus_map, "route_waypoints", return_value={"coordinates": [[40.42, -86.91], [40.43, -86.92]], "distance_m": 400, "time_s": 300}):
    routed = client.post("/route", json={"waypoints": [{"lat": 40.42, "lon": -86.91}, {"lat": 40.43, "lon": -86.92}]})
assert routed.status_code == 200
assert len(routed.json()["coordinates"]) == 2

assert gemma._parse_json('Sure!\n```json\n{"events":[{"title":"a","start":"1"}]}\n```')["events"]
print("attached fix regression checks passed")
