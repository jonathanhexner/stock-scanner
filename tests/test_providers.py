import pytest

from src.ask import providers
from src.store import db


def test_builtin_providers_are_registered():
    assert {p.id for p in providers.available()} >= {"glossary", "portfolio"}


def test_unknown_provider_fails_loud():
    with pytest.raises(providers.UnknownProvider):
        providers.build("no-such-provider", {})


def test_glossary_block_carries_the_shipped_terms():
    block = providers.build("glossary", {})

    assert block is not None
    assert "Owner earnings" in block.body
    assert "Falsifier" in block.body


def test_glossary_is_low_priority_so_real_data_wins_the_budget():
    glossary = providers.build("glossary", {})
    portfolio = providers.Provider("portfolio", "", lambda s: None, priority=80)

    assert glossary.priority < portfolio.priority


def test_empty_glossary_file_yields_no_block(tmp_path):
    assert providers.load_glossary(tmp_path / "missing.yaml") == {}


def test_portfolio_block_is_none_when_nothing_is_selected():
    assert providers.build("portfolio", {"portfolio_ids": []}) is None
    assert providers.build("portfolio", {}) is None


def test_portfolio_block_reports_holdings(tmp_path, monkeypatch):
    path = tmp_path / "journal.sqlite"
    db.init_db(path)
    monkeypatch.setattr(db, "DB_PATH", path)
    with db.connect(path) as conn:
        pid = db.create_portfolio(conn, "Real", "real", notes="Actual money.")
        db.add_transaction(conn, pid, "2024-01-15", "KO", volume=50, price=60.0)

    block = providers.build("portfolio", {"portfolio_ids": [pid]})

    assert "Real (real, benchmark SPY)" in block.body
    assert "KO: 50 units" in block.body
    assert "average cost 60.00 USD" in block.body


def test_portfolio_block_ignores_ids_that_do_not_exist(tmp_path, monkeypatch):
    path = tmp_path / "journal.sqlite"
    db.init_db(path)
    monkeypatch.setattr(db, "DB_PATH", path)

    assert providers.build("portfolio", {"portfolio_ids": ["nope"]}) is None


def test_split_defaults_separates_registered_from_future_providers():
    """Agents legitimately name providers from later phases. A page must not
    offer those as options — that raised a StreamlitAPIException on the Chat
    page before this existed."""
    registered, pending = providers.split_defaults(["glossary", "company", "portfolio"])

    assert registered == ["glossary", "portfolio"]
    assert pending == ["company"]


def test_every_shipped_agent_has_at_least_one_usable_provider_today():
    from src.ask.agents import load_agents

    for agent in load_agents().values():
        registered, _ = providers.split_defaults(agent.default_providers)
        assert registered, f"{agent.id} has no registered provider — its Chat page would be blank"
