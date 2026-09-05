"""SQLite store. Plain SQL, no ORM.

Transactions are the source of truth; holdings are derived from them. That
shape is borrowed from investbrain (see THIRD_PARTY.md) and it is what
FinanceToolkit's Portfolio module wants anyway.

Phase 1 tables only. Theses arrive in Phase 3.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "journal.sqlite"

PORTFOLIO_KINDS = ("real", "paper", "passed")

SCHEMA = """
CREATE TABLE IF NOT EXISTS portfolios (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    kind          TEXT NOT NULL CHECK (kind IN ('real', 'paper', 'passed')),
    base_currency TEXT NOT NULL DEFAULT 'USD',
    benchmark     TEXT NOT NULL DEFAULT 'SPY',
    notes         TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id           TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    date         TEXT NOT NULL,
    identifier   TEXT NOT NULL,
    volume       REAL NOT NULL,
    price        REAL NOT NULL,
    costs        REAL NOT NULL DEFAULT 0,
    currency     TEXT NOT NULL DEFAULT 'USD',
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_txn_portfolio ON transactions(portfolio_id, date);

CREATE TABLE IF NOT EXISTS chat_threads (
    id           TEXT PRIMARY KEY,
    agent_id     TEXT NOT NULL,
    title        TEXT NOT NULL,
    provider_ids TEXT NOT NULL DEFAULT '[]',
    selection    TEXT NOT NULL DEFAULT '{}',
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id         TEXT PRIMARY KEY,
    thread_id  TEXT NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    agent_id   TEXT NOT NULL DEFAULT '',
    usage      TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_msg_thread ON chat_messages(thread_id, created_at);

CREATE TABLE IF NOT EXISTS lesson_progress (
    lesson_id TEXT PRIMARY KEY,
    read_at   TEXT,
    tried_at  TEXT
);
"""


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def new_id() -> str:
    return uuid.uuid4().hex


@contextmanager
def connect(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Resolve DB_PATH at call time so tests (and a future config) can redirect it."""
    path = path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path: Path | None = None) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)


# --- portfolios ---------------------------------------------------------------


@dataclass(frozen=True)
class Portfolio:
    id: str
    name: str
    kind: str
    base_currency: str
    benchmark: str
    notes: str


def create_portfolio(
    conn: sqlite3.Connection,
    name: str,
    kind: str,
    base_currency: str = "USD",
    benchmark: str = "SPY",
    notes: str = "",
) -> str:
    if kind not in PORTFOLIO_KINDS:
        raise ValueError(f"kind {kind!r} not one of {PORTFOLIO_KINDS}")
    portfolio_id = new_id()
    conn.execute(
        "INSERT INTO portfolios (id, name, kind, base_currency, benchmark, notes, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (portfolio_id, name, kind, base_currency, benchmark, notes, now()),
    )
    return portfolio_id


def list_portfolios(conn: sqlite3.Connection) -> list[Portfolio]:
    rows = conn.execute("SELECT * FROM portfolios ORDER BY kind, name").fetchall()
    return [
        Portfolio(r["id"], r["name"], r["kind"], r["base_currency"], r["benchmark"], r["notes"])
        for r in rows
    ]


def seed_starter_portfolios(conn: sqlite3.Connection) -> None:
    """Real / Paper / Passed. The 'passed' one is where calibration is learned."""
    if conn.execute("SELECT 1 FROM portfolios LIMIT 1").fetchone():
        return
    create_portfolio(conn, "Real", "real", notes="Actual money.")
    create_portfolio(conn, "Paper", "paper", notes="Ideas I would have bought.")
    create_portfolio(conn, "Passed", "passed", notes="Ideas I rejected. Was I right?")


# --- transactions -------------------------------------------------------------


def add_transaction(
    conn: sqlite3.Connection,
    portfolio_id: str,
    date: str,
    identifier: str,
    volume: float,
    price: float,
    costs: float = 0.0,
    currency: str = "USD",
) -> str:
    txn_id = new_id()
    conn.execute(
        "INSERT INTO transactions"
        " (id, portfolio_id, date, identifier, volume, price, costs, currency, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (txn_id, portfolio_id, date, identifier.upper(), volume, price, costs, currency, now()),
    )
    return txn_id


def holdings(conn: sqlite3.Connection, portfolio_id: str) -> list[dict]:
    """Derived from transactions. Positions fully sold out are dropped."""
    rows = conn.execute(
        "SELECT identifier,"
        "       SUM(volume) AS volume,"
        "       SUM(volume * price) AS invested,"
        "       SUM(costs) AS costs,"
        "       MIN(date) AS first_bought"
        " FROM transactions WHERE portfolio_id = ?"
        " GROUP BY identifier HAVING SUM(volume) > 0"
        " ORDER BY identifier",
        (portfolio_id,),
    ).fetchall()
    return [
        {
            "identifier": r["identifier"],
            "volume": r["volume"],
            "invested": r["invested"],
            "costs": r["costs"],
            "average_cost": r["invested"] / r["volume"],
            "first_bought": r["first_bought"],
        }
        for r in rows
    ]


# --- chat ---------------------------------------------------------------------


def create_thread(
    conn: sqlite3.Connection,
    agent_id: str,
    title: str,
    provider_ids: list[str],
    selection: dict,
) -> str:
    thread_id = new_id()
    stamp = now()
    conn.execute(
        "INSERT INTO chat_threads"
        " (id, agent_id, title, provider_ids, selection, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (thread_id, agent_id, title, json.dumps(provider_ids), json.dumps(selection), stamp, stamp),
    )
    return thread_id


def list_threads(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM chat_threads ORDER BY updated_at DESC").fetchall()
    return [
        {
            "id": r["id"],
            "agent_id": r["agent_id"],
            "title": r["title"],
            "provider_ids": json.loads(r["provider_ids"]),
            "selection": json.loads(r["selection"]),
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


def add_message(
    conn: sqlite3.Connection,
    thread_id: str,
    role: str,
    content: str,
    agent_id: str = "",
    usage: dict | None = None,
) -> str:
    message_id = new_id()
    stamp = now()
    conn.execute(
        "INSERT INTO chat_messages (id, thread_id, role, content, agent_id, usage, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (message_id, thread_id, role, content, agent_id, json.dumps(usage or {}), stamp),
    )
    conn.execute("UPDATE chat_threads SET updated_at = ? WHERE id = ?", (stamp, thread_id))
    return message_id


def messages(conn: sqlite3.Connection, thread_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT role, content, usage FROM chat_messages"
        " WHERE thread_id = ? ORDER BY created_at, rowid",
        (thread_id,),
    ).fetchall()
    return [
        {"role": r["role"], "content": r["content"], "usage": json.loads(r["usage"])} for r in rows
    ]
