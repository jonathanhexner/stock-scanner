"""The Ask panel — the same conversation widget every page gets.

Pages hand it an AskContext and an agent id; it owns the rest. Chat uses the
same `converse` underneath, with the context picked by hand instead of by page.
"""

from __future__ import annotations

import streamlit as st

from src.ask import client
from src.ask.agents import Agent, load_agents, load_preamble
from src.ask.context import AskContext


@st.cache_data(show_spinner=False)
def _agents() -> dict[str, Agent]:
    return load_agents()


@st.cache_data(show_spinner=False)
def _preamble() -> str:
    return load_preamble()


def agents() -> dict[str, Agent]:
    return _agents()


def show_context(context: AskContext) -> None:
    """Never send invisible context."""
    if context.blocks:
        names = ", ".join(f"{b.label} ({b.size:,} chars)" for b in context.blocks)
        st.caption(f"Context: {names}")
    else:
        st.caption("Context: none — answers will be general, not about your data.")
    if context.dropped:
        st.warning(f"Context budget exceeded. Dropped: {', '.join(context.dropped)}")


def converse(
    agent_id: str,
    context: AskContext,
    history: list[dict],
    question: str,
) -> str:
    """Stream one answer into the page and return the full text."""
    agent = agents()[agent_id]
    fitted = context.fit()

    try:
        stream = client.stream_answer(agent, _preamble(), fitted, history, question)
        return st.write_stream(stream)
    except client.MissingAPIKey as exc:
        st.error(str(exc))
        return ""


def ask_panel(page: str, context: AskContext, agent_id: str = "tutor") -> None:
    """An expander on every page. History is per-page and lives for the session."""
    key = f"ask_history_{page}"
    history = st.session_state.setdefault(key, [])

    with st.expander(f"Ask about {context.title}", expanded=False):
        show_context(context)

        for message in history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input("Ask a question", key=f"ask_input_{page}")
        if not question:
            return

        history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            answer = converse(agent_id, context, history[:-1], question)

        if answer:
            history.append({"role": "assistant", "content": answer})
        else:
            history.pop()
