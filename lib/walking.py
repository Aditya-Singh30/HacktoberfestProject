from __future__ import annotations

import math

from lib.buildings import building_lookup

WALK_M_PER_MIN = 55  # campus walk with lights and crowds


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def walk_minutes(code_a: str, code_b: str) -> int | None:
    buildings = building_lookup()
    a = buildings.get((code_a or "").upper())
    b = buildings.get((code_b or "").upper())
    if not a or not b:
        return None
    if a["code"] == b["code"]:
        return 2
    meters = haversine_m(a["lat"], a["lon"], b["lat"], b["lon"])
    return max(2, round(meters / WALK_M_PER_MIN))
