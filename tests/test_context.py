from src.ask.context import AskContext, ContextBlock


def block(label, body, priority=50, provider_id="p"):
    return ContextBlock(provider_id=provider_id, label=label, body=body, priority=priority)


def test_render_labels_each_block_and_names_its_source():
    ctx = AskContext(title="KO", blocks=[block("Glossary", "P/E: price over earnings")])

    rendered = ctx.render()

    assert 'source="p"' in rendered
    assert 'label="Glossary"' in rendered
    assert "P/E: price over earnings" in rendered


def test_render_is_explicit_when_there_is_no_context():
    assert "No context" in AskContext(title="nothing").render()


def test_fit_keeps_high_priority_blocks_and_reports_what_it_dropped():
    ctx = AskContext(
        title="KO",
        blocks=[
            block("Glossary", "x" * 100, priority=10),
            block("Portfolios", "y" * 100, priority=80),
        ],
    )

    fitted = ctx.fit(budget=100)

    assert [b.label for b in fitted.blocks] == ["Portfolios"]
    assert fitted.dropped == ["Glossary"]


def test_fit_preserves_insertion_order_among_kept_blocks():
    ctx = AskContext(
        title="KO",
        blocks=[
            block("first", "a", priority=10),
            block("second", "b", priority=90),
        ],
    )

    assert [b.label for b in ctx.fit(budget=1000).blocks] == ["first", "second"]


def test_fit_within_budget_drops_nothing():
    ctx = AskContext(title="KO", blocks=[block("a", "x" * 10), block("b", "y" * 10)])

    fitted = ctx.fit(budget=1000)

    assert len(fitted.blocks) == 2
    assert fitted.dropped == []


def test_fit_does_not_mutate_the_original():
    ctx = AskContext(title="KO", blocks=[block("a", "x" * 100), block("b", "y" * 100)])

    ctx.fit(budget=100)

    assert len(ctx.blocks) == 2
    assert ctx.dropped == []


def test_provider_ids_lists_every_contributing_provider():
    ctx = AskContext(
        title="KO",
        blocks=[block("a", "x", provider_id="glossary"), block("b", "y", provider_id="portfolio")],
    )

    assert ctx.provider_ids == ["glossary", "portfolio"]
