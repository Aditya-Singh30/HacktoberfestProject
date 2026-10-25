from __future__ import annotations

import pandas as pd
import streamlit as st


def render_timeline(day_frame: pd.DataFrame) -> None:
    st.markdown('<div class="section-label">Today’s line</div>', unsafe_allow_html=True)
    if day_frame.empty:
        st.caption("Paste a schedule or load the sample day to fill the timeline.")
        return

    items = []
    for row in day_frame.itertuples(index=False):
        tight = bool(getattr(row, "tight", False))
        source = getattr(row, "source", "schedule")
        badge_class = "badge-ig" if source == "instagram" else "badge-class"
        badge_label = "Instagram" if source == "instagram" else "Class"
        extra = ""
        if tight:
            extra = f'<span class="badge badge-tight">Tight · {int(row.walk_min)} min walk</span>'
        items.append(
            f"""
            <div class="t-item {'tight' if tight else 'ok'}">
              <div class="t-dot"></div>
              <div class="t-time">{row.start} – {row.end}</div>
              <div class="t-title">{row.title}
                <span class="badge {badge_class}">{badge_label}</span>
                {extra}
              </div>
              <div class="t-meta">{row.building} · {row.description or source}</div>
            </div>
            """
        )
    st.markdown(f'<div class="timeline">{"".join(items)}</div>', unsafe_allow_html=True)
