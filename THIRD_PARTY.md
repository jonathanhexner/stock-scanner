# Third-party sources

Every external project we depend on, port from, or take as a design reference.
Add a row before merging anything derived from someone else's work.

| Project | Licence | How we use it | Attribution owed |
|---|---|---|---|
| [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | MIT | Graham/Buffett/Munger analyst scoring ported into `src/screening/` and the Chat agent personas. Buy/sell signal output removed. | Keep MIT notice in ported files |
| [JerBouma/FinanceToolkit](https://github.com/JerBouma/FinanceToolkit) | MIT | Dependency — ratios and valuation models | Standard dependency attribution |
| [dgunning/edgartools](https://github.com/dgunning/edgartools) | MIT | Dependency — filings retrieval and section extraction | Standard dependency attribution |
| `yfinance` | Apache-2.0 | Dependency — prices, basic fundamentals | Standard dependency attribution |
| [investbrainapp/investbrain](https://github.com/investbrainapp/investbrain) | CC-BY-NC | **Design reference only** — multi-portfolio model, grounded-chat UX. No code copied (wrong stack, non-commercial licence). | — |
| [ghostfolio/ghostfolio](https://github.com/ghostfolio/ghostfolio) | AGPL | **Design reference only** — positions/activities schema, import formats. No code copied. | — |
| [OpenBB](https://github.com/OpenBB-finance/OpenBB) | AGPL | Not currently used. If adopted: fine for local personal use; AGPL obligations bite only if this is ever offered as a service. | — |
| awesome-investing lists, Damodaran's NYU materials | varies | **Linked, never copied.** Lessons cite them; we write only framing and exercises. | Link with author credit |

Rule: we link to educational content, we do not reproduce it. No book text,
no paid-course material, in `content/` or in any prompt.
