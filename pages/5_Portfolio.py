"""Portfolio — multiple books, hand-entered. Performance maths arrives in Phase 5."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ask import providers
from src.ask.context import AskContext
from src.ask.panel import ask_panel
from src.store import db
from src.ui import bootstrap, page_header, sidebar_portfolios

st.set_page_config(page_title="Portfolio", page_icon="💼", layout="wide")
bootstrap()
selected = sidebar_portfolios()
page_header("Portfolio", "Real money, paper ideas, and the ones you passed on.")

with db.connect() as conn:
    portfolios = {p.id: p for p in db.list_portfolios(conn)}

if not selected:
    st.info("Select a portfolio in the sidebar.")
    st.stop()

for portfolio_id in selected:
    portfolio = portfolios[portfolio_id]
    st.subheader(f"{portfolio.name} · {portfolio.kind}")
    st.caption(f"{portfolio.notes}  Benchmark: {portfolio.benchmark}")

    with db.connect() as conn:
        rows = db.holdings(conn, portfolio_id)

    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.caption("No holdings yet.")

    with st.form(f"add_{portfolio_id}", clear_on_submit=True):
        st.write("Record a transaction")
        cols = st.columns(5)
        identifier = cols[0].text_input("Ticker", key=f"t_{portfolio_id}")
        volume = cols[1].number_input("Units", value=0.0, step=1.0, key=f"v_{portfolio_id}")
        price = cols[2].number_input("Price", value=0.0, step=1.0, key=f"p_{portfolio_id}")
        costs = cols[3].number_input("Costs", value=0.0, step=1.0, key=f"c_{portfolio_id}")
        date = cols[4].date_input("Date", key=f"d_{portfolio_id}")
        if st.form_submit_button("Add") and identifier and volume:
            with db.connect() as conn:
                db.add_transaction(
                    conn,
                    portfolio_id,
                    date.isoformat(),
                    identifier,
                    volume,
                    price,
                    costs,
                    portfolio.base_currency,
                )
            st.rerun()

    st.divider()

st.info(
    "**Phase 5** adds performance against the benchmark — return, alpha, beta, weights — "
    "by handing these transactions to FinanceToolkit's Portfolio module. Verified to work "
    "with no API key."
)

context = AskContext(title="my portfolios")
block = providers.build("portfolio", {"portfolio_ids": selected})
if block:
    context.add(block)

ask_panel("portfolio", context, agent_id="portfolio_reviewer")
