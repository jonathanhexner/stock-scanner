# Roadmap

One app: **learn → find → think → track**, with an *Ask* box on every screen and
a full **Chat** page where you pick an agent and the context it gets.

The product is not the screener. Screeners are commodities. The product is the
**thesis journal**: a place where Jonathan writes down why he'd own something,
what would prove him wrong, and then finds out. Everything else — lessons,
candidate list, portfolios, chat — exists to feed or check that journal.

Phases ship end-to-end. Finish one before starting the next.

---

## Design principles

1. **One app, one process.** A single Streamlit app with pages. No separate
   services, no API server, no frontend build step.
2. **One context engine, two front-ends.** *Ask* (a panel on every page,
   auto-scoped to what you're looking at) and *Chat* (a full page where you
   choose the agent and the context) are two views onto the same
   `AskContext` + agent registry. Never two prompt-building code paths.
3. **Context is composed from providers, not retrieved.** Each phase registers
   context providers (lessons, glossary, a company's numbers, a thesis, a
   filing section, a portfolio). Ask picks them automatically; Chat lets you
   pick them by hand. No RAG stack, no embeddings.
4. **Search GitHub before writing a module.** Prices, fundamentals, filings,
   ratios, investor-criteria scoring, portfolio schemas, lesson content — all of
   it already exists. Port or depend on it. Only the journal, the thesis-break
   check, the context engine, and the calibration view are ours. If a new module
   feels big, that's a signal someone has already published it.
5. **Agents teach and challenge; they do not advise.** They explain concepts,
   pull numbers, and argue the bear case. No agent outputs "buy" or "sell".
   Enforced in a shared system-prompt preamble every agent inherits.
6. **Local-only.** SQLite + Parquet on disk. No accounts, no cloud, no upload of
   holdings anywhere. (Same rule as the moneyman project.)

---

## Maximal reuse

**The standing rule: search GitHub before writing a module.** Nearly every part of
this app already exists as an open-source project. We are assembling, not
inventing. The only thing with no good off-the-shelf equivalent is the **thesis
journal with falsifiers** — so that is the only thing we build properly.

### Reuse from existing GitHub projects

