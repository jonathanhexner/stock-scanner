"""Shared Streamlit chrome: the sidebar every page renders."""

from __future__ import annotations

import streamlit as st

from src.store import db


def bootstrap() -> None:
    """Run on every page load, deliberately uncached.

    `CREATE TABLE IF NOT EXISTS` is cheap and idempotent, and caching it meant a
    schema change did not reach a running server — a new table simply did not
    exist until someone restarted Streamlit. Correctness beats the microseconds.
    """
    db.init_db()
    with db.connect() as conn:
        db.seed_starter_portfolios(conn)


def sidebar_portfolios() -> list[str]:
    """Portfolio switcher. Returns the selected ids; the selection is app-wide."""
    with db.connect() as conn:
        portfolios = db.list_portfolios(conn)

    names = {p.id: f"{p.name} ({p.kind})" for p in portfolios}
    default = st.session_state.get("selected_portfolios") or [p.id for p in portfolios]

    with st.sidebar:
        st.subheader("Portfolios")
        selected = st.multiselect(
            "In context",
            options=list(names),
            default=[d for d in default if d in names],
            format_func=lambda pid: names[pid],
            label_visibility="collapsed",
        )
        st.caption("What the agents can see. Nothing selected means nothing sent.")

    st.session_state["selected_portfolios"] = selected
    return selected


def page_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.caption(subtitle)


def not_built_yet(phase: int, what: str) -> None:
    st.info(f"**Arrives in Phase {phase}.** {what}\n\nThe Ask panel below works now.")
