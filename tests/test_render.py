"""Streamlit renders `$...$` as LaTeX, which mangles money in a money app."""

from src.ask.render import escape_money, escaped_stream


def test_amounts_are_escaped():
    assert escape_money("$70 fair value against $55") == "\$70 fair value against \$55"


def test_a_lone_dollar_is_left_alone():
    """So `\$` never appears inside a code block or plain prose."""
    assert escape_money("costs $ per unit") == "costs $ per unit"
    assert escape_money("echo $HOME") == "echo $HOME"


def test_text_without_money_is_untouched():
    assert escape_money("no amounts here") == "no amounts here"


def test_stream_escapes_across_a_chunk_boundary():
    """The failure this exists for: '$' arrives in one chunk, '70' in the next."""
    assert "".join(escaped_stream(iter(["worth $", "70 today"]))) == "worth \$70 today"


def test_stream_preserves_a_trailing_dollar_at_the_end():
    assert "".join(escaped_stream(iter(["price in $"]))) == "price in $"


def test_stream_reassembles_the_original_text():
    chunks = ["The ", "fair value is $", "70, ", "the trigger $55."]

    assert "".join(escaped_stream(iter(chunks))) == "The fair value is \$70, the trigger \$55."


def test_empty_stream_yields_nothing():
    assert list(escaped_stream(iter([]))) == []
