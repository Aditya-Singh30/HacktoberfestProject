from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BUILDINGS_PATH = ROOT / "data" / "buildings.csv"


@lru_cache(maxsize=1)
def load_buildings() -> pd.DataFrame:
    return pd.read_csv(BUILDINGS_PATH)


def building_lookup() -> dict[str, dict]:
    rows = {}
    for row in load_buildings().to_dict(orient="records"):
        rows[str(row["code"]).upper()] = row
    return rows


def known_codes() -> set[str]:
    return set(building_lookup().keys())
