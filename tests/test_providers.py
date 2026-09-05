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


# --- thesis provider ----------------------------------------------------------


def _thesis(**over):
    base = {
        "id": "t1", "ticker": "KO", "version": 2, "status": "owned",
        "business": "Sells concentrate to bottlers.", "why_cheap": "Out of favour.",
        "why_it_closes": "Pricing power returns.", "owner_earnings": "~$10bn",
        "fair_value": "$70", "mos_price": 55.0, "confidence": 4,
        "in_circle": True, "circle_why": "Simple business.",
        "sources": ["10-K 2025 Item 1A"], "note": "Revised after Q2.",
    }
    base.update(over)
    return base


def test_rendered_thesis_carries_every_field_an_agent_needs():
    body = providers.render_thesis(_thesis(), [])

    for expected in ["KO — thesis v2 (owned)", "Sells concentrate", "Out of favour",
                     "Pricing power returns", "$70", "55.0", "4/5", "10-K 2025 Item 1A"]:
        assert expected in body


def test_a_thesis_with_no_falsifiers_says_so_loudly():
    """The agent must be able to see that a thesis is unfalsifiable."""
    body = providers.render_thesis(_thesis(), [])

    assert "NONE RECORDED" in body
    assert "could prove" in body
    assert "cannot be checked later" in body


def test_unwritten_fields_are_marked_rather_than_left_blank():
    body = providers.render_thesis(_thesis(why_cheap="", fair_value=""), [])

    assert body.count("(not written)") == 2


def test_falsifier_rules_and_trips_are_rendered():
    rules = [
        {"statement": "Gross margin below 38%", "metric": "Gross Margin",
         "comparator": "<", "threshold": 0.38, "tripped_at": None, "tripped_note": ""},
        {"statement": "CEO leaves", "metric": "", "comparator": "", "threshold": None,
         "tripped_at": "2026-08-01", "tripped_note": "Announced retirement"},
    ]

    body = providers.render_thesis(_thesis(), rules)

    assert "rule: Gross Margin < 0.38" in body
    assert "TRIPPED 2026-08-01: Announced retirement" in body


def test_thesis_block_is_none_without_a_ticker():
    assert providers.build("thesis", {}) is None
    assert providers.build("thesis", {"ticker": ""}) is None


def test_thesis_block_reads_the_latest_version(tmp_path, monkeypatch):
    path = tmp_path / "journal.sqlite"
    db.init_db(path)
    monkeypatch.setattr(db, "DB_PATH", path)
    with db.connect(path) as conn:
        db.save_thesis(conn, "KO", why_cheap="v1 reason")
        tid = db.save_thesis(conn, "KO", why_cheap="v2 reason")
        db.add_falsifier(conn, tid, "Gross margin below 38%")

    block = providers.build("thesis", {"ticker": "ko"})

    assert block.label == "Thesis: KO"
    assert "v2 reason" in block.body
    assert "v1 reason" not in block.body
    assert block.priority == 90


def test_thesis_block_is_none_when_the_ticker_has_no_thesis(tmp_path, monkeypatch):
    path = tmp_path / "journal.sqlite"
    db.init_db(path)
    monkeypatch.setattr(db, "DB_PATH", path)

    assert providers.build("thesis", {"ticker": "NOPE"}) is None
