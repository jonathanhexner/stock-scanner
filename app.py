"""Value-investing workbench. Run with: streamlit run app.py"""

from __future__ import annotations

import streamlit as st

from src.ask import providers  # noqa: F401  (registers the built-in providers)
from src.ask.context import AskContext
from src.ask.panel import agents, ask_panel
from src.store import db
from src.ui import bootstrap, page_header, sidebar_portfolios

st.set_page_config(page_title="Workbench", page_icon="📓", layout="wide")
bootstrap()

selected = sidebar_portfolios()
page_header("Workbench", "Learn it, find it, write down why, then find out.")

st.markdown(
    """
This is a place to **think in writing about businesses**, not a place to be told
what to buy. The screener is the least important part of it.

The loop it exists to support:

1. **Learn** a concept, then try it on a real company.
2. **Scan** for something worth reading about.
3. Write a **thesis** — why it's cheap, and what would prove you wrong.
4. **Track** it, and find out whether you were right for the reason you thought.

Every page has an *Ask* panel. The **Chat** page lets you pick the agent and
exactly what it can see.
"""
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Your portfolios")
    with db.connect() as conn:
        for portfolio in db.list_portfolios(conn):
            rows = db.holdings(conn, portfolio.id)
            st.write(f"**{portfolio.name}** ({portfolio.kind}) — {len(rows)} holdings")
            st.caption(portfolio.notes)

with col2:
    st.subheader("Agents")
    for agent in agents().values():
        st.write(f"**{agent.name}** — {agent.description}")

st.divider()
ask_panel(
    "home",
    AskContext(title="value investing"),
    agent_id="tutor",
)
