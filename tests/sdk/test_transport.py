"""Unit tests for SDK async transport."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from sdk.ai_sre_observability.models import LLMCallMetric, MetricPayload
from sdk.ai_sre_observability.transport import AsyncTransport


@pytest.mark.asyncio
async def test_send_metric_success():
    """Test sending metric successfully."""
    transport = AsyncTransport(observability_url="http://localhost:8000")

    metric = MetricPayload(
        service_name="test-service",
        metric_type="llm_call",
        trace_id="test-trace-123",
        timestamp=datetime.utcnow(),
        data={
            "provider": "openai",
            "model": "gpt-4",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "duration_seconds": 1.5,
            "status": "success"
        }
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "ok"}

        result = await transport.send_metric(metric)

        assert result is True
        mock_post.assert_called_once()

    await transport.close()


@pytest.mark.asyncio
async def test_send_metric_failure_graceful():
    """Test sending metric fails gracefully (returns False, no exception)."""
    transport = AsyncTransport(observability_url="http://localhost:8000")

    metric = MetricPayload(
        service_name="test-service",
        metric_type="llm_call",
        trace_id="test-trace-456",
        timestamp=datetime.utcnow(),
        data={"provider": "openai"}
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Network error")

        result = await transport.send_metric(metric)

        assert result is False

    await transport.close()


@pytest.mark.asyncio
async def test_send_batch():
    """Test sending batch of metrics."""
    transport = AsyncTransport(observability_url="http://localhost:8000")

    metrics = [
        MetricPayload(
            service_name="test-service",
            metric_type="llm_call",
            trace_id=f"test-trace-{i}",
            timestamp=datetime.utcnow(),
            data={"provider": "openai", "model": "gpt-4"}
        )
        for i in range(3)
    ]

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "ok"}

        results = await transport.send_batch(metrics)

        assert len(results) == 3
        assert all(result is True for result in results)
        assert mock_post.call_count == 3

    await transport.close()
