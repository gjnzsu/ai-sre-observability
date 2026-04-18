"""Unit tests for SDK ObservabilityClient."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from sdk.ai_sre_observability.client import ObservabilityClient, LLMCallTracker
from sdk.ai_sre_observability.models import MetricPayload


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initializes correctly."""
    client = ObservabilityClient(
        service_name="test-service",
        observability_url="http://localhost:8000"
    )

    assert client.service_name == "test-service"
    assert client.observability_url == "http://localhost:8000"
    assert client._batch == []
    assert client._batch_task is None

    await client.stop()


@pytest.mark.asyncio
async def test_track_llm_call_context_manager():
    """Test track_llm_call context manager."""
    client = ObservabilityClient(
        service_name="test-service",
        observability_url="http://localhost:8000"
    )

    with patch.object(client, '_add_to_batch') as mock_add:
        async with client.track_llm_call(provider="openai", model="gpt-4") as tracker:
            assert isinstance(tracker, LLMCallTracker)
            assert tracker.provider == "openai"
            assert tracker.model == "gpt-4"

            # Simulate LLM call
            tracker.prompt_tokens = 100
            tracker.completion_tokens = 50
            tracker.status = "success"

        # Verify metric was added to batch
        mock_add.assert_called_once()
        call_args = mock_add.call_args[0][0]
        assert call_args.metric_type == "llm_call"
        assert call_args.data["provider"] == "openai"
        assert call_args.data["model"] == "gpt-4"
        assert call_args.data["prompt_tokens"] == 100
        assert call_args.data["completion_tokens"] == 50
        assert call_args.data["status"] == "success"

    await client.stop()


@pytest.mark.asyncio
async def test_increment_metric():
    """Test increment counter metric."""
    client = ObservabilityClient(
        service_name="test-service",
        observability_url="http://localhost:8000"
    )

    with patch.object(client, '_add_to_batch') as mock_add:
        client.increment("api_calls", value=1, labels={"endpoint": "/health"})

        mock_add.assert_called_once()
        call_args = mock_add.call_args[0][0]
        assert call_args.metric_type == "counter"
        assert call_args.data["metric_name"] == "api_calls"
        assert call_args.data["value"] == 1
        assert call_args.data["labels"] == {"endpoint": "/health"}

    await client.stop()


@pytest.mark.asyncio
async def test_histogram_metric():
    """Test histogram metric."""
    client = ObservabilityClient(
        service_name="test-service",
        observability_url="http://localhost:8000"
    )

    with patch.object(client, '_add_to_batch') as mock_add:
        client.histogram("response_time", value=0.5, labels={"method": "GET"})

        mock_add.assert_called_once()
        call_args = mock_add.call_args[0][0]
        assert call_args.metric_type == "histogram"
        assert call_args.data["metric_name"] == "response_time"
        assert call_args.data["value"] == 0.5
        assert call_args.data["labels"] == {"method": "GET"}

    await client.stop()
