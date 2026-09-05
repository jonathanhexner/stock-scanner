"""Scheduled entry point. Run via Task Scheduler or on demand.

Pipeline (see ROADMAP.md, Phase 5):
    1. Load open positions and their current thesis versions (src.store)
    2. Re-fetch fundamentals for each holding (src.data.fetcher)
    3. Evaluate recorded falsifiers — has any of them tripped?
    4. Persist the check result so the Portfolio page can show it
    5. Send a short Telegram digest: flags + the numbers behind them

Never emits a buy/sell recommendation. It reports whether what Jonathan wrote
down as "this would prove me wrong" has happened.
"""

from __future__ import annotations


def main() -> None:
    raise NotImplementedError("See ROADMAP.md, Phase 5.")


if __name__ == "__main__":
    main()
