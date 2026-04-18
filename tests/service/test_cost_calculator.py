"""Unit tests for cost calculator service."""

import pytest
from service.cost_calculator import CostCalculator


@pytest.fixture
def cost_calculator():
    """Create a cost calculator with test pricing data."""
    pricing = {
        "openai": {
            "gpt-4o": {
                "prompt": 0.000005,
                "completion": 0.000015
            }
        },
        "deepseek": {
            "deepseek-chat": {
                "prompt": 0.00000014,
                "completion": 0.00000028
            }
        }
    }
    return CostCalculator(pricing)


def test_calculate_openai_gpt4o_cost(cost_calculator):
    """Test OpenAI GPT-4o cost calculation."""
    cost = cost_calculator.calculate_cost(
        provider="openai",
        model="gpt-4o",
        prompt_tokens=150,
        completion_tokens=80
    )
    expected = 0.00000195
    assert cost == pytest.approx(expected)


def test_calculate_deepseek_cost(cost_calculator):
    """Test DeepSeek cost calculation."""
    cost = cost_calculator.calculate_cost(
        provider="deepseek",
        model="deepseek-chat",
        prompt_tokens=1000,
        completion_tokens=500
    )
    expected = 0.00000028
    assert cost == pytest.approx(expected)


def test_unknown_provider_returns_zero(cost_calculator):
    """Test unknown provider returns 0.0."""
    cost = cost_calculator.calculate_cost(
        provider="unknown_provider",
        model="gpt-4o",
        prompt_tokens=100,
        completion_tokens=50
    )
    assert cost == 0.0


def test_unknown_model_returns_zero(cost_calculator):
    """Test unknown model returns 0.0."""
    cost = cost_calculator.calculate_cost(
        provider="openai",
        model="unknown_model",
        prompt_tokens=100,
        completion_tokens=50
    )
    assert cost == 0.0
