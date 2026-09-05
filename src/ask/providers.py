"""Context providers.

A provider turns a selection (whatever the page or the Chat picker chose) into
a ContextBlock. Later phases register more — `lesson`, `thesis`, `company`,
`filing` — and both Ask and Chat pick them up without changing.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

import yaml

from src.ask.context import ContextBlock
from src.store import db

GLOSSARY_FILE = Path(__file__).resolve().parents[2] / "content" / "glossary.yaml"


class UnknownProvider(KeyError):
    pass


@dataclass(frozen=True)
class Provider:
    id: str
    label: str
    build: Callable[[dict], ContextBlock | None]
    priority: int = 50


_REGISTRY: dict[str, Provider] = {}


def register(provider: Provider) -> None:
    _REGISTRY[provider.id] = provider


def available() -> list[Provider]:
    return sorted(_REGISTRY.values(), key=lambda p: p.label)


def split_defaults(provider_ids: Iterable[str]) -> tuple[list[str], list[str]]:
    """Split an agent's preferred providers into (registered, not yet registered).

    Agents name providers from later phases — `company`, `filing`, `thesis`.
    That is legal; the page must not offer them as selectable options until the
    phase that registers them lands.
    """
    registered = [pid for pid in provider_ids if pid in _REGISTRY]
    pending = [pid for pid in provider_ids if pid not in _REGISTRY]
    return registered, pending


def build(provider_id: str, selection: dict) -> ContextBlock | None:
    if provider_id not in _REGISTRY:
        raise UnknownProvider(provider_id)
    return _REGISTRY[provider_id].build(selection)


# --- glossary -----------------------------------------------------------------


def load_glossary(path: Path = GLOSSARY_FILE) -> dict[str, str]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _glossary_block(selection: dict) -> ContextBlock | None:
    terms = load_glossary()
    if not terms:
        return None
    body = "\n".join(f"- {term}: {meaning}" for term, meaning in sorted(terms.items()))
    return ContextBlock(
        provider_id="glossary",
        label="Glossary",
        body=body,
        priority=10,
    )


# --- portfolio ----------------------------------------------------------------


def _portfolio_block(selection: dict) -> ContextBlock | None:
    """Selected portfolios and their holdings. Nothing selected means nothing sent."""
    wanted = selection.get("portfolio_ids") or []
    if not wanted:
        return None

    lines: list[str] = []
    with db.connect() as conn:
        by_id = {p.id: p for p in db.list_portfolios(conn)}
        for portfolio_id in wanted:
            portfolio = by_id.get(portfolio_id)
            if portfolio is None:
                continue
            lines.append(f"## {portfolio.name} ({portfolio.kind}, benchmark {portfolio.benchmark})")
            if portfolio.notes:
                lines.append(portfolio.notes)
            rows = db.holdings(conn, portfolio_id)
            if not rows:
                lines.append("No holdings recorded.")
            for row in rows:
                lines.append(
                    f"- {row['identifier']}: {row['volume']:g} units, "
                    f"average cost {row['average_cost']:.2f} {portfolio.base_currency}, "
                    f"first bought {row['first_bought']}"
                )
            lines.append("")

    if not lines:
        return None
    return ContextBlock(
        provider_id="portfolio",
        label="Portfolios",
        body="\n".join(lines).strip(),
        priority=80,
    )


register(Provider("glossary", "Glossary", _glossary_block, priority=10))
register(Provider("portfolio", "My portfolios", _portfolio_block, priority=80))
