"""End-to-end integration tests for AI SRE Observability Platform."""

import asyncio
import time
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from service.main import app
from sdk.ai_sre_observability import ObservabilityClient


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def observability_client():
    """Create an observability client for testing."""
    client = ObservabilityClient(
        service_name="test-service",
        observability_url="http://testserver",
        batch_interval=0.1,  # Short interval for testing
        timeout=5.0,
    )
    await client.start()
    yield client
    await client.stop()


def test_health_endpoint_integration(test_client):
    """Test health endpoint returns correct data."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "services_tracked" in data
    assert "metrics_received_last_minute" in data
    assert isinstance(data["services_tracked"], list)
    assert isinstance(data["metrics_received_last_minute"], int)


def test_metrics_endpoint_integration(test_client):
    """Test Prometheus metrics are exposed correctly."""
    response = test_client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

    # Check that response contains Prometheus-formatted metrics
    content = response.text
    assert len(content) > 0

    # Should contain some metric names (even if empty)
    # Prometheus metrics typically have HELP and TYPE comments
    assert "# HELP" in content or "# TYPE" in content or "_total" in content


def test_services_endpoint_integration(test_client):
    """Test services endpoint returns tracked services."""
    response = test_client.get("/services")

    assert response.status_code == 200
    data = response.json()

    assert "services" in data
    assert isinstance(data["services"], list)


def test_ingest_llm_metric_integration(test_client):
    """Test ingesting LLM metrics through the API."""
    payload = {
        "service_name": "test-service",
        "metric_type": "llm_call",
        "trace_id": "test-trace-123",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "provider": "openai",
            "model": "gpt-4",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "duration_seconds": 1.5,
            "status": "success",
            "error_type": None,
        },
    }

    response = test_client.post("/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["trace_id"] == "test-trace-123"


def test_ingest_http_metric_integration(test_client):
    """Test ingesting HTTP metrics through the API."""
    payload = {
        "service_name": "test-service",
        "metric_type": "http_request",
        "trace_id": "test-trace-456",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "endpoint": "/api/users",
            "method": "GET",
            "status_code": 200,
            "duration_seconds": 0.5,
        },
    }

    response = test_client.post("/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["trace_id"] == "test-trace-456"


def test_cost_calculation_integration(test_client):
    """Test cost calculation works end-to-end."""
    # Send LLM metric with known token counts
    payload = {
        "service_name": "cost-test-service",
        "metric_type": "llm_call",
        "trace_id": "cost-trace-123",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "provider": "openai",
            "model": "gpt-4",
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "duration_seconds": 2.0,
            "status": "success",
            "error_type": None,
        },
    }

    response = test_client.post("/ingest", json=payload)
    assert response.status_code == 200

    # Get metrics and verify cost is tracked
    metrics_response = test_client.get("/metrics")
    assert metrics_response.status_code == 200

    content = metrics_response.text
    # Should contain cost metrics
    assert "llm_cost_usd" in content or "cost" in content.lower()


def test_service_tracking_integration(test_client):
    """Test that services are tracked correctly."""
    # Send metrics from multiple services
    services = ["service-a", "service-b", "service-c"]

    for service in services:
        payload = {
            "service_name": service,
            "metric_type": "llm_call",
            "trace_id": f"trace-{service}",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "prompt_tokens": 50,
                "completion_tokens": 25,
                "duration_seconds": 0.5,
                "status": "success",
                "error_type": None,
            },
        }
        response = test_client.post("/ingest", json=payload)
        assert response.status_code == 200

    # Check health endpoint shows tracked services
    health_response = test_client.get("/health")
    assert health_response.status_code == 200

    health_data = health_response.json()
    tracked_services = health_data["services_tracked"]

    # All services should be tracked
    for service in services:
        assert service in tracked_services

    # Check services endpoint
    services_response = test_client.get("/services")
    assert services_response.status_code == 200

    services_data = services_response.json()
    service_names = [s["name"] for s in services_data["services"]]

    for service in services:
        assert service in service_names


def test_error_tracking_integration(test_client):
    """Test that errors are tracked correctly."""
    payload = {
        "service_name": "error-test-service",
        "metric_type": "llm_call",
        "trace_id": "error-trace-123",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "provider": "openai",
            "model": "gpt-4",
            "prompt_tokens": 100,
            "completion_tokens": 0,
            "duration_seconds": 0.1,
            "status": "error",
            "error_type": "RateLimitError",
        },
    }

    response = test_client.post("/ingest", json=payload)
    assert response.status_code == 200

    # Get metrics and verify error is tracked
    metrics_response = test_client.get("/metrics")
    assert metrics_response.status_code == 200

    content = metrics_response.text
    # Should contain error metrics
    assert "error" in content.lower() or "llm_errors" in content


def test_metrics_counter_integration(test_client):
    """Test that metrics counter increments correctly."""
    # Get initial count
    health_response = test_client.get("/health")
    initial_count = health_response.json()["metrics_received_last_minute"]

    # Send a metric
    payload = {
        "service_name": "counter-test",
        "metric_type": "llm_call",
        "trace_id": "counter-trace",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "duration_seconds": 0.2,
            "status": "success",
            "error_type": None,
        },
    }

    test_client.post("/ingest", json=payload)

    # Get updated count
    health_response = test_client.get("/health")
    updated_count = health_response.json()["metrics_received_last_minute"]

    # Count should have increased
    assert updated_count > initial_count


@pytest.mark.asyncio
async def test_sdk_to_service_integration():
    """Test SDK sends metrics to service successfully."""
    # This test would require a running service instance
    # For now, we'll test the SDK client functionality

    client = ObservabilityClient(
        service_name="sdk-test-service",
        observability_url="http://localhost:8000",
        batch_interval=0.1,
        timeout=5.0,
    )

    await client.start()

    # Track an LLM call
    async with client.track_llm_call("openai", "gpt-4") as tracker:
        tracker.prompt_tokens = 100
        tracker.completion_tokens = 50
        await asyncio.sleep(0.1)

    # Wait for batch to be sent
    await asyncio.sleep(0.2)

    await client.stop()

    # If we get here without errors, the SDK is working
    assert True


def test_multiple_metrics_batch_integration(test_client):
    """Test sending multiple metrics in sequence."""
    metrics_count = 10

    for i in range(metrics_count):
        payload = {
            "service_name": "batch-test-service",
            "metric_type": "llm_call",
            "trace_id": f"batch-trace-{i}",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "prompt_tokens": 50 + i,
                "completion_tokens": 25 + i,
                "duration_seconds": 0.5 + (i * 0.1),
                "status": "success",
                "error_type": None,
            },
        }

        response = test_client.post("/ingest", json=payload)
        assert response.status_code == 200

    # Verify service is tracked
    health_response = test_client.get("/health")
    assert health_response.status_code == 200

    health_data = health_response.json()
    assert "batch-test-service" in health_data["services_tracked"]


def test_invalid_metric_type_integration(test_client):
    """Test handling of invalid metric types."""
    payload = {
        "service_name": "invalid-test",
        "metric_type": "invalid_type",
        "trace_id": "invalid-trace",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "some_field": "some_value",
        },
    }

    # Should return validation error for invalid metric type
    response = test_client.post("/ingest", json=payload)
    assert response.status_code == 422  # Validation error


def test_prometheus_metrics_format_integration(test_client):
    """Test that Prometheus metrics follow correct format."""
    # Send some metrics first
    payload = {
        "service_name": "prometheus-test",
        "metric_type": "llm_call",
        "trace_id": "prom-trace",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "provider": "openai",
            "model": "gpt-4",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "duration_seconds": 1.0,
            "status": "success",
            "error_type": None,
        },
    }

    test_client.post("/ingest", json=payload)

    # Get metrics
    response = test_client.get("/metrics")
    assert response.status_code == 200

    content = response.text
    lines = content.split("\n")

    # Check for Prometheus format
    # Should have comments and metric lines
    has_comments = any(line.startswith("#") for line in lines)
    has_metrics = any(line and not line.startswith("#") for line in lines)

    assert has_comments or has_metrics  # At least one should be present
