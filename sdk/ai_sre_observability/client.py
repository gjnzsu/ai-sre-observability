"""ObservabilityClient for tracking LLM calls and metrics with batching."""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional

from .models import MetricPayload
from .transport import AsyncTransport

logger = logging.getLogger(__name__)


class LLMCallTracker:
    """Context manager for tracking LLM call metrics."""

    def __init__(self, provider: str, model: str):
        """Initialize LLM call tracker.

        Args:
            provider: LLM provider (e.g., 'openai', 'anthropic')
            model: Model name (e.g., 'gpt-4', 'claude-3')
        """
        self.provider = provider
        self.model = model
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.status = "success"
        self.error_type: Optional[str] = None
        self._start_time = time.time()

    def get_duration(self) -> float:
        """Get duration of the LLM call in seconds.

        Returns:
            Duration in seconds
        """
        return time.time() - self._start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert tracker to dictionary for metric payload.

        Returns:
            Dictionary with LLM call data
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "duration_seconds": self.get_duration(),
            "status": self.status,
            "error_type": self.error_type,
        }


class ObservabilityClient:
    """Client for tracking LLM calls and metrics with batching."""

    def __init__(
        self,
        service_name: str,
        observability_url: str,
        batch_interval: float = 5.0,
        timeout: float = 5.0,
    ):
        """Initialize observability client.

        Args:
            service_name: Name of the service
            observability_url: URL of the observability platform
            batch_interval: Interval for batch sending in seconds (default: 5.0)
            timeout: Request timeout in seconds (default: 5.0)
        """
        self.service_name = service_name
        self.observability_url = observability_url
        self.batch_interval = batch_interval
        self._transport = AsyncTransport(observability_url, timeout)
        self._batch: List[MetricPayload] = []
        self._lock = Lock()
        self._batch_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the batch sender background task."""
        if not self._running:
            self._running = True
            self._batch_task = asyncio.create_task(self._batch_sender())
            logger.info("ObservabilityClient started")

    async def stop(self):
        """Stop the batch sender and flush remaining metrics."""
        if self._running:
            self._running = False
            if self._batch_task:
                self._batch_task.cancel()
                try:
                    await self._batch_task
                except asyncio.CancelledError:
                    pass
            await self._flush_batch()
            await self._transport.close()
            logger.info("ObservabilityClient stopped")

    @asynccontextmanager
    async def track_llm_call(self, provider: str, model: str):
        """Context manager for tracking LLM calls.

        Args:
            provider: LLM provider (e.g., 'openai', 'anthropic')
            model: Model name (e.g., 'gpt-4', 'claude-3')

        Yields:
            LLMCallTracker instance
        """
        tracker = LLMCallTracker(provider, model)
        try:
            yield tracker
        except Exception as e:
            tracker.status = "error"
            tracker.error_type = type(e).__name__
            raise
        finally:
            # Create metric payload
            metric = MetricPayload(
                service_name=self.service_name,
                metric_type="llm_call",
                trace_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                data=tracker.to_dict(),
            )
            self._add_to_batch(metric)

    def increment(
        self, metric_name: str, value: int = 1, labels: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric.

        Args:
            metric_name: Name of the metric
            value: Value to increment by (default: 1)
            labels: Optional labels for the metric
        """
        metric = MetricPayload(
            service_name=self.service_name,
            metric_type="counter",
            trace_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            data={
                "metric_name": metric_name,
                "value": value,
                "labels": labels or {},
            },
        )
        self._add_to_batch(metric)

    def histogram(
        self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Record a histogram metric.

        Args:
            metric_name: Name of the metric
            value: Value to record
            labels: Optional labels for the metric
        """
        metric = MetricPayload(
            service_name=self.service_name,
            metric_type="histogram",
            trace_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            data={
                "metric_name": metric_name,
                "value": value,
                "labels": labels or {},
            },
        )
        self._add_to_batch(metric)

    def _add_to_batch(self, metric: MetricPayload):
        """Add metric to batch.

        Args:
            metric: MetricPayload to add
        """
        with self._lock:
            self._batch.append(metric)
            logger.debug(f"Added metric to batch: {metric.trace_id}")

    async def _batch_sender(self):
        """Background task that sends batches at regular intervals."""
        while self._running:
            try:
                await asyncio.sleep(self.batch_interval)
                await self._flush_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch sender: {e}")

    async def _flush_batch(self):
        """Flush the current batch to the transport."""
        with self._lock:
            if not self._batch:
                return
            batch_to_send = self._batch.copy()
            self._batch.clear()

        logger.info(f"Flushing batch of {len(batch_to_send)} metrics")
        results = await self._transport.send_batch(batch_to_send)
        success_count = sum(1 for r in results if r)
        logger.info(f"Batch sent: {success_count}/{len(results)} successful")
