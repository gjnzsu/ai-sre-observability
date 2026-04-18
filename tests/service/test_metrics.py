"""Tests for Prometheus metrics registry."""

import pytest
from service.metrics import MetricsRegistry


def test_track_llm_request():
    """Test tracking LLM request increments counter."""
    registry = MetricsRegistry()

    # Track a request
    registry.track_llm_request(
        service="openai",
        model="gpt-4",
        operation="chat_completion"
    )

    # Verify the counter was incremented
    metric = registry.llm_requests_total
    samples = list(metric.collect())[0].samples

    # Find the sample with our labels
    found = False
    for sample in samples:
        if (sample.labels.get('service') == 'openai' and
            sample.labels.get('model') == 'gpt-4' and
            sample.labels.get('operation') == 'chat_completion'):
            assert sample.value == 1.0
            found = True
            break

    assert found, "Expected metric sample not found"


def test_track_llm_tokens():
    """Test tracking LLM tokens."""
    registry = MetricsRegistry()

    # Track tokens
    registry.track_llm_tokens(
        service="openai",
        model="gpt-4",
        token_type="prompt",
        count=100
    )

    # Verify the counter was incremented
    metric = registry.llm_tokens_total
    samples = list(metric.collect())[0].samples

    # Find the sample with our labels
    found = False
    for sample in samples:
        if (sample.labels.get('service') == 'openai' and
            sample.labels.get('model') == 'gpt-4' and
            sample.labels.get('token_type') == 'prompt'):
            assert sample.value == 100.0
            found = True
            break

    assert found, "Expected metric sample not found"


def test_track_llm_cost():
    """Test tracking LLM cost."""
    registry = MetricsRegistry()

    # Track cost
    registry.track_llm_cost(
        service="openai",
        model="gpt-4",
        cost_usd=0.05
    )

    # Verify the counter was incremented
    metric = registry.llm_cost_usd_total
    samples = list(metric.collect())[0].samples

    # Find the sample with our labels
    found = False
    for sample in samples:
        if (sample.labels.get('service') == 'openai' and
            sample.labels.get('model') == 'gpt-4'):
            assert sample.value == 0.05
            found = True
            break

    assert found, "Expected metric sample not found"
