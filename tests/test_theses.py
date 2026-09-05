import sqlite3

import pytest

from src.store import db


@pytest.fixture
def conn(tmp_path):
    path = tmp_path / "journal.sqlite"
    db.init_db(path)
    with db.connect(path) as connection:
        yield connection


def test_first_thesis_is_version_one(conn):
    db.save_thesis(conn, "ko", business="Sells sugar water at scale.")

    thesis = db.latest_thesis(conn, "KO")

    assert thesis["version"] == 1
    assert thesis["ticker"] == "KO"
    assert thesis["status"] == "watching"


def test_saving_appends_a_version_rather_than_overwriting(conn):
    db.save_thesis(conn, "KO", why_cheap="Out of favour.")
    db.save_thesis(conn, "KO", why_cheap="Actually, margins are compressing.")

    versions = db.thesis_versions(conn, "KO")

    assert [v["version"] for v in versions] == [2, 1]
    assert versions[1]["why_cheap"] == "Out of favour."


def test_a_changed_mind_stays_readable(conn):
    """The whole point of versioning: you can see what you used to think."""
    db.save_thesis(conn, "KO", confidence=5, status="owned")
    db.save_thesis(conn, "KO", confidence=2, status="exited", note="I was wrong about pricing.")

    first, latest = db.thesis_versions(conn, "KO")[1], db.latest_thesis(conn, "KO")

    assert (first["confidence"], first["status"]) == (5, "owned")
    assert (latest["confidence"], latest["status"]) == (2, "exited")


def test_ticker_case_does_not_create_two_histories(conn):
    db.save_thesis(conn, "ko")
    db.save_thesis(conn, "KO")

    assert len(db.thesis_versions(conn, "Ko")) == 2


def test_unknown_status_is_rejected(conn):
    with pytest.raises(ValueError, match="not one of"):
        db.save_thesis(conn, "KO", status="mooning")


def test_unknown_field_is_rejected_rather_than_silently_dropped(conn):
    with pytest.raises(ValueError, match="unknown thesis fields"):
        db.save_thesis(conn, "KO", conviction=11)


def test_confidence_outside_one_to_five_is_rejected(conn):
    with pytest.raises(sqlite3.IntegrityError):
        db.save_thesis(conn, "KO", confidence=9)


def test_sources_round_trip_as_a_list(conn):
    db.save_thesis(conn, "KO", sources=["10-K 2025 Item 1A", "https://example.com"])

    assert db.latest_thesis(conn, "KO")["sources"] == [
        "10-K 2025 Item 1A",
        "https://example.com",
    ]


def test_list_theses_shows_only_the_latest_version_per_ticker(conn):
    db.save_thesis(conn, "KO", note="v1")
    db.save_thesis(conn, "KO", note="v2")
    db.save_thesis(conn, "MSFT", note="only")

    listed = {t["ticker"]: t for t in db.list_theses(conn)}

    assert set(listed) == {"KO", "MSFT"}
    assert listed["KO"]["note"] == "v2"


def test_latest_thesis_is_none_for_an_unknown_ticker(conn):
    assert db.latest_thesis(conn, "NOPE") is None


def test_a_thesis_survives_deleting_its_portfolio(conn):
    """Deleting a portfolio must not delete the thinking that went into it."""
    pid = db.create_portfolio(conn, "Paper", "paper")
    db.save_thesis(conn, "KO", portfolio_id=pid)

    conn.execute("DELETE FROM portfolios WHERE id = ?", (pid,))

    assert db.latest_thesis(conn, "KO")["portfolio_id"] is None


# --- falsifiers ---------------------------------------------------------------


def test_falsifier_needs_a_statement(conn):
    thesis_id = db.save_thesis(conn, "KO")

    with pytest.raises(ValueError, match="needs a statement"):
        db.add_falsifier(conn, thesis_id, "   ")


def test_falsifier_records_a_checkable_rule(conn):
    thesis_id = db.save_thesis(conn, "KO")
    db.add_falsifier(
        conn,
        thesis_id,
        "Gross margin below 38% for two consecutive quarters",
        metric="Gross Margin",
        comparator="<",
        threshold=0.38,
    )

    (falsifier,) = db.falsifiers(conn, thesis_id)

    assert falsifier["metric"] == "Gross Margin"
    assert falsifier["comparator"] == "<"
    assert falsifier["threshold"] == 0.38
    assert falsifier["tripped_at"] is None


def test_a_prose_only_falsifier_is_allowed(conn):
    """Not everything that would prove you wrong is a number."""
    thesis_id = db.save_thesis(conn, "KO")
    db.add_falsifier(conn, thesis_id, "The founder-CEO leaves")

    (falsifier,) = db.falsifiers(conn, thesis_id)

    assert falsifier["comparator"] == ""
    assert falsifier["threshold"] is None


def test_nonsense_comparator_is_rejected(conn):
    thesis_id = db.save_thesis(conn, "KO")

    with pytest.raises(sqlite3.IntegrityError):
        db.add_falsifier(conn, thesis_id, "x", metric="m", comparator="~=", threshold=1)


def test_falsifiers_carry_onto_a_new_version(conn):
    v1 = db.save_thesis(conn, "KO")
    db.add_falsifier(conn, v1, "Gross margin below 38%", "Gross Margin", "<", 0.38)
    v2 = db.save_thesis(conn, "KO")

    carried = db.copy_falsifiers(conn, v1, v2)

    assert carried == 1
    assert db.falsifiers(conn, v2)[0]["statement"] == "Gross margin below 38%"
    assert db.falsifiers(conn, v2)[0]["tripped_at"] is None


def test_carrying_falsifiers_does_not_move_them_off_the_old_version(conn):
    v1 = db.save_thesis(conn, "KO")
    db.add_falsifier(conn, v1, "Gross margin below 38%")
    v2 = db.save_thesis(conn, "KO")
    db.copy_falsifiers(conn, v1, v2)

    assert len(db.falsifiers(conn, v1)) == 1


def test_marking_a_falsifier_tripped_records_when_and_why(conn):
    thesis_id = db.save_thesis(conn, "KO")
    falsifier_id = db.add_falsifier(conn, thesis_id, "Gross margin below 38%")

    db.mark_falsifier_tripped(conn, falsifier_id, note="FY2026 Q2 came in at 36.1%")

    (falsifier,) = db.falsifiers(conn, thesis_id)
    assert falsifier["tripped_at"] is not None
    assert "36.1%" in falsifier["tripped_note"]


def test_deleting_a_thesis_takes_its_falsifiers_with_it(conn):
    thesis_id = db.save_thesis(conn, "KO")
    db.add_falsifier(conn, thesis_id, "x")

    conn.execute("DELETE FROM theses WHERE id = ?", (thesis_id,))

    assert db.falsifiers(conn, thesis_id) == []
