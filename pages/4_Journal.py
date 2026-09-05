"""Journal — the core of the product.

A thesis is never edited in place. Saving appends a version, so a changed mind
stays readable. Falsifiers carry forward, because a version that quietly lost
them would no longer be checkable.
"""

from __future__ import annotations

import streamlit as st

from src.ask import providers
from src.ask.context import AskContext
from src.ask.panel import ask_panel, converse
from src.ask.render import escape_money
from src.store import db
from src.ui import bootstrap, page_header, sidebar_portfolios

st.set_page_config(page_title="Journal", page_icon="📓", layout="wide")
bootstrap()
sidebar_portfolios()
page_header("Journal", "Why you'd own it, and what would prove you wrong.")

with db.connect() as conn:
    existing = db.list_theses(conn)
    portfolios = {p.id: f"{p.name} ({p.kind})" for p in db.list_portfolios(conn)}

versions = {t["ticker"]: t["version"] for t in existing}
choice = st.selectbox(
    "Thesis",
    options=["+ New thesis"] + list(versions),
    format_func=lambda t: t if t == "+ New thesis" else f"{t} — v{versions[t]}",
)

is_new = choice == "+ New thesis"
current: dict | None = None
rules: list[dict] = []

if not is_new:
    with db.connect() as conn:
        current = db.latest_thesis(conn, choice)
        rules = db.falsifiers(conn, current["id"]) if current else []

editor, side = st.columns([3, 2])

with editor:
    with st.form("thesis"):
        ticker = st.text_input(
            "Ticker", value="" if is_new else choice, disabled=not is_new
        ).upper()

        business = st.text_area(
            "The business, in one line",
            value=current["business"] if current else "",
            help="If you can't, you're outside your circle of competence.",
        )
        why_cheap = st.text_area(
            "Why is it cheap?",
            value=current["why_cheap"] if current else "",
            help="Name the mechanism, not the multiple.",
        )
        why_it_closes = st.text_area(
            "Why won't it stay cheap?",
            value=current["why_it_closes"] if current else "",
            help="What closes the gap, and roughly when.",
        )
        owner_earnings = st.text_area(
            "Owner earnings — your estimate and how you got there",
            value=current["owner_earnings"] if current else "",
        )
        fair_value = st.text_area(
            "What's it worth?", value=current["fair_value"] if current else ""
        )

        cols = st.columns(4)
        mos_price = cols[0].number_input(
            "Margin-of-safety price",
            value=float(current["mos_price"]) if current and current["mos_price"] else 0.0,
            step=1.0,
        )
        confidence = cols[1].slider(
            "Confidence", 1, 5, value=(current["confidence"] if current else 3) or 3
        )
        status = cols[2].selectbox(
            "Status",
            options=db.THESIS_STATUSES,
            index=db.THESIS_STATUSES.index(current["status"]) if current else 0,
        )
        portfolio_id = cols[3].selectbox(
            "Portfolio",
            options=[None] + list(portfolios),
            format_func=lambda pid: "— none —" if pid is None else portfolios[pid],
            index=0,
        )

        in_circle = st.checkbox(
            "This is inside my circle of competence",
            value=current["in_circle"] if current else False,
        )
        circle_why = st.text_input(
            "Why (or why not)?", value=current["circle_why"] if current else ""
        )
        sources = st.text_area(
            "Sources, one per line",
            value="\n".join(current["sources"]) if current else "",
        )
        note = st.text_input(
            "What changed since the last version?",
            placeholder="Only relevant when revising.",
        )

        saved = st.form_submit_button("Save new version")

    if saved:
        if not ticker:
            st.error("A thesis needs a ticker.")
        else:
            with db.connect() as conn:
                previous = db.latest_thesis(conn, ticker)
                thesis_id = db.save_thesis(
                    conn,
                    ticker,
                    portfolio_id=portfolio_id,
                    status=status,
                    business=business,
                    why_cheap=why_cheap,
                    why_it_closes=why_it_closes,
                    owner_earnings=owner_earnings,
                    fair_value=fair_value,
                    mos_price=mos_price or None,
                    confidence=confidence,
                    in_circle=in_circle,
                    circle_why=circle_why,
                    sources=[s.strip() for s in sources.splitlines() if s.strip()],
                    note=note,
                )
                carried = db.copy_falsifiers(conn, previous["id"], thesis_id) if previous else 0
            with db.connect() as conn:
                version = db.latest_thesis(conn, ticker)["version"]
            st.success(f"Saved {ticker} v{version} · {carried} falsifiers carried over")
            st.rerun()

