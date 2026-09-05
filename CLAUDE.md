# CLAUDE.md — Stock Scanner Project

Guidance for Claude Code (and any other agent) working in this repo. Read this first.

## What we are building

A personal **value-investing workbench** for Jonathan — one Streamlit app that teaches, screens, records, and tracks. Five surfaces:

1. **Learn** — a self-paced value-investing course (short lessons we write, plus a glossary), where every concept can be tried immediately on a real company.
2. **Scan** — a deliberately thin candidate list. Coarse filters over a hand-dropped universe, with reasons attached. It exists to hand you into the journal, not to rank stocks precisely.
3. **Chat** — a full chat page with persistent threads, a switchable **agent** (Tutor, Analyst, Devil's Advocate, Journal Coach, Portfolio Reviewer) and an explicit **context picker**, including which portfolio(s) the agent can see.
4. **Journal** — **the core of the product.** A structured, versioned thesis per idea: why it's cheap, why that won't last, what fair value looks like, and — critically — what would prove the thesis wrong.
5. **Portfolio** — **multiple** portfolios (real / paper / passed-on), hand-entered positions linked to the thesis version that justified them, a scheduled thesis-break check, and a Telegram digest.

Cutting across all of them: an **Ask panel on every page**, pre-loaded with that page's context — the same engine as Chat, just auto-scoped instead of hand-picked.

The screener is a commodity; the journal is not. When in doubt about where to spend effort, spend it on the journal and on Ask's context quality.

It must be runnable on-demand, not only on schedule.

`ROADMAP.md` holds the phased plan and the reuse table (what we take from Jonathan's other projects, and what we take off the shelf instead of building). Read it before starting work.

## Stack

- **Language:** Python 3.11+
- **Data:** start with [`yfinance`](https://pypi.org/project/yfinance/) for ease; consider [`OpenBB`](https://github.com/OpenBB-finance/OpenBB) when fundamentals become a bottleneck. Always cache to a local Parquet/SQLite store (in `data/`) so we don't hammer providers.
- **Filings:** `edgartools` for 10-K/10-Q retrieval and section extraction. Do not write an EDGAR client.
- **Ask (LLM):** the official `anthropic` Python SDK, model `claude-opus-5`. **Read the bundled `claude-api` skill before writing any Anthropic call** — the API has drifted and training-recalled patterns are stale.
- **Journal storage:** SQLite at `data/journal.sqlite`, plain SQL, no ORM.
- **Screening & analytics:** `pandas`, `numpy`
- **Technicals:** `pandas_ta` (or `ta`) — RSI, MACD, SMA/EMA, Bollinger, ADX, etc.
- **Charts:** `plotly`
- **UI:** `streamlit`
- **Scheduling:** Windows Task Scheduler (user is on Windows 10) for local; GitHub Actions if we move to cloud
- **Notifications:** Telegram bot first (cheap and already wired for the user), email second
- **Config:** `.env` for secrets, `pydantic-settings` or plain `os.environ`. Watchlists / criteria thresholds live in `config/` as YAML/JSON so they're editable without code changes.

## Project layout

```
stock-scanner/
├── CLAUDE.md            (this file)
├── README.md            (human-facing setup + usage)
├── ROADMAP.md           (phased plan — update as we ship)
├── requirements.txt
├── .env.example
├── .gitignore
├── app.py               (Streamlit entry point)
├── pages/               (Learn, Scan, Chat, Journal, Portfolio — Streamlit multipage)
├── content/
│   ├── lessons/         (course content, markdown — written by us)
│   └── glossary.yaml    (term → one-line definition)
├── src/
│   ├── ask/             (AskContext, provider registry, agent registry, panel, client)
│   ├── store/           (SQLite: portfolios, positions, theses, threads, progress)
│   ├── data/            (fetchers, caching, universe definitions, filings)
│   ├── screening/       (value-investing rules)
│   ├── analysis/        (technical indicators, detail-view logic)
│   └── reporting/       (telegram, report formatting)
├── scripts/
│   └── daily_check.py   (entry point for scheduled run: thesis-break check + digest)
├── data/                (cache + journal.sqlite — gitignored)
├── config/
│   ├── agents/          (one .md per agent + _preamble.md — add agents without code)
│   ├── universes/       (screener CSV exports, dropped in by hand)
│   └── value_criteria.yaml
└── tests/
```

Each `src/<area>/` is a small package. Keep modules **flat and focused** — one job per module.

## Value-investing criteria (starting point — refine with the user)

Classic Graham/Buffett-style filters; tune in `config/value_criteria.yaml`:

- **Profitability:** ROE > 10%, ROIC > 8%, positive net income last 3 years
- **Valuation:** P/E < 20 (or below sector median), P/B < 3, EV/EBITDA < 12
- **Quality / safety:** Debt/Equity < 1, current ratio > 1.5, interest coverage > 5
- **Cash:** positive free cash flow over last 3 years, FCF yield > 5%
- **Growth (mild):** revenue & EPS CAGR > 5% over 5 years
- **Margin of safety:** simple DCF or earnings-power-value estimate vs market cap

Output a **composite score** (e.g., normalized rank across criteria) so we get a ranked list, not just a boolean filter. Ranking matters more than passing/failing every check.

Track *why* each candidate ranked where it did — surfaces in the report and the dashboard.

## Coding conventions

- **No premature abstraction.** This is a personal tool. Three similar lines beats a clever generic base class. If we duplicate something twice, leave it; refactor on the third.
- **Type hints encouraged**, especially on public functions and dataclasses.
- **Dataclasses or pydantic models** for structured records (e.g. `Candidate`, `Fundamentals`, `PriceBar`). Keep them in the module that owns them; don't build a "models" megapackage.
- **No comments explaining what the code does** — names should carry that. Only comment a non-obvious *why*.
- **Errors:** fail loud. If a data fetch returns nothing for a ticker, log it and skip — don't silently fill with NaN.
- **Caching:** every external API call goes through a cache layer (`src/data/cache.py`). Default TTL: fundamentals 24h, prices 1h, news 15m. Use `data/cache.sqlite` or Parquet files keyed by ticker + endpoint + date.
- **Logging:** standard `logging` module, INFO by default. Don't `print`.
- **Tests:** `pytest`, run with a bare `pytest` from the repo root (config in `pyproject.toml`). Keep the suite small and fast — it should stay under a second. Test the deterministic parts: agent/config parsing, context assembly and its budget, screening logic, thesis-break evaluation. Do not unit-test the data layer beyond a smoke test, and do not mock the Anthropic API into a fake conversation — test the request we build, not the reply we imagine.
- **Some tests assert on the shipped config, not fixtures.** `tests/test_agents.py` checks that the real `config/agents/*.md` parse and that the preamble still carries the no-advice rule. That rule silently disappearing is the worst failure this project has, so it has a test. Keep it that way.
- **A phase is not done until its tests pass and `ruff check .` is clean.** CI runs both on every push (`.github/workflows/ci.yml`).

## How to run

```powershell
# one-time
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # then fill in values

# interactive dashboard
streamlit run app.py

# on-demand scan
python scripts/daily_scan.py

# scheduled — register with Windows Task Scheduler pointing at scripts/daily_scan.py
```

## When the user asks for changes

- **Search GitHub before writing a module.** This is the project's first rule, not a nicety. Ratios, investor-criteria scoring, filings parsing, portfolio schemas, lesson content — all of it exists. Port it or depend on it, and record the source and licence in `THIRD_PARTY.md`. See the reuse table in `ROADMAP.md` for the shortlist already vetted. If a proposed module feels big, that's the signal to go looking again.
- **We build four things:** the thesis journal, the thesis-break check, the context engine, and the calibration view. Everything else is glue. Be suspicious of any task that isn't one of those.
- **Stay small.** Build the simplest version that works end-to-end first, then iterate. The roadmap in `ROADMAP.md` lists phases — finish the current phase before reaching into the next.
- **Don't add data providers we don't need.** yfinance covers ~80% of what value screening requires for free. Don't pull in OpenBB (AGPL, heavy) until a concrete metric is missing.
- **Ported code keeps its notice.** `ai-hedge-fund` and `FinanceToolkit` are MIT — keep the copyright notice on anything derived from them.
- **Confirm before destructive moves.** Wiping `data/cache.sqlite`, force-pushing, changing the screening logic in a way that throws out a prior backtest — ask first.
- **Update `ROADMAP.md`** when you finish a phase or add scope. Treat it as the source of truth for "what's next."

## The Ask/Chat layer

**One engine, two front-ends.** *Ask* is a panel on every page with context auto-scoped to what you're looking at. *Chat* is a full page where you pick the agent and the context by hand, with persistent threads. Both go through the same `AskContext` + agent registry — **never write a second prompt-building path.**

- **Context comes from providers, not retrieval.** `src/ask/providers.py` holds a registry: `id → (label, fn(selection) -> ContextBlock)`. Each phase registers more (`glossary`, `portfolio`, then `lesson`, `thesis`, `filing`, `company`). Ask selects providers automatically; Chat exposes them as a multi-select. No embeddings, no RAG.
- **Agents are files, not code.** `config/agents/*.md`, YAML front-matter (`name`, `description`, `default_providers`, `effort`) plus the system prompt body. Adding an agent must never require a code change.
- **Show the context.** The Chat page displays which blocks were sent. Never send invisible context.
- **Portfolio context is explicit and multi-select.** An agent sees the portfolio(s) the user selected — one, several, or all — never "whatever was lying around in session state".

Hard rules in `config/agents/_preamble.md`, inherited by every agent:

- **They teach and challenge; they never advise.** No buy/sell/hold, no "this is a good investment", no price target framed as a recommendation. Explaining how *Jonathan* would compute one is fine.
- **They argue the other side.** The "critique my thesis" flow is adversarial by design: unstated assumptions, bear case, missing falsifiers.
- **They ground answers in the supplied context** and say when a number isn't there rather than recalling one.
- **They read and write text; they never act.** No agent edits a thesis, changes a portfolio, or triggers a job on its own.

Jonathan is learning. Prefer explanations that build the mental model over answers that hand him a conclusion.

## Telegram delivery

The user already has a Telegram bot wired up (verified May 2026). For the report sender:

1. Read `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from `.env`.
2. Format the report as Markdown — bullet list of top N tickers with score, key metrics, and a short rationale per ticker.
3. Send via the `python-telegram-bot` library or a raw `requests.post` to the Bot API (the latter is fewer deps).

Keep messages under Telegram's 4096-char limit — chunk if needed.

## Out of scope (for now)

- Live trading / brokerage integration
- Options data
- Backtesting (revisit in Phase 6 — and then backtest *the journal*, not the screener)
- Mobile app (the Telegram digest is the mobile UX)
- Machine learning models (this is a workbench for judgment, not a quant fund)
- Multi-user, accounts, hosting — holdings never leave the machine
- A more elaborate screener. If the screening feels weak, read more filings; don't add factors.

If the user asks for one of these, build the simpler scoped version first and call out the expansion in `ROADMAP.md`.
