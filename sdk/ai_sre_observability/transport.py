"""Async HTTP transport for sending metrics to the observability platform."""

import logging
from typing import List, Optional

import httpx

from .models import MetricPayload

logger = logging.getLogger(__name__)


class AsyncTransport:
    """Async HTTP transport for sending metrics."""

    def __init__(self, observability_url: str, timeout: float = 5.0):
        """Initialize async transport.

        Args:
            observability_url: Base URL of the observability platform
            timeout: Request timeout in seconds (default: 5.0)
        """
        self.observability_url = observability_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx.AsyncClient.

        Returns:
            httpx.AsyncClient instance
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def send_metric(self, metric: MetricPayload) -> bool:
        """Send single metric to the observability platform.

        Args:
            metric: MetricPayload to send

        Returns:
            True if successful, False otherwise (graceful degradation)
        """
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.observability_url}/api/v1/metrics",
                json=metric.model_dump(mode="json"),
            )
            response.raise_for_status()
            logger.debug(f"Metric sent successfully: {metric.trace_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send metric {metric.trace_id}: {e}")
            return False

    async def send_batch(self, metrics: List[MetricPayload]) -> List[bool]:
        """Send batch of metrics to the observability platform.

        Args:
            metrics: List of MetricPayload to send

        Returns:
            List of boolean results for each metric
        """
        results = []
        for metric in metrics:
            result = await self.send_metric(metric)
            results.append(result)
        return results

    async def close(self):
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
