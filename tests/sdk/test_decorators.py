"""Unit tests for SDK decorators and public API."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sdk.ai_sre_observability.decorators import track_llm_call
from sdk.ai_sre_observability import setup_observability, get_client
from sdk.ai_sre_observability.client import ObservabilityClient


@pytest.mark.asyncio
async def test_track_llm_call_decorator():
    """Test @track_llm_call decorator tracks calls."""
    # Setup observability
    setup_observability(
        service_name="test-service",
        observability_url="http://localhost:8000"
    )

    client = get_client()

    # Mock the track_llm_call context manager
    mock_tracker = MagicMock()
    mock_tracker.prompt_tokens = 0
    mock_tracker.completion_tokens = 0

    with patch.object(client, 'track_llm_call') as mock_track:
        mock_track.return_value.__aenter__.return_value = mock_tracker
        mock_track.return_value.__aexit__.return_value = None

        # Define a decorated function
        @track_llm_call(provider="openai", model="gpt-4")
        async def call_llm(prompt: str):
            # Simulate LLM response with usage
            return {
                "content": "Hello!",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5
                }
            }

        # Call the decorated function
        result = await call_llm("Hi")

        # Verify decorator called track_llm_call
        mock_track.assert_called_once_with("openai", "gpt-4")

        # Verify token counts were extracted
        assert mock_tracker.prompt_tokens == 10
        assert mock_tracker.completion_tokens == 5

        # Verify result is returned
        assert result["content"] == "Hello!"

    await client.stop()


@pytest.mark.asyncio
async def test_setup_observability():
    """Test setup_observability creates global client."""
    # Setup observability
    setup_observability(
        service_name="test-service",
        observability_url="http://localhost:8000"
    )

    # Get client
    client = get_client()

    # Verify client is created
    assert isinstance(client, ObservabilityClient)
    assert client.service_name == "test-service"
    assert client.observability_url == "http://localhost:8000"

    await client.stop()


def test_get_client_before_setup_raises():
    """Test get_client before setup raises RuntimeError."""
    # Reset global client
    import sdk.ai_sre_observability as obs_module
    obs_module._global_client = None

    # Verify get_client raises RuntimeError
    with pytest.raises(RuntimeError, match="Observability not initialized"):
        get_client()
