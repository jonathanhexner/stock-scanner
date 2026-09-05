# stock-scanner

A personal value-investing workbench: one Streamlit app that teaches the
fundamentals, surfaces candidates, and — the point of the whole thing — keeps a
versioned **thesis journal** for every idea, so you record why you'd own
something and what would prove you wrong, then find out.

An *Ask* panel sits on every page, pre-loaded with that page's context (the
lesson, the company's numbers, the thesis you're drafting, your positions), and
a full **Chat** page lets you pick an agent — Tutor, Analyst, Devil's Advocate,
Journal Coach, Portfolio Reviewer — and choose exactly what context it sees,
including which of your portfolios. They teach and argue the bear case; they
never give buy/sell advice.

Five surfaces: **Learn**, **Scan**, **Chat**, **Journal**, **Portfolio**.
Portfolios are plural by design — real money, paper ideas, and the ones you
passed on, so you can see which set actually did better.

Built to run locally on Windows. Your holdings never leave the machine.

## Quick start

```powershell
# from the repo root
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# interactive dashboard
streamlit run app.py

# one-off thesis-break check + digest
python scripts/daily_check.py
```

To schedule the daily check:

1. Open **Task Scheduler** (Win+R → `taskschd.msc`).
2. Create Basic Task → daily at e.g. 17:30 (after US market close).
3. Action: Start a program → `C:\Users\<you>\stock-scanner\.venv\Scripts\python.exe`
4. Arguments: `scripts\daily_check.py`
5. Start in: `C:\Users\<you>\stock-scanner`

## What's where

| Path | What it holds |
|------|---------------|
| `app.py` | Streamlit entry point |
| `pages/` | Learn, Scan, Chat, Journal, Portfolio |
| `content/` | Course lessons (markdown) + glossary |
| `src/ask/` | Context providers, agent registry, Ask panel, Anthropic client |
| `src/store/` | SQLite — portfolios, positions, theses, chat threads, progress |
| `scripts/daily_check.py` | Task-Scheduler entry — thesis-break check + Telegram digest |
| `src/data/` | Data fetching + caching (yfinance, edgartools for filings) |
| `src/screening/` | Value-investing filters (deliberately coarse) |
| `src/analysis/` | Technical indicators for the detail view |
| `src/reporting/` | Telegram sender, report formatting |
| `config/` | `agents/` (one .md per agent), universes, criteria — edit without code changes |
| `data/` | Local cache + `journal.sqlite` (gitignored) |
| `tests/` | Unit tests, focused on the screening logic |
| `CLAUDE.md` | Guidance for Claude Code agents |
| `ROADMAP.md` | Phased plan — what's done, what's next |

## Working with Claude Code

This project has a `CLAUDE.md` that briefs any Claude Code session on the goals,
stack, conventions, and out-of-scope items. When you open Claude Code here,
just start asking for the next thing in `ROADMAP.md` — the agent will pick up
the context automatically.

## Stack

Python · streamlit · pandas · yfinance · edgartools · FinanceToolkit · pandas_ta · plotly · anthropic · SQLite

Assembled from existing open-source work wherever possible — see
[THIRD_PARTY.md](THIRD_PARTY.md) for what we depend on, port, or reference, and
`ROADMAP.md` for the reuse table. We build four things ourselves: the thesis
journal, the thesis-break check, the context engine, and the calibration view.

## License

Personal use. Not investment advice — this is a learning and record-keeping tool.

## Testing

```bash
pytest
ruff check .
```

Both run in CI on every push. A phase is not done until they pass.
