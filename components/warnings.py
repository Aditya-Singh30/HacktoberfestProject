from __future__ import annotations

import streamlit as st


def render_warnings(notes: list[str]) -> None:
    if not notes:
        st.markdown(
            '<div class="ok-card">Gaps look walkable for this day. No tight transfers.</div>',
            unsafe_allow_html=True,
        )
        return
    for note in notes:
        st.markdown(f'<div class="warning-card"><strong>{note}</strong></div>', unsafe_allow_html=True)
