import sqlite3

import pytest

from src.store import db


@pytest.fixture
def conn(tmp_path):
    path = tmp_path / "journal.sqlite"
    db.init_db(path)
    with db.connect(path) as connection:
        yield connection


def test_seed_creates_the_three_starter_portfolios(conn):
    db.seed_starter_portfolios(conn)

    assert {p.kind for p in db.list_portfolios(conn)} == {"real", "paper", "passed"}


def test_seeding_twice_does_not_duplicate(conn):
    db.seed_starter_portfolios(conn)
    db.seed_starter_portfolios(conn)

    assert len(db.list_portfolios(conn)) == 3


def test_unknown_portfolio_kind_is_rejected(conn):
    with pytest.raises(ValueError, match="not one of"):
        db.create_portfolio(conn, "Crypto punts", "yolo")


def test_holdings_are_derived_from_transactions(conn):
    pid = db.create_portfolio(conn, "Real", "real")
    db.add_transaction(conn, pid, "2024-01-15", "ko", volume=50, price=60.0)
    db.add_transaction(conn, pid, "2025-02-10", "KO", volume=25, price=66.0)

    (holding,) = db.holdings(conn, pid)

    assert holding["identifier"] == "KO"
    assert holding["volume"] == 75
    assert holding["average_cost"] == pytest.approx(62.0)
    assert holding["first_bought"] == "2024-01-15"


def test_a_position_sold_out_disappears_from_holdings(conn):
    pid = db.create_portfolio(conn, "Real", "real")
    db.add_transaction(conn, pid, "2024-01-15", "KO", volume=50, price=60.0)
    db.add_transaction(conn, pid, "2025-06-01", "KO", volume=-50, price=70.0)

    assert db.holdings(conn, pid) == []


def test_holdings_are_scoped_to_one_portfolio(conn):
    real = db.create_portfolio(conn, "Real", "real")
    paper = db.create_portfolio(conn, "Paper", "paper")
    db.add_transaction(conn, real, "2024-01-15", "KO", volume=50, price=60.0)
    db.add_transaction(conn, paper, "2024-01-15", "MSFT", volume=10, price=400.0)

    assert [h["identifier"] for h in db.holdings(conn, real)] == ["KO"]
    assert [h["identifier"] for h in db.holdings(conn, paper)] == ["MSFT"]


def test_a_transaction_needs_a_real_portfolio(conn):
    with pytest.raises(sqlite3.IntegrityError):
        db.add_transaction(conn, "no-such-portfolio", "2024-01-15", "KO", 1, 1.0)


def test_thread_round_trips_its_agent_and_context_selection(conn):
    thread_id = db.create_thread(
        conn,
        agent_id="graham",
        title="Is KO cheap?",
        provider_ids=["glossary", "portfolio"],
        selection={"portfolio_ids": ["abc"]},
    )

    (thread,) = db.list_threads(conn)

    assert thread["id"] == thread_id
    assert thread["agent_id"] == "graham"
    assert thread["provider_ids"] == ["glossary", "portfolio"]
    assert thread["selection"] == {"portfolio_ids": ["abc"]}


def test_messages_come_back_in_order(conn):
    thread_id = db.create_thread(conn, "tutor", "t", [], {})
    db.add_message(conn, thread_id, "user", "what is owner earnings?")
    db.add_message(conn, thread_id, "assistant", "Net income plus...", agent_id="tutor")

    assert [m["role"] for m in db.messages(conn, thread_id)] == ["user", "assistant"]


def test_message_role_is_constrained(conn):
    thread_id = db.create_thread(conn, "tutor", "t", [], {})

    with pytest.raises(sqlite3.IntegrityError):
        db.add_message(conn, thread_id, "system", "sneaky")


def test_init_db_is_idempotent(tmp_path):
    path = tmp_path / "journal.sqlite"
    db.init_db(path)
    db.init_db(path)

    with db.connect(path) as conn:
        assert db.list_portfolios(conn) == []


def test_init_db_adds_tables_missing_from_an_older_database(tmp_path):
    """A schema change must reach a database that already exists — this is what
    broke the Journal page the first time it was opened."""
    path = tmp_path / "journal.sqlite"
    with db.connect(path) as conn:
        conn.executescript(
            "CREATE TABLE portfolios (id TEXT PRIMARY KEY, name TEXT, kind TEXT,"
            " base_currency TEXT, benchmark TEXT, notes TEXT, created_at TEXT);"
        )

    db.init_db(path)

    with db.connect(path) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"theses", "falsifiers", "chat_threads"} <= tables
