"""Agent definitions loaded from `config/agents/*.md`.

An agent is a markdown file: YAML front-matter between `---` fences, then the
system prompt body. `_preamble.md` has no front-matter and is prepended to every
agent's prompt — it carries the rules that outrank anything an agent says about
itself.

Adding an agent is adding a file. Never a code change.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

AGENTS_DIR = Path(__file__).resolve().parents[2] / "config" / "agents"
PREAMBLE_FILE = "_preamble.md"

VALID_EFFORTS = {"low", "medium", "high", "xhigh", "max"}


class AgentDefinitionError(ValueError):
    """An agent file is malformed. Fail loud — a silently skipped agent is worse."""


@dataclass(frozen=True)
class Agent:
    id: str
    name: str
    description: str
    default_providers: tuple[str, ...]
    effort: str
    prompt: str

    def system_prompt(self, preamble: str) -> str:
        return f"{preamble.strip()}\n\n---\n\n{self.prompt.strip()}"


def split_front_matter(text: str, source: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise AgentDefinitionError(f"{source}: missing YAML front-matter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise AgentDefinitionError(f"{source}: front-matter is not closed by a second ---")
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        raise AgentDefinitionError(f"{source}: front-matter is not valid YAML: {exc}") from exc
    if not isinstance(meta, dict):
        raise AgentDefinitionError(f"{source}: front-matter must be a mapping")
    return meta, parts[2]


def parse_agent(path: Path) -> Agent:
    meta, body = split_front_matter(path.read_text(encoding="utf-8"), path.name)

    for field in ("name", "description"):
        if not meta.get(field):
            raise AgentDefinitionError(f"{path.name}: '{field}' is required")

    if not body.strip():
        raise AgentDefinitionError(f"{path.name}: prompt body is empty")

    effort = meta.get("effort", "medium")
    if effort not in VALID_EFFORTS:
        raise AgentDefinitionError(
            f"{path.name}: effort {effort!r} not one of {sorted(VALID_EFFORTS)}"
        )

    providers = meta.get("default_providers") or []
    if not isinstance(providers, list):
        raise AgentDefinitionError(f"{path.name}: default_providers must be a list")

    return Agent(
        id=path.stem,
        name=str(meta["name"]),
        description=str(meta["description"]),
        default_providers=tuple(str(p) for p in providers),
        effort=effort,
        prompt=body,
    )


def load_preamble(agents_dir: Path = AGENTS_DIR) -> str:
    path = agents_dir / PREAMBLE_FILE
    if not path.exists():
        raise AgentDefinitionError(f"{path} is missing — every agent inherits it")
    return path.read_text(encoding="utf-8")


def load_agents(agents_dir: Path = AGENTS_DIR) -> dict[str, Agent]:
    """Load every agent definition, keyed by id (the filename stem)."""
    agents = {}
    for path in sorted(agents_dir.glob("*.md")):
        if path.name == PREAMBLE_FILE:
            continue
        agent = parse_agent(path)
        agents[agent.id] = agent
        logger.info("loaded agent %s (%s)", agent.id, agent.name)
    if not agents:
        raise AgentDefinitionError(f"no agent definitions found in {agents_dir}")
    return agents
