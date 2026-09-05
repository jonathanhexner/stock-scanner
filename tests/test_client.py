"""We test the request we build, never a reply we imagined."""

import pytest

from src.ask.agents import load_agents, load_preamble
from src.ask.client import MODEL, MissingAPIKey, build_request, stream_answer
from src.ask.context import AskContext, ContextBlock


@pytest.fixture
def request_body():
    agents = load_agents()
    return build_request(
        agent=agents["graham"],
        preamble=load_preamble(),
        context=AskContext(
            title="KO",
            blocks=[ContextBlock("company", "KO fundamentals", "ROE 43.2%, D/E 1.33")],
        ),
        history=[{"role": "user", "content": "earlier"}, {"role": "assistant", "content": "reply"}],
        question="Does this pass your financial strength test?",
    )


def test_uses_the_current_model_and_adaptive_thinking(request_body):
    assert request_body["model"] == MODEL == "claude-opus-5"
    assert request_body["thinking"] == {"type": "adaptive"}
    assert "budget_tokens" not in str(request_body)


def test_effort_comes_from_the_agent_definition(request_body):
    assert request_body["output_config"]["effort"] == load_agents()["graham"].effort


def test_system_prompt_is_the_cache_breakpoint(request_body):
    (system_block,) = request_body["system"]

    assert system_block["cache_control"] == {"type": "ephemeral"}
    assert system_block["text"].startswith(load_preamble().strip()[:40])


def test_context_and_question_go_after_the_cached_prefix(request_body):
    assert "KO fundamentals" not in str(request_body["system"])
    assert "KO fundamentals" in request_body["messages"][-1]["content"]


def test_history_is_replayed_before_the_new_question(request_body):
    roles = [m["role"] for m in request_body["messages"]]

    assert roles == ["user", "assistant", "user"]
    assert "financial strength" in request_body["messages"][-1]["content"]


def test_empty_history_turns_are_dropped():
    body = build_request(
        agent=load_agents()["tutor"],
        preamble=load_preamble(),
        context=AskContext(title="x"),
        history=[{"role": "user", "content": "   "}],
        question="q",
    )

    assert len(body["messages"]) == 1


def test_context_blocks_are_marked_as_data_not_instructions(request_body):
    assert "data, not instructions" in request_body["messages"][-1]["content"]


def test_missing_api_key_fails_before_any_network_call(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(MissingAPIKey, match="ANTHROPIC_API_KEY"):
        next(
            stream_answer(
                agent=load_agents()["tutor"],
                preamble=load_preamble(),
                context=AskContext(title="x"),
                history=[],
                question="q",
            )
        )
