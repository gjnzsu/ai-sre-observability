"""Cost calculator for LLM API usage."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calculate costs for LLM API usage based on token counts."""

    def __init__(self, pricing: Dict[str, Dict[str, Dict[str, float]]]):
        """Initialize cost calculator with pricing data.

        Args:
            pricing: Nested dictionary with structure:
                {
                    "provider": {
                        "model": {
                            "prompt": float,
                            "completion": float
                        }
                    }
                }
        """
        self.pricing = pricing

    def calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for LLM API usage.

        Args:
            provider: LLM provider name (e.g., "openai", "deepseek")
            model: Model name (e.g., "gpt-4o", "deepseek-chat")
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Total cost in USD, or 0.0 if provider/model not found
        """
        if provider not in self.pricing:
            logger.warning(f"Unknown provider: {provider}")
            return 0.0

        if model not in self.pricing[provider]:
            logger.warning(f"Unknown model: {model} for provider: {provider}")
            return 0.0

        model_pricing = self.pricing[provider][model]
        prompt_cost = (prompt_tokens / 1_000_000) * model_pricing["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * model_pricing["completion"]

        return prompt_cost + completion_cost
