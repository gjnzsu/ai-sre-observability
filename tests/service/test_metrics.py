"""Tests for Prometheus metrics registry."""

from service.metrics import MetricsRegistry


OWNERSHIP = {
    "consumer": "ai-market-studio",
    "application": "ai-market-studio",
    "project": "fx-market-insight",
    "team": "markets",
    "use_case": "fx-data-query",
    "feature": "query-result-generation",
}


def test_track_llm_request():
    """Test tracking LLM request increments counter."""
    registry = MetricsRegistry()

    registry.track_llm_request(
        service="chat-api",
        provider="openai",
        model="gpt-4",
        status="success",
        ownership=OWNERSHIP,
    )

    samples = list(registry.llm_requests_total.collect())[0].samples

    found = False
    for sample in samples:
        if (
            sample.labels.get("service") == "chat-api"
            and sample.labels.get("provider") == "openai"
            and sample.labels.get("model") == "gpt-4"
            and sample.labels.get("consumer") == "ai-market-studio"
            and sample.labels.get("use_case") == "fx-data-query"
            and sample.labels.get("feature") == "query-result-generation"
            and sample.labels.get("status") == "success"
        ):
            assert sample.value == 1.0
            found = True
            break

    assert found, "Expected metric sample not found"


def test_track_llm_tokens():
    """Test tracking LLM tokens."""
    registry = MetricsRegistry()

    registry.track_llm_tokens(
        service="chat-api",
        provider="openai",
        model="gpt-4",
        token_type="prompt",
        count=100,
        ownership=OWNERSHIP,
    )

    samples = list(registry.llm_tokens_total.collect())[0].samples

    found = False
    for sample in samples:
        if (
            sample.labels.get("service") == "chat-api"
            and sample.labels.get("provider") == "openai"
            and sample.labels.get("model") == "gpt-4"
            and sample.labels.get("consumer") == "ai-market-studio"
            and sample.labels.get("use_case") == "fx-data-query"
            and sample.labels.get("feature") == "query-result-generation"
            and sample.labels.get("token_type") == "prompt"
        ):
            assert sample.value == 100.0
            found = True
            break

    assert found, "Expected metric sample not found"


def test_track_llm_cost():
    """Test tracking LLM cost."""
    registry = MetricsRegistry()

    registry.track_llm_cost(
        service="chat-api",
        provider="openai",
        model="gpt-4",
        cost_usd=0.05,
        ownership=OWNERSHIP,
    )

    samples = list(registry.llm_token_cost_usd_total.collect())[0].samples

    found = False
    for sample in samples:
        if (
            sample.labels.get("service") == "chat-api"
            and sample.labels.get("provider") == "openai"
            and sample.labels.get("model") == "gpt-4"
            and sample.labels.get("consumer") == "ai-market-studio"
            and sample.labels.get("use_case") == "fx-data-query"
            and sample.labels.get("feature") == "query-result-generation"
        ):
            assert sample.value == 0.05
            found = True
            break

    assert found, "Expected metric sample not found"


def test_track_llm_cost_defaults_unknown_ownership_labels():
    """Test legacy LLM cost calls remain compatible with default labels."""
    registry = MetricsRegistry()

    registry.track_llm_cost(
        service="chat-api",
        provider="openai",
        model="gpt-4",
        cost_usd=0.05,
    )

    samples = list(registry.llm_token_cost_usd_total.collect())[0].samples
    found = False
    for sample in samples:
        if (
            sample.labels.get("service") == "chat-api"
            and sample.labels.get("provider") == "openai"
            and sample.labels.get("model") == "gpt-4"
        ):
            assert sample.labels.get("consumer") == "unknown"
            assert sample.labels.get("application") == "unknown"
            assert sample.labels.get("use_case") == "unknown"
            assert sample.labels.get("feature") == "unknown"
            assert sample.value == 0.05
            found = True
            break

    assert found, "Expected metric sample not found"


def test_track_business_metric():
    """Test tracking low-cardinality business metrics."""
    registry = MetricsRegistry()

    registry.track_business_metric(
        service="ai-market-studio",
        metric_name="ai_cost_attribution_requests_total",
        value=1,
        labels={
            "application": "ai-market-studio",
            "project": "fx-market-insight",
            "team": "markets",
            "use_case": "fx-data-query",
            "feature": "query-result-generation",
            "model": "gpt-4o",
            "status": "success",
            "tool_used": "collect_market_context",
        },
    )

    samples = list(registry.business_metric_total.collect())[0].samples
    found = False
    for sample in samples:
        if (
            sample.labels.get("service") == "ai-market-studio"
            and sample.labels.get("metric_name") == "ai_cost_attribution_requests_total"
            and sample.labels.get("use_case") == "fx-data-query"
            and sample.labels.get("feature") == "query-result-generation"
        ):
            assert sample.value == 1.0
            found = True
            break

    assert found, "Expected business metric sample not found"
