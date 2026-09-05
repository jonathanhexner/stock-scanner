# Framework survey — what exists, per phase

Phase 0 output. Candidates were cloned and, where possible, actually run — not
judged from their READMEs. Verified 2026-09-05 on Python 3.14 / Windows.

**Compatibility ratings**

| Rating | Meaning |
|---|---|
| **Drop-in** | Add as a dependency and use. No porting. |
| **Port** | Copy code or prompts into our repo, with attribution. |
| **Reference** | Read it, copy the design, don't take the code (wrong stack or licence). |
| **Reject** | Looked relevant, isn't. |

---

## Phase 1 — Spine (context engine, agents, Ask + Chat)

| Candidate | Licence · stack | Compatibility | Finding |
|---|---|---|---|
| [ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | MIT · Python | **Port + Reference** | Investor personas (`hedge_fund/signals/{graham,buffett,munger,lynch}.py`) are **pure system prompts** on a shared `LLMAgent` base — 50-60 lines each, no bespoke logic. Directly portable as our Chat personas. The architecture is the bigger prize: `PromptCache` keyed on (agent, model, system, user) so an unchanged snapshot never pays for a second LLM call, and an explicit failure contract — data errors propagate, LLM failures abstain. Adopt both. |
| [investbrain](https://github.com/investbrainapp/investbrain) | CC-BY-NC · Laravel | **Reference** | Its `agent_conversations` / `agent_conversation_messages` schema is almost exactly the thread model we specced, plus fields we'd missed: `tool_calls`, `tool_results`, `usage`, `attachments`, `meta`. Copy the shape. |
| LangChain / agent frameworks | — | **Reject** | We make one API call with assembled context. A framework adds indirection and nothing else. |

## Phase 2 — Learn

| Candidate | Licence · stack | Compatibility | Finding |
|---|---|---|---|
| [romainsimon/awesome-investing](https://github.com/romainsimon/awesome-investing) | curated links | **Reference** | Free 14-lesson course, beginner → advanced. Link to it; don't rewrite it. |
| [Pamir/awesome-value-investment](https://github.com/Pamir/awesome-value-investment), [mr-karan/awesome-investing](https://github.com/mr-karan/awesome-investing) | curated links | **Reference** | Source material for the reading list. |
| Damodaran (NYU) | free, public | **Reference** | Lectures and valuation spreadsheets. The best free valuation teaching there is. |

**No framework exists for this phase, and none should.** Curate and link; we write
only the framing paragraph and the "try it on a real ticker" exercise per lesson.

## Phase 3 — Journal

| Candidate | Compatibility | Finding |
|---|---|---|
| investbrain | **Reject** | Portfolios, holdings, transactions, AI chat — **no thesis or notes-per-holding table at all.** |
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) | **Reject** | *Generates* investment theses with agents. Does not help a human write one or hold them to it. |
| [openInvest](https://github.com/longsizhuo/openInvest) | **Reject** | Auditable verdicts for AI agents, not a human decision journal. |

**Confirmed gap.** Nothing found records a human's thesis with falsifiers and
checks them later. This is the one phase we build properly, and it's the reason
the project exists.

## Phase 4 — Scan

| Candidate | Licence · stack | Compatibility | Finding |
|---|---|---|---|
| [FinanceToolkit](https://github.com/JerBouma/FinanceToolkit) | MIT · Python | **Drop-in** ✅ verified | **Runs with no API key at all** — `Toolkit([...], enforce_source="YahooFinance")`. Smoke-tested on KO: ROE 43.2%, D/E 1.33 (FY2025), plus the full profitability and solvency sets including Interest Coverage and FCF Yield. Kills the FMP signup *and* the separate yfinance dependency for fundamentals. |
| [edgartools](https://github.com/dgunning/edgartools) | MIT · Python | **Drop-in** ✅ v5.56.0 imports clean; `Company`, `find`, `get_filings` and XBRL all present. Live SEC calls need `set_identity("<your email>")` — SEC requires a contact in the User-Agent. That's your config step. |
| ai-hedge-fund signals | MIT · Python | **Reject for screening** ⚠️ | **My earlier recommendation was wrong.** The repo was restructured — there are no deterministic Graham/Buffett ratio-scoring functions any more, only LLM prompts. Nothing to port for a deterministic screener. Use FinanceToolkit ratios + our own thresholds. |
| Screeni-py, AlphaSuite, assorted Streamlit dashboards | various | **Reject** | Technical/breakout screening or hobby dashboards. Not value screening. |

## Phase 5 — Track

| Candidate | Licence · stack | Compatibility | Finding |
|---|---|---|---|
| FinanceToolkit `Portfolio` | MIT · Python | **Drop-in** ✅ verified | Takes a plain **pandas DataFrame** of transactions — i.e. straight out of our SQLite — and returns positions overview, portfolio overview, and performance with return, benchmark return, volatility, alpha, beta and weights. Ran keyless against a 3-transaction test set with `benchmark_ticker="SPY"`. **Phase 5's maths is free.** Gotcha: required column is `Identifier` (not `Ticker`), and a missing `Currency` column silently defaults to **EUR** — always set it. |
| [ghostfolio](https://github.com/ghostfolio/ghostfolio) | AGPL · TS | **Reference** | Positions/activities schema and import formats. |
| investbrain | CC-BY-NC · Laravel | **Reference** | Confirms the right shape: **transactions are the source of truth, holdings are derived** (`average_cost_basis`, `total_cost_basis`, `realized_gain`, `dividends_earned`). Its `wishlist` boolean is a thin version of our real/paper/passed split. |

## Phase 6 — Commute (audio + phone)

| Candidate | Licence | Compatibility | Finding |
|---|---|---|---|
| [Piper](https://github.com/OHF-Voice/piper1-gpl) | **GPL-3.0** | **Drop-in, as a subprocess** | Fully offline neural TTS. The right choice for a brief that names your holdings — nothing leaves the machine. Invoke as a CLI, not as an imported library, to keep GPL away from this MIT repo. (The old MIT `rhasspy/piper` was archived Oct 2025; current development is GPL.) |
| `edge-tts` | — | **Limited** ⚠️ | Better voices, but it **streams your text to Microsoft's cloud service**. Fine for generic lesson audio, never for anything naming a position. |
| FinanceToolkit MCP, edgartools MCP, [many yfinance MCP servers](https://github.com/Alex2Yang97/yahoo-finance-mcp) | MIT | **Drop-in** | Market-data MCP already exists — FinanceToolkit and edgartools each ship one (edgartools also ships Claude Skills). We only need to write a small MCP server for **our journal and portfolios**, which nobody else has. |

---

## What changed as a result

1. **No FMP API key, and no separate fundamentals provider.** FinanceToolkit on
   the Yahoo source covers Phase 4.
2. **ai-hedge-fund moves from Phase 4 to Phase 1** — it's a source of agent
   prompts and LLM-layer architecture, not screening code.
3. **Phase 5 shrinks a lot.** We store transactions; FinanceToolkit computes the
   performance.
4. **Phase 6's market-data half is already built** by other people.
5. **Phase 3 is confirmed as the thing to build.** Nothing out there does it.
