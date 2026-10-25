from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
TIMEOUT_S = int(os.getenv("OLLAMA_TIMEOUT", "180"))
OPTIONS = {"temperature": 0, "num_ctx": 4096}


class GemmaError(RuntimeError):
    pass


def extract(skill: str, user_text: str, schema: dict[str, Any], images: list[str] | None = None) -> dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(2):
        try:
            return _chat(skill, user_text, schema, images)
        except GemmaError as exc:
            last_error = exc
            if "Cannot reach Ollama" in str(exc):
                break
    raise GemmaError(str(last_error))


def ask(system: str, user_text: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "think": False,
        "options": OPTIONS,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user_text}],
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_S)
        response.raise_for_status()
        return str(response.json().get("message", {}).get("content") or "").strip()
    except requests.RequestException as exc:
        raise GemmaError(_friendly(exc, getattr(exc, "response", None))) from exc


def _chat(skill: str, user_text: str, schema: dict[str, Any], images: list[str] | None) -> dict[str, Any]:
    msg: dict[str, Any] = {"role": "user", "content": user_text}
    if images:
        msg["images"] = images
    payload: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "think": False,
        "format": schema,
        "options": OPTIONS,
        "messages": [{"role": "system", "content": skill}, msg],
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_S)
        if response.status_code >= 400 and "format" in response.text.lower():
            payload.pop("format")
            payload["messages"][0]["content"] += "\nReturn ONLY a valid JSON object with an 'events' list. No prose, no code fences."
            response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_S)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise GemmaError(_friendly(exc, getattr(exc, "response", None))) from exc

    message = data.get("message", {})
    content = message.get("content") or message.get("thinking") or ""
    if not content.strip():
        raise GemmaError("Gemma returned an empty response.")
    return _parse_json(content)


def _parse_json(content: str) -> dict[str, Any]:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise GemmaError("Gemma did not return valid JSON.") from None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise GemmaError("Gemma did not return valid JSON.") from exc
    if isinstance(parsed, str):
        parsed = json.loads(parsed)
    if isinstance(parsed, list):
        parsed = {"events": parsed}
    if not isinstance(parsed, dict):
        raise GemmaError("Gemma JSON was not an object.")
    return parsed


def _friendly(exc: Exception, response: requests.Response | None = None) -> str:
    text = str(exc)
    if "Failed to establish a new connection" in text or "Connection refused" in text:
        return f"Cannot reach Ollama at {OLLAMA_URL}. Start it with `ollama serve` and pull the model (`ollama pull gemma4:e4b`, or set OLLAMA_MODEL=gemma4:e2b)."
    if response is not None:
        body = response.text[:300]
        if response.status_code == 404 and "not found" in body.lower():
            return f"Model '{OLLAMA_MODEL}' isn't pulled yet. Run: ollama pull {OLLAMA_MODEL}"
        return f"Ollama error {response.status_code}: {body}"
    if "timed out" in text.lower():
        return "Gemma timed out. First request loads the model; try again, or use gemma4:e2b."
    return text
