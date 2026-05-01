"""Unit tests for SDK pricing helpers."""

import pytest

from sdk.ai_sre_observability.pricing import calculate_cost


def test_calculate_gpt54_cost():
    """Test GPT-5.4 cost calculation uses current OpenAI pricing."""
    cost = calculate_cost("gpt-5.4", input_tokens=1_000_000, output_tokens=1_000_000)

    assert cost == pytest.approx(17.50)
