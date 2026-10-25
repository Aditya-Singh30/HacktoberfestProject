from unittest import mock

from fastapi.testclient import TestClient

import gemma
import main

client = TestClient(main.app)
main.load_buildings = lambda: [
    {"code": "BRNG", "name": "Beering Hall"},
    {"code": "LWSN", "name": "Lawson Computer Science Building"},
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
    assert client.post("/extract/schedule", json={"text": "x", "date": "2026-10-25"}).json()["events"] == []

assert client.post("/extract/event", json={"caption": "", "date": "2026-10-27", "images": []}).status_code == 400
with mock.patch.object(gemma, "extract", side_effect=gemma.GemmaError("Cannot reach Ollama")):
    assert client.post("/extract/event", json={"caption": "x", "date": "2026-10-27"}).status_code == 502

assert gemma._parse_json('Sure!\n```json\n{"events":[{"title":"a","start":"1"}]}\n```')["events"]
print("attached fix regression checks passed")
