"""AI SRE Observability SDK - Public API."""

from typing import Optional

from .client import ObservabilityClient
from .decorators import track_llm_call

__version__ = "0.1.0"

# Global client instance
_global_client: Optional[ObservabilityClient] = None


def setup_observability(
    service_name: str,
    observability_url: str,
    batch_interval: float = 5.0,
    timeout: float = 5.0,
) -> ObservabilityClient:
    """Initialize the global observability client.

    Args:
        service_name: Name of the service
        observability_url: URL of the observability platform
        batch_interval: Interval for batch sending in seconds (default: 5.0)
        timeout: Request timeout in seconds (default: 5.0)

    Returns:
        The initialized ObservabilityClient

    Example:
        setup_observability(
            service_name="my-service",
            observability_url="http://localhost:8000"
        )
    """
    global _global_client

    _global_client = ObservabilityClient(
        service_name=service_name,
        observability_url=observability_url,
        batch_interval=batch_interval,
        timeout=timeout,
    )

    # Start the client in the background
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_global_client.start())
    except RuntimeError:
        # No event loop running, client will be started when first used
        pass

    return _global_client


def get_client() -> ObservabilityClient:
    """Get the global observability client.

    Returns:
        The global ObservabilityClient instance

    Raises:
        RuntimeError: If observability has not been initialized

    Example:
        client = get_client()
        async with client.track_llm_call("openai", "gpt-4") as tracker:
            # Make LLM call
            pass
    """
    if _global_client is None:
        raise RuntimeError(
            "Observability not initialized. Call setup_observability() first."
        )
    return _global_client


__all__ = [
    "setup_observability",
    "get_client",
    "track_llm_call",
    "ObservabilityClient",
]