with side:
    st.subheader("Falsifiers")
    st.caption(
        "What would prove this wrong? Specific and checkable later — "
        "'gross margin below 38% for two quarters', not 'the moat erodes'."
    )

    if current is None:
        st.info("Save the thesis first, then record what would break it.")
    else:
        if not rules:
            st.warning("No falsifiers recorded. This thesis cannot be proved wrong.")
        for rule in rules:
            if rule["tripped_at"]:
                st.error(f"**TRIPPED** {rule['statement']} — {rule['tripped_note']}")
            else:
                st.write(f"• {rule['statement']}")
                if rule["metric"] and rule["comparator"]:
                    st.caption(f"rule: {rule['metric']} {rule['comparator']} {rule['threshold']}")
                if st.button("Mark tripped", key=f"trip_{rule['id']}"):
                    with db.connect() as conn:
                        db.mark_falsifier_tripped(conn, rule["id"])
                    st.rerun()

        with st.form(f"falsifier_{current['id']}", clear_on_submit=True):
            statement = st.text_input("What would prove me wrong?")
            fcols = st.columns(3)
            metric = fcols[0].text_input("Metric (optional)")
            comparator = fcols[1].selectbox("", options=["", "<", "<=", ">", ">="])
            threshold = fcols[2].number_input("Threshold", value=0.0, step=0.01)
            if st.form_submit_button("Add falsifier") and statement.strip():
                with db.connect() as conn:
                    db.add_falsifier(
                        conn,
                        current["id"],
                        statement,
                        metric=metric,
                        comparator=comparator,
                        threshold=threshold or None,
                    )
                st.rerun()

if current is not None:
    st.divider()
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Critique my thesis")
        st.caption("The Devil's Advocate argues the bear case. It recommends nothing.")
        if st.button("Attack it", type="primary"):
            context = AskContext(title=f"{choice} thesis")
            block = providers.build("thesis", {"ticker": choice})
            if block:
                context.add(block)
            glossary = providers.build("glossary", {})
            if glossary:
                context.add(glossary)
            with st.chat_message("assistant"):
                converse(
                    "devils_advocate",
                    context,
                    [],
                    "Attack this thesis. Unstated assumptions, the bear case, and any "
                    "falsifier that should be on the list and isn't.",
                )

    with right:
        st.subheader("History")
        st.download_button(
            "Export latest as Markdown",
            data=providers.render_thesis(current, rules),
            file_name=f"{choice}-thesis-v{current['version']}.md",
            mime="text/markdown",
        )
        with db.connect() as conn:
            for version in db.thesis_versions(conn, choice):
                stamp = version["created_at"][:10]
                label = f"v{version['version']} · {version['status']} · {stamp}"
                with st.expander(label):
                    if version["note"]:
                        st.caption(f"Changed: {version['note']}")
                    rendered = providers.render_thesis(version, db.falsifiers(conn, version["id"]))
                    st.markdown(escape_money(rendered).replace("\n", "  \n"))

    st.divider()
    thesis_context = AskContext(title=f"the {choice} thesis")
    thesis_block = providers.build("thesis", {"ticker": choice})
    if thesis_block:
        thesis_context.add(thesis_block)
    ask_panel("journal", thesis_context, agent_id="journal_coach")
else:
    st.divider()
    ask_panel("journal", AskContext(title="writing a thesis"), agent_id="journal_coach")
