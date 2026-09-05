"""Learn — the course. Phase 2 fills in the lessons."""

from __future__ import annotations

import streamlit as st

from src.ask import providers
from src.ask.context import AskContext
from src.ask.panel import ask_panel
from src.ui import bootstrap, not_built_yet, page_header, sidebar_portfolios

st.set_page_config(page_title="Learn", page_icon="📚", layout="wide")
bootstrap()
sidebar_portfolios()
page_header("Learn", "One concept at a time, then try it on a real company.")

not_built_yet(2, "Curated lessons, each ending in a 'try it on a real ticker' exercise.")

terms = providers.load_glossary()
st.subheader(f"Glossary ({len(terms)} terms)")
query = st.text_input("Filter", placeholder="e.g. owner earnings")
for term, meaning in sorted(terms.items()):
    if query.lower() in term.lower() or query.lower() in meaning.lower():
        st.markdown(f"**{term}** — {meaning}")

context = AskContext(title="the glossary")
block = providers.build("glossary", {})
if block:
    context.add(block)

st.divider()
ask_panel("learn", context, agent_id="tutor")
