"""Chat — pick the agent, pick exactly what it can see, keep the thread."""

from __future__ import annotations

import streamlit as st

from src.ask import providers
from src.ask.context import AskContext
from src.ask.panel import agents, converse, show_context
from src.store import db
from src.ui import bootstrap, page_header, sidebar_portfolios

st.set_page_config(page_title="Chat", page_icon="💬", layout="wide")
bootstrap()
selected_portfolios = sidebar_portfolios()
page_header("Chat", "Pick an agent and what it can see. Threads are kept.")

roster = agents()

with st.sidebar:
    st.subheader("Threads")
    with db.connect() as conn:
        threads = db.list_threads(conn)
    options = ["New thread"] + [t["id"] for t in threads]
    titles = {t["id"]: f"{roster[t['agent_id']].name}: {t['title']}" for t in threads
              if t["agent_id"] in roster}
    chosen = st.radio(
        "Thread",
        options=options,
        format_func=lambda tid: "New thread" if tid == "New thread" else titles.get(tid, tid),
        label_visibility="collapsed",
    )

left, right = st.columns([1, 2])

with left:
    agent_id = st.selectbox(
        "Agent",
        options=list(roster),
        format_func=lambda aid: roster[aid].name,
        index=0,
    )
    st.caption(roster[agent_id].description)

    labels = {p.id: p.label for p in providers.available()}
    defaults, pending = providers.split_defaults(roster[agent_id].default_providers)
    picked = st.multiselect(
        "Context",
        options=list(labels),
        default=defaults,
        format_func=lambda pid: labels[pid],
    )
    if pending:
        st.caption(
            f"This agent also wants {', '.join(pending)} — "
            "not registered until a later phase."
        )

selection = {"portfolio_ids": selected_portfolios}
context = AskContext(title="this conversation")
for provider_id in picked:
    try:
        block = providers.build(provider_id, selection)
    except providers.UnknownProvider:
        continue
    if block:
        context.add(block)

with right:
    show_context(context.fit())

    thread_id = None if chosen == "New thread" else chosen
    history = []
    if thread_id:
        with db.connect() as conn:
            history = db.messages(conn, thread_id)

    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Ask anything")

if not question:
    st.stop()

with db.connect() as conn:
    if thread_id is None:
        thread_id = db.create_thread(
            conn,
            agent_id=agent_id,
            title=question[:60],
            provider_ids=picked,
            selection=selection,
        )
    db.add_message(conn, thread_id, "user", question)

with right:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        answer = converse(agent_id, context, history, question)

if answer:
    with db.connect() as conn:
        db.add_message(conn, thread_id, "assistant", answer, agent_id=agent_id)

st.rerun()
