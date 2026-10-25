"""Geoapify geocoding and walking routes for Purdue campus.

Used by the FastAPI backend (`/geocode`, `/route`) and as a small CLI.
"""
from __future__ import annotations

import os

import requests

API_KEY = os.getenv("GEOAPIFY_API_KEY", "0cfd16273a174c60b80a4dcd9c8b4179")
GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"
ROUTING_URL = "https://api.geoapify.com/v1/routing"
CAMPUS_BIAS = "proximity:-86.9140,40.4237"
CAMPUS_FILTER = "rect:-86.96,40.415,-86.88,40.445"


def geocode(location: str, *, campus: bool = True) -> dict:
    text = str(location or "").strip()
    if not text:
        raise ValueError("Enter a place to search.")
    if "west lafayette" not in text.lower() and "purdue" not in text.lower():
        text = f"{text}, Purdue University, West Lafayette, Indiana"

    params = {
        "text": text,
        "format": "json",
        "limit": 1,
        "bias": CAMPUS_BIAS,
        "apiKey": API_KEY,
    }
    if campus:
        params["filter"] = CAMPUS_FILTER

    response = requests.get(GEOCODING_URL, params=params, timeout=10)
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results and campus:
        params.pop("filter", None)
        response = requests.get(GEOCODING_URL, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("results") or []
    if not results:
        raise ValueError(f"Location not found: {location}")

    place = results[0]
    return {
        "name": place.get("formatted") or text,
        "lat": float(place["lat"]),
        "lon": float(place["lon"]),
    }


def _leaflet_coords(geometry: dict) -> list[list[float]]:
    kind = geometry.get("type")
    raw = geometry.get("coordinates") or []
    if kind == "LineString":
        return [[lat, lon] for lon, lat in raw]
    if kind == "MultiLineString":
        coords: list[list[float]] = []
        for line in raw:
            coords.extend([lat, lon] for lon, lat in line)
        return coords
    return []


def route_waypoints(points: list[dict]) -> dict:
    if len(points) < 2:
        raise ValueError("Need at least two waypoints for a walking route.")
    params = {
        "waypoints": "|".join(f"{point['lat']},{point['lon']}" for point in points),
        "mode": "walk",
        "format": "geojson",
        "apiKey": API_KEY,
    }
    response = requests.get(ROUTING_URL, params=params, timeout=20)
    response.raise_for_status()
    features = response.json().get("features") or []
    if not features:
        raise ValueError("Geoapify did not return a walking route.")

    route = features[0]
    props = route.get("properties") or {}
    coordinates = _leaflet_coords(route.get("geometry") or {})
    if not coordinates:
        raise ValueError("Walking route had no coordinates.")
    return {
        "coordinates": coordinates,
        "distance_m": props.get("distance"),
        "time_s": props.get("time"),
        "geojson": route,
    }


def routePlaces(start: dict, end: dict) -> dict:
    return route_waypoints([start, end])


def main() -> None:
    try:
        start = geocode(input("Enter starting location: "))
        print(f"Place found: {start['name']}")
        end = geocode(input("Enter destination: "))
        print(f"Place found: {end['name']}")
        route = routePlaces(start, end)
        print(f"Walk: {route['distance_m']} m, {route['time_s']} s, {len(route['coordinates'])} points")
    except (requests.exceptions.RequestException, ValueError, KeyError) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
