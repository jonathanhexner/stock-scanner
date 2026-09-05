"""Making model output safe for Streamlit's markdown renderer.

Streamlit treats `$...$` as LaTeX. In an app whose whole subject is money, a
sentence like "$70 fair value against $55" gets swallowed and rendered as maths.
Escaping the dollar signs is the fix, and it has to happen mid-stream.
"""

from __future__ import annotations

from collections.abc import Iterator


def escape_money(text: str) -> str:
    r"""Escape `$` when it introduces an amount, so `$70` survives as `$70`.

    Only `$` followed by a digit is escaped — that is the money case and the
    only one that reliably opens a LaTeX span here. A lone `$` in prose or code
    is left alone, so `\$` never shows up inside a code block.
    """
    out = []
    for index, char in enumerate(text):
        if char == "$" and index + 1 < len(text) and text[index + 1].isdigit():
            out.append("\\$")
        else:
            out.append(char)
    return "".join(out)


def escaped_stream(chunks: Iterator[str]) -> Iterator[str]:
    """Escape amounts across chunk boundaries.

    A chunk can end on `$` with the digits arriving in the next one, so a
    trailing `$` is held back rather than emitted unescaped.
    """
    pending = ""
    for chunk in chunks:
        text = pending + chunk
        pending = ""
        if text.endswith("$"):
            text, pending = text[:-1], "$"
        if text:
            yield escape_money(text)
    if pending:
        yield pending
