"""Journal — the core of the product. Phase 3."""

from __future__ import annotations

import streamlit as st

from src.ask import providers  # noqa: F401
from src.ask.context import AskContext
from src.ask.panel import ask_panel
from src.ui import bootstrap, not_built_yet, page_header, sidebar_portfolios

st.set_page_config(page_title="Journal", page_icon="📓", layout="wide")
bootstrap()
sidebar_portfolios()
page_header("Journal", "Why you'd own it, and what would prove you wrong.")

not_built_yet(
    3,
    "Versioned theses with falsifiers, a guided editor, and a 'critique my thesis' "
    "flow that argues the bear case. Nothing open-source does this — it's the "
    "reason the project exists.",
)

st.markdown(
    """
The shape of a thesis, so you can start thinking in it now:

- **The business, in one line.** If you can't, you're outside your circle.
- **Why is it cheap?** Name the mechanism, not the multiple.
- **Why won't it stay cheap?** What closes the gap, and roughly when.
- **What's it worth?** Owner earnings, then a margin-of-safety price.
- **What would prove me wrong?** Specific and checkable later. This is the field
  that makes the rest of it worth writing.
- **How confident am I, 1-5?** Recorded so it can be scored against outcomes.
"""
)

st.divider()
ask_panel("journal", AskContext(title="writing a thesis"), agent_id="journal_coach")
