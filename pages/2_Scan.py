"""Scan — a thin candidate list. Phase 4."""

from __future__ import annotations

import streamlit as st

from src.ask import providers  # noqa: F401
from src.ask.context import AskContext
from src.ask.panel import ask_panel
from src.ui import bootstrap, not_built_yet, page_header, sidebar_portfolios

st.set_page_config(page_title="Scan", page_icon="🔎", layout="wide")
bootstrap()
sidebar_portfolios()
page_header("Scan", "A starting point for reading. Not a recommendation.")

not_built_yet(
    4,
    "Coarse value filters over a hand-dropped universe, with reasons attached — "
    "ratios from FinanceToolkit, which needs no API key.",
)

st.divider()
ask_panel("scan", AskContext(title="screening for value"), agent_id="tutor")
