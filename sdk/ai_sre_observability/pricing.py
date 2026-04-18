"""
LLM Pricing Constants

Pricing per 1M tokens (input/output) in USD
"""

PRICING = {
    "gpt-4o": {
        "input": 2.50,  # $2.50 per 1M input tokens
        "output": 10.00,  # $10.00 per 1M output tokens
    },
    "gpt-4o-mini": {
        "input": 0.15,  # $0.15 per 1M input tokens
        "output": 0.60,  # $0.60 per 1M output tokens
    },
    "deepseek-chat": {
        "input": 0.14,  # $0.14 per 1M input tokens
        "output": 0.28,  # $0.28 per 1M output tokens
    },
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate the cost of an LLM call.

    Args:
        model: Model name (e.g., "gpt-4o")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Total cost in USD
    """
    if model not in PRICING:
        return 0.0

    pricing = PRICING[model]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]

    return input_cost + output_cost
