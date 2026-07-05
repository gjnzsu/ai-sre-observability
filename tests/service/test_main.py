"""Tests for FastAPI main application."""

import os
from datetime import datetime

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_pricing_config():
    """Mock pricing configuration."""
    return {
        "openai": {
            "gpt-4o": {
                "prompt": 2.50,
                "completion": 10.00
            }
        },
        "anthropic": {
            "claude-3-opus": {
                "prompt": 15.00,
                "completion": 75.00
            }
        }
    }


@pytest.fixture
def client(mock_pricing_config, tmp_path):
    """Create test client with mocked config."""
    # Create a temporary config file
    config_file = tmp_path / "pricing.yaml"
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(mock_pricing_config, f)

    # Set environment variable
    os.environ['PRICING_CONFIG_PATH'] = str(config_file)
    os.environ.pop('OBSERVABILITY_API_KEYS', None)

    # Import after setting env var
    from service.main import app

    # Use TestClient with context manager to trigger startup/shutdown events
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_client(mock_pricing_config, tmp_path):
    """Create test client with API key authentication enabled."""
    config_file = tmp_path / "pricing.yaml"
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(mock_pricing_config, f)

    os.environ['PRICING_CONFIG_PATH'] = str(config_file)
    os.environ['OBSERVABILITY_API_KEYS'] = "test-api-key, rotated-key"

    from service.main import app

    with TestClient(app) as test_client:
        yield test_client

    os.environ.pop('OBSERVABILITY_API_KEYS', None)


def test_health_endpoint(client):
    """Test /health endpoint returns correct structure."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "status" in data
    assert "services_tracked" in data
    assert "metrics_received_last_minute" in data

    # Check types
    assert isinstance(data["status"], str)
    assert isinstance(data["services_tracked"], list)
    assert isinstance(data["metrics_received_last_minute"], int)

    # Check values
    assert data["status"] == "ok"
    assert data["metrics_received_last_minute"] >= 0


def test_metrics_endpoint(client):
    """Test /metrics endpoint returns Prometheus format."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

    # Check Prometheus format
    content = response.text
    assert "# HELP" in content or "# TYPE" in content


def test_ingest_llm_call(client):
    """Test /ingest endpoint accepts LLM call metrics."""
    payload = {
        "service_name": "test-service",
        "metric_type": "llm_call",
        "trace_id": "trace-123",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "provider": "openai",
            "model": "gpt-4o",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "duration_seconds": 1.5,
            "status": "success"
        }
    }

    response = client.post("/ingest", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "status" in data
    assert "trace_id" in data
    assert data["status"] == "success"
    assert data["trace_id"] == "trace-123"


def test_ingest_without_configured_api_key_keeps_legacy_clients_working(client):
    """Test /ingest remains open when no API keys are configured."""
    payload = {
        "service_name": "ai-market-studio",
        "metric_type": "llm_call",
        "trace_id": "legacy-trace-123",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "provider": "openai",
            "model": "gpt-4o",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "duration_seconds": 1.5,
            "status": "success"
        }
    }

    response = client.post("/ingest", json=payload)

    assert response.status_code == 200
    assert response.json()["trace_id"] == "legacy-trace-123"


def test_ingest_requires_api_key_when_configured(auth_client):
    """Test /ingest rejects missing or invalid API keys when configured."""
    payload = {
        "service_name": "ai-market-studio",
        "metric_type": "llm_call",
        "trace_id": "auth-trace-123",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "provider": "openai",
            "model": "gpt-4o",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "duration_seconds": 1.5,
            "status": "success"
        }
    }

    missing_key_response = auth_client.post("/ingest", json=payload)
    invalid_key_response = auth_client.post(
        "/ingest",
        json=payload,
        headers={"X-API-Key": "wrong-key"}
    )
    valid_key_response = auth_client.post(
        "/ingest",
        json=payload,
        headers={"X-API-Key": "test-api-key"}
    )

    assert missing_key_response.status_code == 401
    assert invalid_key_response.status_code == 401
    assert valid_key_response.status_code == 200
    assert valid_key_response.json()["trace_id"] == "auth-trace-123"


def test_services_endpoint(client):
    """Test /services endpoint returns tracked services list."""
    # First ingest a metric to register a service
    payload = {
        "service_name": "test-service",
        "metric_type": "llm_call",
        "trace_id": "trace-456",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "provider": "openai",
            "model": "gpt-4o",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "duration_seconds": 1.5,
            "status": "success"
        }
    }
    client.post("/ingest", json=payload)

    # Now check services endpoint
    response = client.get("/services")

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "services" in data
    assert isinstance(data["services"], list)

    # Check if our service is tracked
    if len(data["services"]) > 0:
        service = data["services"][0]
        assert "name" in service
        assert "last_seen" in service
        assert "metrics_count" in service
