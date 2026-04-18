"""Prometheus metrics registry for AI SRE Observability Platform."""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Dict, Any


class MetricsRegistry:
    """Central registry for all Prometheus metrics."""

    def __init__(self):
        """Initialize all Prometheus metrics."""
        # Create a custom registry for this instance
        self.registry = CollectorRegistry()

        # LLM Metrics
        self.llm_requests_total = Counter(
            'llm_requests_total',
            'Total number of LLM API requests',
            ['service', 'model', 'operation'],
            registry=self.registry
        )

        self.llm_tokens_total = Counter(
            'llm_tokens_total',
            'Total number of tokens processed',
            ['service', 'model', 'token_type'],
            registry=self.registry
        )

        self.llm_cost_usd_total = Counter(
            'llm_cost_usd_total',
            'Total cost in USD for LLM requests',
            ['service', 'model'],
            registry=self.registry
        )

        self.llm_request_duration_seconds = Histogram(
            'llm_request_duration_seconds',
            'Duration of LLM requests in seconds',
            ['service', 'model', 'operation'],
            registry=self.registry
        )

        self.llm_errors_total = Counter(
            'llm_errors_total',
            'Total number of LLM errors',
            ['service', 'model', 'error_type'],
            registry=self.registry
        )

        # HTTP Metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'Duration of HTTP requests in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )

        self.http_requests_in_flight = Gauge(
            'http_requests_in_flight',
            'Number of HTTP requests currently being processed',
            ['method', 'endpoint'],
            registry=self.registry
        )

        # System Health Metrics
        self.service_up = Gauge(
            'service_up',
            'Service health status (1 = up, 0 = down)',
            ['service'],
            registry=self.registry
        )

        # Internal tracking
        self._services: Dict[str, Dict[str, Any]] = {}

    # LLM Tracking Methods
    def track_llm_request(self, service: str, model: str, operation: str) -> None:
        """Track an LLM request.

        Args:
            service: LLM service name (e.g., 'openai', 'anthropic')
            model: Model name (e.g., 'gpt-4', 'claude-3')
            operation: Operation type (e.g., 'chat_completion', 'embedding')
        """
        self.llm_requests_total.labels(
            service=service,
            model=model,
            operation=operation
        ).inc()

    def track_llm_tokens(self, service: str, model: str, token_type: str, count: int) -> None:
        """Track LLM token usage.

        Args:
            service: LLM service name
            model: Model name
            token_type: Type of tokens ('prompt', 'completion', 'total')
            count: Number of tokens
        """
        self.llm_tokens_total.labels(
            service=service,
            model=model,
            token_type=token_type
        ).inc(count)

    def track_llm_cost(self, service: str, model: str, cost_usd: float) -> None:
        """Track LLM cost.

        Args:
            service: LLM service name
            model: Model name
            cost_usd: Cost in USD
        """
        self.llm_cost_usd_total.labels(
            service=service,
            model=model
        ).inc(cost_usd)

    def track_llm_duration(self, service: str, model: str, operation: str, duration: float) -> None:
        """Track LLM request duration.

        Args:
            service: LLM service name
            model: Model name
            operation: Operation type
            duration: Duration in seconds
        """
        self.llm_request_duration_seconds.labels(
            service=service,
            model=model,
            operation=operation
        ).observe(duration)

    def track_llm_error(self, service: str, model: str, error_type: str) -> None:
        """Track LLM error.

        Args:
            service: LLM service name
            model: Model name
            error_type: Type of error (e.g., 'rate_limit', 'timeout', 'invalid_request')
        """
        self.llm_errors_total.labels(
            service=service,
            model=model,
            error_type=error_type
        ).inc()

    # HTTP Tracking Methods
    def track_http_request(self, method: str, endpoint: str, status: int) -> None:
        """Track an HTTP request.

        Args:
            method: HTTP method (e.g., 'GET', 'POST')
            endpoint: API endpoint
            status: HTTP status code
        """
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()

    def track_http_duration(self, method: str, endpoint: str, duration: float) -> None:
        """Track HTTP request duration.

        Args:
            method: HTTP method
            endpoint: API endpoint
            duration: Duration in seconds
        """
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    # System Health Methods
    def set_service_health(self, service: str, is_up: bool) -> None:
        """Set service health status.

        Args:
            service: Service name
            is_up: True if service is up, False otherwise
        """
        self.service_up.labels(service=service).set(1 if is_up else 0)

    # Service Registration Methods
    def register_service(self, service: str, info: Dict[str, Any]) -> None:
        """Register a service for tracking.

        Args:
            service: Service name
            info: Service information dictionary
        """
        self._services[service] = info

    def get_tracked_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all tracked services.

        Returns:
            Dictionary of service names to their info
        """
        return self._services.copy()

    def get_service_info(self, service: str) -> Dict[str, Any]:
        """Get information about a specific service.

        Args:
            service: Service name

        Returns:
            Service information dictionary, or empty dict if not found
        """
        return self._services.get(service, {})
