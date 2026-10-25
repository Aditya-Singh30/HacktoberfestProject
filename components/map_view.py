from __future__ import annotations

import os

import pandas as pd
import pydeck as pdk
import streamlit as st

from lib.buildings import building_lookup

CAMPUS_LAT = 40.4265
CAMPUS_LON = -86.9135


def _map_style() -> str:
    key = os.environ.get("GEOAPIFY_API_KEY", "")
    if key:
        return f"https://maps.geoapify.com/v1/styles/dark-matter/style.json?apiKey={key}"
    return "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"


def render_map(day_frame: pd.DataFrame) -> None:
    st.markdown('<div class="section-label">Campus route</div>', unsafe_allow_html=True)
    buildings = building_lookup()
    pins = []
    path = []
    for i, row in enumerate(day_frame.itertuples(index=False), start=1):
        info = buildings.get(str(row.building).upper())
        if not info:
            continue
        pins.append(
            {
                "lat": info["lat"],
                "lon": info["lon"],
                "title": f"{i}. {row.title}",
                "when": f"{row.start}–{row.end}",
                "building": row.building,
                "stop": str(i),
            }
        )
        path.append([info["lon"], info["lat"]])

    layers = []
    if path:
        layers.append(
            pdk.Layer(
                "PathLayer",
                data=[{"path": path}],
                get_path="path",
                get_color=[232, 93, 4],
                width_scale=1,
                width_min_pixels=4,
            )
        )
    if pins:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=pins,
                get_position="[lon, lat]",
                get_fill_color=[244, 140, 6],
                get_radius=45,
                radius_min_pixels=8,
                pickable=True,
            )
        )
        layers.append(
            pdk.Layer(
                "TextLayer",
                data=pins,
                get_position="[lon, lat]",
                get_text="stop",
                get_size=14,
                get_color=[26, 20, 16],
                get_alignment_baseline="center",
            )
        )

    deck = pdk.Deck(
        map_style=_map_style(),
        initial_view_state=pdk.ViewState(
            latitude=CAMPUS_LAT,
            longitude=CAMPUS_LON,
            zoom=15,
            pitch=35,
        ),
        layers=layers,
        tooltip={"text": "{title}\n{building} {when}"},
    )
    st.pydeck_chart(deck, use_container_width=True)
    if not pins:
        st.caption("No mapped buildings yet. Unknown codes stay off the map.")
    elif not os.environ.get("GEOAPIFY_API_KEY"):
        st.caption("Map uses a dark basemap. Set GEOAPIFY_API_KEY to switch to Geoapify tiles.")
