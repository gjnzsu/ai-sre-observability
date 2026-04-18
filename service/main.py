"""FastAPI application for AI SRE Observability Platform."""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import generate_latest

from service.config import load_pricing_config
from service.cost_calculator import CostCalculator
from service.metrics import MetricsRegistry
from service.models import (
    MetricIngestRequest,
    MetricIngestResponse,
    HealthResponse,
    ServicesResponse,
    ServiceInfo,
    LLMCallData,
    HTTPRequestData,
    BusinessMetricData
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI SRE Observability Platform",
    description="Centralized observability platform for AI services",
    version="0.1.0"
)

# Global state
metrics_registry: MetricsRegistry = None
cost_calculator: CostCalculator = None
metrics_received_count: int = 0
last_reset_time: datetime = datetime.utcnow()
service_metrics: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    global metrics_registry, cost_calculator, last_reset_time

    logger.info("Starting AI SRE Observability Platform...")

    # Load pricing configuration
    config_path = os.getenv("PRICING_CONFIG_PATH", "/config/pricing.yaml")
    pricing_config = load_pricing_config(config_path)

    if not pricing_config:
        logger.warning(f"No pricing config loaded from {config_path}, using empty config")
        pricing_config = {}

    # Initialize components
    metrics_registry = MetricsRegistry()
    cost_calculator = CostCalculator(pricing_config)
    last_reset_time = datetime.utcnow()

    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AI SRE Observability Platform...")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint.

    Returns:
        Health status with service tracking information
    """
    global metrics_received_count, last_reset_time

    # Reset counter every minute
    now = datetime.utcnow()
    if (now - last_reset_time) > timedelta(minutes=1):
        metrics_received_count = 0
        last_reset_time = now

    # Get tracked services
    tracked_services = list(metrics_registry.get_tracked_services().keys())

    return HealthResponse(
        status="ok",
        services_tracked=tracked_services,
        metrics_received_last_minute=metrics_received_count
    )


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint.

    Returns:
        Prometheus-formatted metrics
    """
    metrics_data = generate_latest(metrics_registry.registry)
    return Response(content=metrics_data, media_type="text/plain; charset=utf-8")


@app.post("/ingest", response_model=MetricIngestResponse)
async def ingest_metrics(request: MetricIngestRequest):
    """Ingest metrics from SDK clients.

    Args:
        request: Metric ingestion request

    Returns:
        Ingestion response with status
    """
    global metrics_received_count, service_metrics

    try:
        service_name = request.service_name
        metric_type = request.metric_type
        data = request.data

        # Update metrics received counter
        metrics_received_count += 1

        # Track service
        if service_name not in service_metrics:
            service_metrics[service_name] = {
                "name": service_name,
                "last_seen": request.timestamp,
                "metrics_count": 0
            }
            metrics_registry.register_service(service_name, service_metrics[service_name])

        # Update service info
        service_metrics[service_name]["last_seen"] = request.timestamp
        service_metrics[service_name]["metrics_count"] += 1

        # Process based on metric type
        if metric_type == "llm_call" and isinstance(data, LLMCallData):
            # Track LLM request
            metrics_registry.track_llm_request(
                service=service_name,
                provider=data.provider,
                model=data.model,
                status=data.status
            )

            # Track tokens
            metrics_registry.track_llm_tokens(
                service=service_name,
                provider=data.provider,
                model=data.model,
                token_type="prompt",
                count=data.prompt_tokens
            )
            metrics_registry.track_llm_tokens(
                service=service_name,
                provider=data.provider,
                model=data.model,
                token_type="completion",
                count=data.completion_tokens
            )
            metrics_registry.track_llm_tokens(
                service=service_name,
                provider=data.provider,
                model=data.model,
                token_type="total",
                count=data.prompt_tokens + data.completion_tokens
            )

            # Track duration
            metrics_registry.track_llm_duration(
                service=service_name,
                provider=data.provider,
                model=data.model,
                duration=data.duration_seconds
            )

            # Calculate and track cost
            cost = cost_calculator.calculate_cost(
                provider=data.provider,
                model=data.model,
                prompt_tokens=data.prompt_tokens,
                completion_tokens=data.completion_tokens
            )
            metrics_registry.track_llm_cost(
                service=service_name,
                provider=data.provider,
                model=data.model,
                cost_usd=cost
            )

            # Track errors if present
            if data.status == "error" and data.error_type:
                metrics_registry.track_llm_error(
                    service=service_name,
                    provider=data.provider,
                    model=data.model,
                    error_type=data.error_type
                )

        elif metric_type == "http_request" and isinstance(data, HTTPRequestData):
            # Track HTTP request
            metrics_registry.track_http_request(
                service=service_name,
                endpoint=data.endpoint,
                method=data.method,
                status_code=data.status_code
            )

            # Track duration
            metrics_registry.track_http_duration(
                service=service_name,
                endpoint=data.endpoint,
                method=data.method,
                duration=data.duration_seconds
            )

        elif metric_type == "business_metric" and isinstance(data, BusinessMetricData):
            # Business metrics are custom - log for now
            logger.info(f"Received business metric: {data.metric_name} = {data.value}")

        else:
            logger.warning(f"Unknown metric type: {metric_type}")

        return MetricIngestResponse(
            status="success",
            trace_id=request.trace_id
        )

    except Exception as e:
        logger.error(f"Error ingesting metric: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error ingesting metric: {str(e)}")


@app.get("/services", response_model=ServicesResponse)
async def list_services():
    """List all tracked services.

    Returns:
        List of tracked services with their information
    """
    services = []
    for service_name, service_info in service_metrics.items():
        services.append(ServiceInfo(
            name=service_info["name"],
            last_seen=service_info["last_seen"],
            metrics_count=service_info["metrics_count"]
        ))

    return ServicesResponse(services=services)
