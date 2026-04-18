"""Decorators for tracking LLM calls."""

import functools
from typing import Any, Callable, Dict


def track_llm_call(provider: str, model: str):
    """Decorator for tracking LLM calls.

    Args:
        provider: LLM provider (e.g., 'openai', 'anthropic')
        model: Model name (e.g., 'gpt-4', 'claude-3')

    Returns:
        Decorated async function that tracks LLM calls

    Example:
        @track_llm_call(provider="openai", model="gpt-4")
        async def call_openai(prompt: str):
            response = await openai.chat.completions.create(...)
            return response
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Import here to avoid circular dependency
            from . import get_client

            client = get_client()

            async with client.track_llm_call(provider, model) as tracker:
                # Call the wrapped function
                result = await func(*args, **kwargs)

                # Extract token counts from result if available
                if isinstance(result, dict) and "usage" in result:
                    usage = result["usage"]
                    if "prompt_tokens" in usage:
                        tracker.prompt_tokens = usage["prompt_tokens"]
                    if "completion_tokens" in usage:
                        tracker.completion_tokens = usage["completion_tokens"]

                return result

        return wrapper
    return decorator
