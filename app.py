from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from components.map_view import render_map
from components.timeline import render_timeline
from components.warnings import render_warnings
from lib.events import empty_events, events_for_day, with_gaps, warnings
from lib.ingest import parse_csv, sample_day_events

ROOT = Path(__file__).resolve().parent
SAMPLE_SCHEDULE = (ROOT / "data" / "sample_schedule.txt").read_text()
SAMPLE_INSTAGRAM = (ROOT / "data" / "sample_instagram.txt").read_text()

st.set_page_config(page_title="SteamLine · Today’s Line", page_icon="🟠", layout="wide")
st.markdown(f"<style>{(ROOT / 'assets' / 'styles.css').read_text()}</style>", unsafe_allow_html=True)

def append_events(rows: list[dict]) -> None:
    added = pd.DataFrame(rows)
    current = st.session_state.events
    st.session_state.events = pd.concat([current, added], ignore_index=True)


if "events" not in st.session_state:
    st.session_state.events = pd.DataFrame(sample_day_events("2026-10-27"))

with st.sidebar:
    st.markdown("### SteamLine")
    st.caption("Today’s Line · hackathon demo")
    selected_day = st.date_input("Day", value=date(2026, 10, 27)).isoformat()

    st.markdown("#### Add schedule")
    schedule_text = st.text_area(
        "Paste Brightspace / registrar text",
        value=SAMPLE_SCHEDULE,
        height=180,
        label_visibility="collapsed",
    )
    csv_file = st.file_uploader("Or upload a CSV", type=["csv"])
    if st.button("Add schedule to timeline", use_container_width=True):
        if csv_file is not None:
            new_rows = parse_csv(csv_file.getvalue(), selected_day)
        else:
            # Front-end stub: sample parser until Gemma + schedule-extractor lands.
            new_rows = [
                row for row in sample_day_events(selected_day) if row["source"] == "schedule"
            ]
            st.session_state["_last_schedule_paste"] = schedule_text
        append_events(new_rows)
        st.success(f"Added {len(new_rows)} class stops.")

    st.markdown("#### Add Instagram event")
    ig_text = st.text_area(
        "Paste caption",
        value=SAMPLE_INSTAGRAM,
        height=140,
        label_visibility="collapsed",
    )
    screenshot = st.file_uploader("Or upload a flyer screenshot", type=["png", "jpg", "jpeg"])
    if st.button("Add event to timeline", use_container_width=True):
        new_rows = [
            row for row in sample_day_events(selected_day) if row["source"] == "instagram"
        ]
        st.session_state["_last_ig_paste"] = ig_text
        st.session_state["_has_screenshot"] = screenshot is not None
        append_events(new_rows)
        st.success("Added Instagram event. Extractor wiring comes next.")

    if st.button("Load sample day", use_container_width=True):
        st.session_state.events = pd.DataFrame(sample_day_events(selected_day))
        st.rerun()

    if st.button("Clear day", use_container_width=True):
        st.session_state.events = empty_events()
        st.rerun()

st.markdown(
    f"""
    <div class="hero">
      <div>
        <div class="hero-kicker">SteamLine · Purdue</div>
        <h1>Today’s <span>Line</span></h1>
        <p>Classes and club posts on one timeline and map. Tight walking gaps get flagged before you try to make them.</p>
      </div>
      <div class="chip">{selected_day}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

day_frame = with_gaps(events_for_day(st.session_state.events, selected_day))
render_warnings(warnings(day_frame))

left, right = st.columns((1.05, 1), gap="large")
with left:
    render_timeline(day_frame)
with right:
    render_map(day_frame)
    if not day_frame.empty:
        show = day_frame.drop(columns=["_start", "_end"], errors="ignore")
        st.dataframe(show, use_container_width=True, hide_index=True)
