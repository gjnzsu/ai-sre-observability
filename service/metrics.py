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
            ['service', 'provider', 'model', 'status'],
            registry=self.registry
        )

        self.llm_tokens_total = Counter(
            'llm_tokens_total',
            'Total number of tokens processed',
            ['service', 'provider', 'model', 'token_type'],
            registry=self.registry
        )

        self.llm_cost_usd_total = Counter(
            'llm_cost_usd_total',
            'Total cost in USD for LLM requests',
            ['service', 'provider', 'model'],
            registry=self.registry
        )

        self.llm_request_duration_seconds = Histogram(
            'llm_request_duration_seconds',
            'Duration of LLM requests in seconds',
            ['service', 'provider', 'model'],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )

        self.llm_errors_total = Counter(
            'llm_errors_total',
            'Total number of LLM errors',
            ['service', 'provider', 'model', 'error_type'],
            registry=self.registry
        )

        # HTTP Metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total number of HTTP requests',
            ['service', 'endpoint', 'method', 'status_code'],
            registry=self.registry
        )

        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'Duration of HTTP requests in seconds',
            ['service', 'endpoint', 'method'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self.registry
        )

        self.http_requests_in_flight = Gauge(
            'http_requests_in_flight',
            'Number of HTTP requests currently being processed',
            ['service'],
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
    def track_llm_request(self, service: str, provider: str, model: str, status: str) -> None:
        """Track an LLM request.

        Args:
            service: Service name (e.g., 'chat-api', 'embedding-service')
            provider: LLM provider (e.g., 'openai', 'anthropic')
            model: Model name (e.g., 'gpt-4', 'claude-3')
            status: Request status (e.g., 'success', 'error')
        """
        self.llm_requests_total.labels(
            service=service,
            provider=provider,
            model=model,
            status=status
        ).inc()

    def track_llm_tokens(self, service: str, provider: str, model: str, token_type: str, count: int) -> None:
        """Track LLM token usage.

        Args:
            service: Service name
            provider: LLM provider
            model: Model name
            token_type: Type of tokens ('prompt', 'completion', 'total')
            count: Number of tokens
        """
        self.llm_tokens_total.labels(
            service=service,
            provider=provider,
            model=model,
            token_type=token_type
        ).inc(count)

    def track_llm_cost(self, service: str, provider: str, model: str, cost_usd: float) -> None:
        """Track LLM cost.

        Args:
            service: Service name
            provider: LLM provider
            model: Model name
            cost_usd: Cost in USD
        """
        self.llm_cost_usd_total.labels(
            service=service,
            provider=provider,
            model=model
        ).inc(cost_usd)

    def track_llm_duration(self, service: str, provider: str, model: str, duration: float) -> None:
        """Track LLM request duration.

        Args:
            service: Service name
            provider: LLM provider
            model: Model name
            duration: Duration in seconds
        """
        self.llm_request_duration_seconds.labels(
            service=service,
            provider=provider,
            model=model
        ).observe(duration)

    def track_llm_error(self, service: str, provider: str, model: str, error_type: str) -> None:
        """Track LLM error.

        Args:
            service: Service name
            provider: LLM provider
            model: Model name
            error_type: Type of error (e.g., 'rate_limit', 'timeout', 'invalid_request')
        """
        self.llm_errors_total.labels(
            service=service,
            provider=provider,
            model=model,
            error_type=error_type
        ).inc()

    # HTTP Tracking Methods
    def track_http_request(self, service: str, endpoint: str, method: str, status_code: int) -> None:
        """Track an HTTP request.

        Args:
            service: Service name
            endpoint: API endpoint
            method: HTTP method (e.g., 'GET', 'POST')
            status_code: HTTP status code
        """
        self.http_requests_total.labels(
            service=service,
            endpoint=endpoint,
            method=method,
            status_code=str(status_code)
        ).inc()

    def track_http_duration(self, service: str, endpoint: str, method: str, duration: float) -> None:
        """Track HTTP request duration.

        Args:
            service: Service name
            endpoint: API endpoint
            method: HTTP method
            duration: Duration in seconds
        """
        self.http_request_duration_seconds.labels(
            service=service,
            endpoint=endpoint,
            method=method
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
