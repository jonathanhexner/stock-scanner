import pytest

from src.ask.agents import (
    AGENTS_DIR,
    Agent,
    AgentDefinitionError,
    load_agents,
    load_preamble,
    parse_agent,
)

AGENT_MD = """---
name: Tester
description: A test agent.
default_providers: [glossary]
effort: low
---
Body of the prompt.
"""


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_agent_reads_front_matter_and_body(tmp_path):
    agent = parse_agent(write(tmp_path, "tester.md", AGENT_MD))

    assert agent == Agent(
        id="tester",
        name="Tester",
        description="A test agent.",
        default_providers=("glossary",),
        effort="low",
        prompt="\nBody of the prompt.\n",
    )


def test_effort_defaults_to_medium(tmp_path):
    md = AGENT_MD.replace("effort: low\n", "")
    assert parse_agent(write(tmp_path, "tester.md", md)).effort == "medium"


@pytest.mark.parametrize(
    "text, expected",
    [
        ("no front matter at all", "missing YAML front-matter"),
        ("---\nname: X\ndescription: Y\nbody with no closing fence", "not closed"),
        ("---\nname: X\n---\nbody", "'description' is required"),
        ("---\nname: X\ndescription: Y\n---\n   \n", "prompt body is empty"),
        ("---\nname: X\ndescription: Y\neffort: turbo\n---\nbody", "effort"),
        ("---\nname: X\ndescription: Y\ndefault_providers: glossary\n---\nb", "must be a list"),
        ("---\n- not\n- a mapping\n---\nbody", "must be a mapping"),
    ],
)
def test_malformed_agent_files_fail_loud(tmp_path, text, expected):
    with pytest.raises(AgentDefinitionError, match=expected):
        parse_agent(write(tmp_path, "bad.md", text))


def test_load_agents_skips_preamble_and_keys_by_stem(tmp_path):
    write(tmp_path, "_preamble.md", "Shared rules.")
    write(tmp_path, "tester.md", AGENT_MD)

    agents = load_agents(tmp_path)

    assert list(agents) == ["tester"]


def test_load_agents_raises_when_directory_is_empty(tmp_path):
    with pytest.raises(AgentDefinitionError, match="no agent definitions"):
        load_agents(tmp_path)


def test_system_prompt_puts_preamble_first(tmp_path):
    agent = parse_agent(write(tmp_path, "tester.md", AGENT_MD))

    prompt = agent.system_prompt("Shared rules.")

    assert prompt.startswith("Shared rules.")
    assert prompt.endswith("Body of the prompt.")


# --- the real config, not fixtures -------------------------------------------------


def test_shipped_agents_all_parse():
    agents = load_agents()

    assert "tutor" in agents
    assert "devils_advocate" in agents


def test_shipped_agents_declare_known_providers():
    known = {"glossary", "portfolio", "lesson", "thesis", "company", "filing"}

    for agent in load_agents().values():
        unknown = set(agent.default_providers) - known
        assert not unknown, f"{agent.id} refers to unregistered providers: {unknown}"


def test_preamble_carries_the_no_advice_rule():
    """The rule that matters most. If this file drifts, the app stops being safe."""
    preamble = load_preamble().lower()

    assert "never give investment advice" in preamble
    assert "buy, sell, or hold" in preamble


def test_every_shipped_agent_inherits_the_preamble():
    preamble = load_preamble()

    for agent in load_agents().values():
        assert agent.system_prompt(preamble).startswith(preamble.strip()[:40])


def test_agents_dir_is_where_we_think_it_is():
    assert (AGENTS_DIR / "_preamble.md").exists()
