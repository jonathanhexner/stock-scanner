"""What an agent is allowed to know for one question.

Ask (auto-scoped to a page) and Chat (hand-picked) both build one of these and
hand it to the same client. There is exactly one place that turns facts into a
prompt, and this is the input to it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Rough budget for the context half of a request. Blocks beyond it are dropped,
# lowest priority first, and the UI is told which. Better a visibly trimmed
# context than a silently truncated one.
DEFAULT_BUDGET_CHARS = 200_000


@dataclass(frozen=True)
class ContextBlock:
    """One labelled piece of context from one provider."""

    provider_id: str
    label: str
    body: str
    priority: int = 50

    @property
    def size(self) -> int:
        return len(self.body)

    def render(self) -> str:
        open_tag = f'<context source="{self.provider_id}" label="{self.label}">'
        return f"{open_tag}\n{self.body}\n</context>"


@dataclass
class AskContext:
    title: str
    blocks: list[ContextBlock] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)

    def add(self, block: ContextBlock) -> None:
        self.blocks.append(block)

    @property
    def provider_ids(self) -> list[str]:
        return [b.provider_id for b in self.blocks]

    def fit(self, budget: int = DEFAULT_BUDGET_CHARS) -> AskContext:
        """Drop the lowest-priority blocks until the context fits.

        Higher `priority` wins. Ties keep insertion order, so a page's own
        subject stays ahead of background material it added afterwards.
        """
        ordered = sorted(enumerate(self.blocks), key=lambda p: (-p[1].priority, p[0]))
        kept: list[tuple[int, ContextBlock]] = []
        dropped: list[str] = []
        used = 0
        for index, block in ordered:
            if used + block.size <= budget:
                kept.append((index, block))
                used += block.size
            else:
                dropped.append(block.label)
        return AskContext(
            title=self.title,
            blocks=[b for _, b in sorted(kept, key=lambda p: p[0])],
            dropped=dropped,
        )

    def render(self) -> str:
        if not self.blocks:
            return "No context was supplied for this question."
        return "\n\n".join(b.render() for b in self.blocks)