| Need | Project | License / stack | What we take |
|---|---|---|---|
| Ratios, valuation models, portfolio performance | [JerBouma/FinanceToolkit](https://github.com/JerBouma/FinanceToolkit) | MIT · Python | 200+ ratios and models written out transparently — the formulas are readable, which is what a learner needs. **Verified to run with no API key** via `enforce_source="YahooFinance"`. Its `Portfolio` module also does Phase 5's return/alpha/beta/benchmark maths from a plain DataFrame. |
| Agent personas + LLM-layer architecture | [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | MIT · Python | The Graham / Buffett / Munger / Lynch personas are **pure system prompts** on a shared `LLMAgent` base — port them as Chat agents, stripping the buy/sell signal. Take the architecture too: prompt caching keyed on (agent, model, system, user), and the failure contract (data errors propagate, LLM failures abstain). **Not a source of deterministic screening code** — see `docs/frameworks.md`. |
| Filings | [dgunning/edgartools](https://github.com/dgunning/edgartools) | MIT · Python | 10-K/10-Q retrieval + section extraction (Risk Factors, MD&A) |
| Prices / quotes | `yfinance`, reached through FinanceToolkit | Apache-2.0 · Python | prices and fundamentals. No paid data provider and no API key — verified. |
| Broader data layer, if the above gets painful | [OpenBB](https://github.com/OpenBB-finance/OpenBB) Open Data Platform | **AGPL** · Python | one interface over many providers. Fine for personal local use; AGPL matters only if this is ever offered as a service. Heavy — adopt only when a concrete need appears. |
| Portfolio tracking + LLM chat on holdings | [investbrainapp/investbrain](https://github.com/investbrainapp/investbrain) | **CC-BY-NC** · Laravel/PHP | Already does multi-portfolio + an AI assistant grounded on holdings. Wrong stack to fork, non-commercial licence — **use it as the design reference** for the portfolio data model and the grounded-chat UX. Worth running once to see what good looks like. |
| Portfolio data model, importers | [ghostfolio/ghostfolio](https://github.com/ghostfolio/ghostfolio) | AGPL · TS | positions/activities schema, transaction import formats, benchmark comparison — as a reference, not a dependency |
| Learning content | [romainsimon/awesome-investing](https://github.com/romainsimon/awesome-investing) (free 14-lesson course), [Pamir/awesome-value-investment](https://github.com/Pamir/awesome-value-investment), [mr-karan/awesome-investing](https://github.com/mr-karan/awesome-investing), Damodaran's free NYU lectures + spreadsheets | curated links | **Curate, don't author.** Link out to existing lessons; we write only the connective tissue and the "try it on a real ticker" exercises. Never copy text from books or paid courses. |
| Indicators / charts / UI / storage | `ta` or a live `pandas-ta` fork, `plotly`, `streamlit`, SQLite | — | no custom indicator math, no web frontend, no ORM. NB: `pandas-ta` is unmaintained and no longer installable. |
| Ask / Chat | `anthropic` Python SDK, `claude-opus-5` | — | no RAG stack, no agent framework, no custom streaming layer |

### Reuse from Jonathan's existing work

| From | What we take |
|---|---|
| this repo (`stock-scanner`) | layout, `CLAUDE.md` conventions, `requirements.txt`, venv + Task Scheduler setup |
| Telegram bot (already wired; `.env` has token + chat id) | the digest and thesis-break alert channel — no new notification stack |
| `moneyman` | local-data-only posture; the "one scheduled job writes a file, one viewer reads it" shape; the Windows Task Scheduler recipe |
| Claude Code's own shape | agent-definitions-as-markdown-files: `config/agents/*.md` with YAML front-matter |

### What we actually build

Only these. Everything else is glue.

1. The **thesis journal**: versioned records, falsifiers, the critique flow.
2. The **thesis-break check**: does a recorded falsifier now hold?
3. The **context engine**: providers + agent registry that put the right facts in
   front of the right agent.
4. The **calibration view**: Real vs. Paper vs. Passed — was I right, and for the
   reason I thought?

### Phase 0 — spike (done, 2026-09-05)

Candidates were cloned and run. Full survey and compatibility ratings:
**[docs/frameworks.md](docs/frameworks.md)**. What it changed:

- [x] **FinanceToolkit runs with no API key** (`enforce_source="YahooFinance"`).
      Verified on KO. No FMP signup, no separate fundamentals provider.
- [x] **ai-hedge-fund has no deterministic scoring to port** — the investor
      personas are pure system prompts. It moves from Phase 4 to Phase 1: we take
      the prompts and the LLM-layer architecture (prompt cache, abstain-on-failure).
- [x] **FinanceToolkit's `Portfolio` module does Phase 5's maths** from a plain
      DataFrame — return, benchmark, volatility, alpha, beta, weights. Verified.
      Gotchas: the ticker column must be named `Identifier`, and a missing
      `Currency` column silently defaults to EUR.
- [x] **edgartools 5.56 imports clean**, XBRL included. Needs `set_identity(<your
      email>)` for live SEC calls — a config step, not a dependency.
- [x] **investbrain has no thesis table.** Nor does anything else found. The
      journal is confirmed as the gap worth building.
- [ ] Still open: pick the 8-10 lessons worth linking to from awesome-investing,
      and note which gaps we have to write ourselves. (Phase 2.)

---

## Phase 1 — The spine: context engine, agents, Ask + Chat  ✅ shipped 2026-09-06

Goal: `streamlit run app.py` opens a multi-page app with a working Chat page and
a working context-aware Ask panel on every other page. Later phases only add
*context providers* and pages — never new prompt plumbing.

**Context engine**

- [x] `src/ask/context.py` — `AskContext` dataclass: `title`, `facts` (dict),
      `documents` (list of labelled text blocks), `provider_ids`
- [x] `src/ask/providers.py` — provider registry. A provider is
      `id → (label, fn(selection) -> ContextBlock)`. Phase 1 ships two:
      `glossary` and `portfolio` (empty is fine). Later phases register more.
- [x] Context budget: providers declare a rough token cost; the assembler drops
      the lowest-priority blocks when the budget is exceeded and says so in the UI.
      Use `client.messages.count_tokens` to measure, never a tokenizer guess.

**Agents**

- [x] `config/agents/*.md` — one file per agent, YAML front-matter
      (`name`, `description`, `default_providers`, `effort`) + the system prompt body
- [x] `config/agents/_preamble.md` — inherited by every agent: the no-advice rule,
      "ground answers in supplied context, say when a number isn't there", and
      "Jonathan is learning — build the mental model, don't hand over conclusions"
- [x] `src/ask/agents.py` — load, validate, hot-reload on file change
- [x] Starter roster. Seed the investor personas from `ai-hedge-fund`'s prompts
      (MIT — keep the notice), rewritten to explain and question rather than to
      emit a signal. Take its prompt cache too — key on (agent, model, system,
      user) so an unchanged snapshot never pays for a second call:
  - **Tutor** — explains concepts from first principles, beginner-friendly
  - **Analyst** — pulls and explains one company's numbers and filings
  - **Graham** / **Buffett** — applies that investor's documented criteria to a
    company and shows its working. Reports what passes and fails, not what to do.
  - **Devil's Advocate** — attacks a thesis; assumptions, bear case, missing falsifiers
  - **Journal Coach** — helps write and tighten a thesis and its falsifiers
  - **Portfolio Reviewer** — concentration, overlap, thesis status across holdings

**Client**

- [x] `src/ask/client.py` — **read the `claude-api` skill before writing this.**
      Defaults: `model="claude-opus-5"`, `thinking={"type": "adaptive"}`, streaming via
      `client.messages.stream(...)` + `.get_final_message()`, `max_tokens=64000`.
      Per-agent `output_config={"effort": ...}` — `low` for glossary lookups,
      `high`/`xhigh` for thesis critique.
- [x] Prompt caching (breakpoint in place; cache_read not yet observed live): preamble + agent prompt + glossary + lesson corpus are the
      stable prefix (`cache_control`); selected context and the question come last.
      Verify `usage.cache_read_input_tokens > 0`.
- [x] `ANTHROPIC_API_KEY` in `.env`, documented in `.env.example`

**Front-ends**

- [x] `app.py` + `pages/` — Learn, Scan, Chat, Journal, Portfolio
- [x] `src/ask/panel.py` — the Ask panel: an expander on every page, agent chosen
      automatically for that page, context auto-scoped, history ephemeral
- [x] `pages/3_Chat.py` — the Chat page: persistent threads, agent switcher, and a
      context picker (multi-select over registered providers + the portfolio
      switcher). Shows exactly which blocks were sent — no invisible context.
- [ ] `@ticker` / `#thesis` mentions in the chat box pull that provider in mid-thread
- [ ] "Continue in Chat" button on the Ask panel — carries context and history over

**Storage**

- [x] `src/store/db.py` — SQLite schema, plain SQL, migrations by hand.
      Phase 1 tables: `portfolios`, `positions`, `chat_threads`, `chat_messages`,
      `lesson_progress`. (Theses land in Phase 3.)
- [x] `chat_threads` stores agent id + provider selection, so reopening a thread
      restores its context, not just its text
- [x] Verified in the browser: portfolios seed, a transaction persists and holdings
      derive from it, the Chat agent/context pickers work, and context is displayed
      before it is sent.
- [ ] **Still open:** one live API call, to confirm an answer streams and
      `cache_read_input_tokens > 0`. Costs money, so it needs a deliberate run.

## Phase 2 — Learn

Goal: a self-paced value-investing course inside the app, where every concept can
be interrogated and immediately tried on a real company.

- [ ] `content/lessons/*.md` — **curated, not authored.** Each lesson is a short
      framing paragraph we write, a link to the best existing free explanation
      (awesome-investing's course, Damodaran's lectures, Investopedia), and a
      *Try it* exercise. Never copy text from books or paid courses.
      Starter sequence:
      1. What "value" means; price vs. value; Mr. Market
      2. Reading the income statement, balance sheet, and cash flow statement
      3. Owner earnings and free cash flow
      4. Moats — what makes returns durable
      5. Multiples (P/E, EV/EBIT, P/B) and what each one hides
      6. Simple valuation: earnings power value, then a crude DCF
      7. Margin of safety and position sizing
      8. Circle of competence, and when to say "too hard"
      9. How to write a thesis and a falsifier — leads straight into Phase 3
- [ ] Each lesson ends with a **Try it** block: a ticker plus a question to answer in
      the journal ("compute owner earnings for KO — is it above or below net income?")
- [ ] `content/glossary.yaml` — term → one-line definition, rendered as tooltips
      wherever a metric name appears app-wide
- [ ] Register the `lesson` context provider → Tutor in Chat can be pointed at any lesson
- [ ] `reading.md` — pointers to primary sources (Graham, Buffett's letters, EDGAR).
      Links only; no reproduced text.
- [ ] Progress tracking: lesson read / Try-it completed

## Phase 3 — Journal (the core)

Goal: a structured, versioned record of every investment idea.

- [ ] Thesis record (SQLite, one row per version — append, never overwrite):
      `ticker`, `created_at`, `status` (watching / owned / passed / exited),
      `business_in_one_line`, `why_cheap`, `why_it_wont_stay_cheap`,
      `owner_earnings_estimate`, `fair_value_estimate`, `margin_of_safety_price`,
      `falsifiers` (list — "what would make me wrong"), `confidence` (1-5),
      `circle_of_competence` (bool + why), `sources` (URLs / filing sections)
- [ ] A thesis belongs to a portfolio (or to none — an idea you're still weighing)
- [ ] Guided thesis editor: one field at a time, glossary tooltips, drafts saved
- [ ] **Critique my thesis** — hands the draft plus the company's numbers to the
      Devil's Advocate. It scores nothing and recommends nothing.
- [ ] Thesis history view: diff between versions, so changed minds stay visible
- [ ] Filings tab per ticker via `edgartools`: latest 10-K/10-Q, Risk Factors and MD&A
- [ ] Register `thesis` and `filing` context providers
- [ ] Export a thesis to Markdown

## Phase 4 — Scan (thin)

Goal: a candidate list that hands you into the journal. Deliberately dumb.

- [ ] `config/universes/*.csv` — screener exports dropped in by hand
- [ ] `src/data/fetcher.py` + `src/data/cache.py` — yfinance fetch, Parquet cache
      (fundamentals 24h, prices 1h)
- [ ] Ratios come from `FinanceToolkit` (`enforce_source="YahooFinance"`, no key) —
      do not implement a single formula ourselves
- [ ] `src/screening/value.py` — thresholds applied to those ratios. Written by us:
      the spike found no deterministic value-screening code worth porting. Returns
      pass/fail **with reasons and the numbers behind them**; a rough sort, not a
      ranking that pretends to be precise.
- [ ] `config/value_criteria.yaml` — thresholds surfaced as config so they're tunable
- [ ] Scan page: table with per-row "Ask about this company" and **"Start a thesis"**
- [ ] Candidate detail view: fundamentals + price chart (plotly, `pandas_ta`)
- [ ] Register the `company` context provider (fundamentals + price history)
- [ ] Explicit UI copy: the scan is a starting point for reading, not a recommendation

## Phase 5 — Track (multiple portfolios)

Goal: hold yourself accountable to what you wrote — across real money, paper
ideas, and the ones you passed on.

- [ ] `portfolios` table: `id`, `name`, `kind` (real / paper / watchlist),
      `base_currency`, `benchmark` (default SPY), `created_at`, `notes`.
      Positions and theses carry `portfolio_id`.
- [ ] Starter set: **Real**, **Paper** (ideas you'd have bought), **Passed**
      (ideas you rejected — this is where calibration is actually learned)
- [ ] Portfolio switcher in the sidebar; an "All portfolios" aggregate view
- [ ] Positions table per portfolio: ticker, shares, cost basis, date, and a link
      to the thesis version that justified the buy. Hand-entered; no brokerage
      integration.
- [ ] Performance vs. each portfolio's benchmark from entry dates — hand the
      transactions to `FinanceToolkit`'s `Portfolio` as a DataFrame and read back
      return, alpha, beta, volatility and weights. Column must be `Identifier`;
      always set `Currency` or it silently assumes EUR.
- [ ] **Compare view** — Real vs. Paper vs. Passed vs. benchmark. Did the ideas you
      skipped beat the ones you bought?
- [ ] The `portfolio` context provider becomes real: the Portfolio Reviewer agent
      sees holdings, weights, sector concentration, and each holding's current
      thesis and falsifier status. Chat's context picker can select one portfolio,
      several, or all.
- [ ] **Thesis-break check** — a scheduled job re-pulls fundamentals and asks, per
      holding: has any recorded falsifier tripped? Output is a flag plus the numbers,
      never "sell".
- [ ] Quarterly review prompt: for each holding, re-read the thesis and re-answer
      "would I buy this today at this price?" — recorded as a new thesis version
- [ ] `scripts/daily_check.py` — thesis-break check across all portfolios plus a short
      Telegram digest grouped by portfolio (reuse the existing bot). Under 4096 chars.
- [ ] Windows Task Scheduler recipe verified and documented

## Phase 6 — Commute mode (audio + phone)

Goal: the commute becomes study time. Listening is the primary mode here, so the
output is **pre-generated audio**, not live conversation — see the constraint below.

**Daily audio brief (the main thing)**

- [ ] `src/reporting/brief.py` — compose a 3-5 minute script from data we already
      have: what moved and why, any falsifier that tripped, one lesson segment from
      `content/lessons/`, and one open question from the journal ("you still haven't
      written a falsifier for X")
- [ ] TTS via `edge-tts` (free, no API key, natural voices) or `piper` (fully local,
      no network). Do not build a TTS layer.
- [ ] Delivery: **Telegram voice note** through the existing bot (`sendVoice`).
      Outbound only — nothing on this machine is exposed to the internet. This is
      the default and it needs no new infrastructure.
- [ ] Written to `data/briefs/YYYY-MM-DD.mp3` so a bad brief can be replayed and
      the script inspected
- [ ] Optional: a private podcast RSS feed over the same MP3s, if he'd rather use a
      podcast app than Telegram. Needs somewhere to host the files — only if wanted.

**Ask it things from the phone**

- [ ] `scripts/mcp_server.py` — a **read-only** MCP server exposing
      `get_portfolio`, `get_thesis`, `falsifier_status`, `list_lessons`, `explain_term`.
      No write tools; the no-advice preamble is repeated in every tool description.
- [ ] Add it to Claude as a custom connector (works on Claude mobile, all plans).
      ChatGPT can take a remote MCP connector too.
- [ ] Exposure: requires a public HTTPS URL — Cloudflare Tunnel or Tailscale Funnel.
      **This is the one place the local-only rule bends,** so: read-only tools, a
      shared-secret header, and holdings behind an explicit opt-in flag (default off,
      lessons and glossary only).

**Known constraint — don't design around a feature that doesn't exist**

MCP tools are not available inside voice-mode conversations in either Claude or
ChatGPT. "Talk to my portfolio hands-free while driving" is not currently
possible. Text chat on mobile works fine; the driving experience is the
pre-generated audio brief. Re-check this before building the MCP half.

## Phase 7 — Later (don't start before 1-6 ship)

- [ ] Backtest the journal, not the screener: how did *my* theses do, and were my
      falsifiers the things that actually broke?
- [ ] Calibration scorecard: confidence rating vs. realized outcome, Real vs. Passed
- [ ] Custom agents: a UI for adding a `config/agents/*.md` file without a text editor
- [ ] Sector-relative screening
- [ ] Watchlist alerts when price reaches a recorded margin-of-safety price
- [ ] Move the scheduled job off the laptop (GitHub Actions)

---

## Out of scope

- Brokerage / trading integration, options, ML price prediction, mobile app
- Any output that constitutes a buy/sell/hold recommendation or personalized advice
- Multi-user, accounts, hosting, or anything that puts holdings on someone's server
- Agents that act — every agent reads context and writes text. Nothing places
  orders, edits a thesis without confirmation, or changes a portfolio on its own.
- A "better" screener — if the screening feels weak, the answer is to read more
  filings, not to add factors
