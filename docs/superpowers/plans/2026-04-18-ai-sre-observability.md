# AI SRE Observability Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a centralized observability platform with lightweight SDK and FastAPI service for unified visibility, LLM cost tracking, and request correlation across AI services.

**Architecture:** Hybrid approach with Python SDK (async fire-and-forget) sending metrics to centralized FastAPI service that exposes Prometheus metrics. Trace IDs for request correlation. Grafana dashboards for visualization.

**Tech Stack:** FastAPI, prometheus_client, pydantic, httpx, pytest, Docker, Kubernetes

---

## File Structure

This plan creates the following structure:

```
ai-sre-observability/
├── service/                           # Observability Service (FastAPI)
│   ├── main.py                        # FastAPI app with endpoints
│   ├── models.py                      # Pydantic request/response models
│   ├── metrics.py                     # Prometheus metrics registry
│   ├── cost_calculator.py             # LLM cost calculation
│   ├── config.py                      # Configuration loading
│   ├── requirements.txt               # Service dependencies
│   └── Dockerfile                     # Multi-stage Docker build
├── sdk/                               # SDK Library
│   ├── ai_sre_observability/
│   │   ├── __init__.py                # Public API exports
│   │   ├── client.py                  # ObservabilityClient
│   │   ├── decorators.py              # @track_llm_call decorator
│   │   ├── models.py                  # SDK data models
│   │   ├── transport.py               # Async HTTP transport
│   │   └── pricing.py                 # LLM pricing constants
│   ├── setup.py                       # Package setup
│   ├── requirements.txt               # SDK dependencies
│   └── README.md                      # SDK usage guide
├── k8s/                               # Kubernetes manifests
│   ├── configmap.yaml                 # LLM pricing config
│   ├── deployment.yaml                # Service deployment
│   └── service.yaml                   # ClusterIP service
├── tests/                             # Tests
│   ├── service/
│   │   ├── test_main.py               # Service endpoint tests
│   │   ├── test_metrics.py            # Metrics tests
│   │   └── test_cost_calculator.py    # Cost calculation tests
│   └── sdk/
│       ├── test_client.py             # Client tests
│       ├── test_decorators.py         # Decorator tests
│       └── test_transport.py          # Transport tests
├── grafana/                           # Grafana dashboards
│   └── dashboards/
│       ├── service-overview.json      # Service health dashboard
│       ├── llm-cost.json              # LLM cost tracking
│       └── request-tracing.json       # Request debugging
└── README.md                          # Project documentation
```

---

## Task 1: Project Setup

**Files:**
- Create: `service/requirements.txt`
- Create: `sdk/requirements.txt`
- Create: `tests/service/__init__.py`
- Create: `tests/sdk/__init__.py`
- Create: `README.md`

- [ ] **Step 1: Create service requirements file**

```bash
cat > service/requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
prometheus-client==0.19.0
pydantic==2.5.3
pydantic-settings==2.1.0
pyyaml==6.0.1
httpx==0.26.0
EOF
```

- [ ] **Step 2: Create SDK requirements file**

```bash
cat > sdk/requirements.txt << 'EOF'
httpx==0.26.0
pydantic==2.5.3
EOF
```

- [ ] **Step 3: Create test directory structure**

```bash
mkdir -p tests/service tests/sdk
touch tests/service/__init__.py tests/sdk/__init__.py
```

- [ ] **Step 4: Create project README**

```bash
cat > README.md << 'EOF'
# AI SRE Observability Platform

Centralized observability for AI services with unified visibility, LLM cost tracking, and request correlation.

## Components

- **Observability Service** - FastAPI service that aggregates metrics and exposes Prometheus endpoint
- **SDK Library** - Lightweight Python SDK for instrumenting services
- **Grafana Dashboards** - Pre-built dashboards for visualization

## Quick Start

See [docs/superpowers/specs/2026-04-18-ai-sre-observability-design.md](docs/superpowers/specs/2026-04-18-ai-sre-observability-design.md) for full design.

## Development

```bash
# Install service dependencies
cd service && pip install -r requirements.txt

# Install SDK dependencies
cd sdk && pip install -r requirements.txt

# Run tests
pytest tests/
```
EOF
```

- [ ] **Step 5: Commit project setup**

```bash
git add service/requirements.txt sdk/requirements.txt tests/ README.md
git commit -m "chore: initialize project structure with dependencies"
```

## Task 2: Observability Service - Data Models

**Files:**
- Create: `service/models.py`
- Create: `tests/service/test_models.py`

- [ ] **Step 1: Write test for MetricIngestRequest model**

```python
# tests/service/test_models.py
import pytest
from datetime import datetime
from service.models import MetricIngestRequest, LLMCallData

def test_metric_ingest_request_valid():
    """Test valid metric ingest request"""
    data = {
        "service_name": "ai-market-studio",
        "metric_type": "llm_call",
        "trace_id": "abc-123",
        "timestamp": "2026-04-18T10:30:00Z",
        "data": {
            "provider": "openai",
            "model": "gpt-4o",
            "prompt_tokens": 150,
            "completion_tokens": 80,
            "duration_seconds": 1.2,
            "status": "success"
        }
    }
    request = MetricIngestRequest(**data)
    assert request.service_name == "ai-market-studio"
    assert request.metric_type == "llm_call"
    assert request.trace_id == "abc-123"
    assert request.data.provider == "openai"
    assert request.data.model == "gpt-4o"
    assert request.data.prompt_tokens == 150
    assert request.data.completion_tokens == 80
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd tests/service
pytest test_models.py::test_metric_ingest_request_valid -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'service.models'"

- [ ] **Step 3: Implement data models**

```python
# service/models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class LLMCallData(BaseModel):
    """Data for LLM call metrics"""
    provider: str = Field(..., description="LLM provider (openai, deepseek)")
    model: str = Field(..., description="Model name (gpt-4o, deepseek-chat)")
    prompt_tokens: int = Field(..., ge=0, description="Number of prompt tokens")
    completion_tokens: int = Field(..., ge=0, description="Number of completion tokens")
    duration_seconds: float = Field(..., ge=0, description="Call duration in seconds")
    status: str = Field(..., description="Call status (success, error)")
    error_type: Optional[str] = Field(None, description="Error type if status=error")

class HTTPRequestData(BaseModel):
    """Data for HTTP request metrics"""
    endpoint: str = Field(..., description="API endpoint")
    method: str = Field(..., description="HTTP method")
    status_code: int = Field(..., ge=100, le=599, description="HTTP status code")
    duration_seconds: float = Field(..., ge=0, description="Request duration")

class BusinessMetricData(BaseModel):
    """Data for business metrics"""
    metric_name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")

class MetricIngestRequest(BaseModel):
    """Request model for /ingest endpoint"""
    service_name: str = Field(..., description="Name of the service sending metrics")
    metric_type: str = Field(..., description="Type of metric (llm_call, http_request, business)")
    trace_id: str = Field(..., description="Trace ID for correlation")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    data: LLMCallData | HTTPRequestData | BusinessMetricData = Field(..., description="Metric data")

class MetricIngestResponse(BaseModel):
    """Response model for /ingest endpoint"""
    status: str = Field(..., description="Response status")
    trace_id: str = Field(..., description="Trace ID from request")

class HealthResponse(BaseModel):
    """Response model for /health endpoint"""
    status: str = Field(..., description="Health status")
    services_tracked: list[str] = Field(default_factory=list, description="List of tracked services")
    metrics_received_last_minute: int = Field(..., description="Metrics received in last minute")

class ServiceInfo(BaseModel):
    """Service information"""
    name: str
    last_seen: str
    metrics_count: int

class ServicesResponse(BaseModel):
    """Response model for /services endpoint"""
    services: list[ServiceInfo]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/service/test_models.py::test_metric_ingest_request_valid -v
```

Expected: PASS

- [ ] **Step 5: Commit data models**

```bash
git add service/models.py tests/service/test_models.py
git commit -m "feat(service): add pydantic data models for API"
```

## Task 3: Cost Calculator

**Files:**
- Create: `service/cost_calculator.py`
- Create: `tests/service/test_cost_calculator.py`

- [ ] **Step 1: Write test for cost calculation**

```python
# tests/service/test_cost_calculator.py
import pytest
from service.cost_calculator import CostCalculator

def test_calculate_openai_gpt4o_cost():
    """Test cost calculation for OpenAI GPT-4o"""
    pricing = {
        "openai": {
            "gpt-4o": {
                "prompt": 0.000005,
                "completion": 0.000015
            }
        }
    }
    calculator = CostCalculator(pricing)
    
    cost = calculator.calculate_cost(
        provider="openai",
        model="gpt-4o",
        prompt_tokens=150,
        completion_tokens=80
    )
    
    # (150 / 1_000_000) * 0.000005 + (80 / 1_000_000) * 0.000015
    # = 0.00000075 + 0.0000012 = 0.00000195
    assert cost == pytest.approx(0.00000195, rel=1e-9)

def test_calculate_deepseek_cost():
    """Test cost calculation for DeepSeek"""
    pricing = {
        "deepseek": {
            "deepseek-chat": {
                "prompt": 0.00000014,
                "completion": 0.00000028
            }
        }
    }
    calculator = CostCalculator(pricing)
    
    cost = calculator.calculate_cost(
        provider="deepseek",
        model="deepseek-chat",
        prompt_tokens=1000,
        completion_tokens=500
    )
    
    # (1000 / 1_000_000) * 0.00000014 + (500 / 1_000_000) * 0.00000028
    # = 0.00000014 + 0.00000014 = 0.00000028
    assert cost == pytest.approx(0.00000028, rel=1e-9)

def test_unknown_provider_returns_zero():
    """Test unknown provider returns zero cost"""
    calculator = CostCalculator({})
    cost = calculator.calculate_cost("unknown", "model", 100, 50)
    assert cost == 0.0

def test_unknown_model_returns_zero():
    """Test unknown model returns zero cost"""
    pricing = {"openai": {}}
    calculator = CostCalculator(pricing)
    cost = calculator.calculate_cost("openai", "unknown-model", 100, 50)
    assert cost == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/service/test_cost_calculator.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'service.cost_calculator'"

- [ ] **Step 3: Implement cost calculator**

```python
# service/cost_calculator.py
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CostCalculator:
    """Calculate LLM costs from token counts"""
    
    def __init__(self, pricing: Dict[str, Dict[str, Dict[str, float]]]):
        """
        Initialize with pricing data
        
        Args:
            pricing: Nested dict with structure:
                {
                    "provider": {
                        "model": {
                            "prompt": cost_per_million_tokens,
                            "completion": cost_per_million_tokens
                        }
                    }
                }
        """
        self.pricing = pricing
    
    def calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for an LLM call
        
        Args:
            provider: LLM provider (openai, deepseek)
            model: Model name (gpt-4o, deepseek-chat)
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
        
        Returns:
            Cost in USD
        """
        try:
            model_pricing = self.pricing[provider][model]
            prompt_cost = (prompt_tokens / 1_000_000) * model_pricing["prompt"]
            completion_cost = (completion_tokens / 1_000_000) * model_pricing["completion"]
            return prompt_cost + completion_cost
        except KeyError:
            logger.warning(
                f"No pricing found for provider={provider}, model={model}. Returning 0.0"
            )
            return 0.0
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/service/test_cost_calculator.py -v
```

Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit cost calculator**

```bash
git add service/cost_calculator.py tests/service/test_cost_calculator.py
git commit -m "feat(service): add LLM cost calculator"
```

## Task 4: Prometheus Metrics Registry

**Files:**
- Create: `service/metrics.py`
- Create: `tests/service/test_metrics.py`

- [ ] **Step 1: Write test for metrics registry**

```python
# tests/service/test_metrics.py
import pytest
from prometheus_client import REGISTRY
from service.metrics import MetricsRegistry

def test_track_llm_request():
    """Test tracking LLM request increments counter"""
    registry = MetricsRegistry()
    
    # Track a successful LLM request
    registry.track_llm_request(
        service="ai-market-studio",
        provider="openai",
        model="gpt-4o",
        status="success"
    )
    
    # Verify counter was incremented
    metric = registry.llm_requests_total
    samples = list(metric.collect())[0].samples
    
    # Find the sample with our labels
    found = False
    for sample in samples:
        if (sample.labels.get("service") == "ai-market-studio" and
            sample.labels.get("provider") == "openai" and
            sample.labels.get("model") == "gpt-4o" and
            sample.labels.get("status") == "success"):
            assert sample.value == 1.0
            found = True
            break
    
    assert found, "Expected metric sample not found"

def test_track_llm_tokens():
    """Test tracking LLM tokens"""
    registry = MetricsRegistry()
    
    registry.track_llm_tokens(
        service="ai-market-studio",
        provider="openai",
        model="gpt-4o",
        token_type="prompt",
        count=150
    )
    
    metric = registry.llm_tokens_total
    samples = list(metric.collect())[0].samples
    
    found = False
    for sample in samples:
        if (sample.labels.get("service") == "ai-market-studio" and
            sample.labels.get("token_type") == "prompt"):
            assert sample.value == 150.0
            found = True
            break
    
    assert found

def test_track_llm_cost():
    """Test tracking LLM cost"""
    registry = MetricsRegistry()
    
    registry.track_llm_cost(
        service="ai-market-studio",
        provider="openai",
        model="gpt-4o",
        cost=0.00195
    )
    
    metric = registry.llm_cost_usd_total
    samples = list(metric.collect())[0].samples
    
    found = False
    for sample in samples:
        if sample.labels.get("service") == "ai-market-studio":
            assert sample.value == pytest.approx(0.00195, rel=1e-6)
            found = True
            break
    
    assert found
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/service/test_metrics.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'service.metrics'"

- [ ] **Step 3: Implement metrics registry (part 1 - setup)**

```python
# service/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info
import logging

logger = logging.getLogger(__name__)

class MetricsRegistry:
    """Prometheus metrics registry for observability service"""
    
    def __init__(self):
        # LLM metrics
        self.llm_requests_total = Counter(
            'llm_requests_total',
            'Total LLM requests',
            ['service', 'provider', 'model', 'status']
        )
        
        self.llm_tokens_total = Counter(
            'llm_tokens_total',
            'Total LLM tokens',
            ['service', 'provider', 'model', 'token_type']
        )
        
        self.llm_cost_usd_total = Counter(
            'llm_cost_usd_total',
            'Total LLM cost in USD',
            ['service', 'provider', 'model']
        )
        
        self.llm_request_duration_seconds = Histogram(
            'llm_request_duration_seconds',
            'LLM request duration',
            ['service', 'provider', 'model'],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        self.llm_errors_total = Counter(
            'llm_errors_total',
            'Total LLM errors',
            ['service', 'provider', 'model', 'error_type']
        )
        
        # HTTP metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['service', 'endpoint', 'method', 'status_code']
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['service', 'endpoint', 'method'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.http_requests_in_flight = Gauge(
            'http_requests_in_flight',
            'HTTP requests in flight',
            ['service']
        )
        
        # System health metrics
        self.service_up = Gauge(
            'service_up',
            'Service health status',
            ['service']
        )
        
        # Track services and metrics count
        self._services = {}  # {service_name: {"last_seen": timestamp, "count": int}}
```

- [ ] **Step 4: Implement metrics registry (part 2 - tracking methods)**

```python
# service/metrics.py (continued - add to the class)
    
    def track_llm_request(self, service: str, provider: str, model: str, status: str):
        """Track an LLM request"""
        self.llm_requests_total.labels(
            service=service,
            provider=provider,
            model=model,
            status=status
        ).inc()
    
    def track_llm_tokens(
        self,
        service: str,
        provider: str,
        model: str,
        token_type: str,
        count: int
    ):
        """Track LLM token usage"""
        self.llm_tokens_total.labels(
            service=service,
            provider=provider,
            model=model,
            token_type=token_type
        ).inc(count)
    
    def track_llm_cost(self, service: str, provider: str, model: str, cost: float):
        """Track LLM cost"""
        self.llm_cost_usd_total.labels(
            service=service,
            provider=provider,
            model=model
        ).inc(cost)
    
    def track_llm_duration(
        self,
        service: str,
        provider: str,
        model: str,
        duration: float
    ):
        """Track LLM request duration"""
        self.llm_request_duration_seconds.labels(
            service=service,
            provider=provider,
            model=model
        ).observe(duration)
    
    def track_llm_error(
        self,
        service: str,
        provider: str,
        model: str,
        error_type: str
    ):
        """Track LLM error"""
        self.llm_errors_total.labels(
            service=service,
            provider=provider,
            model=model,
            error_type=error_type
        ).inc()
    
    def track_http_request(
        self,
        service: str,
        endpoint: str,
        method: str,
        status_code: int
    ):
        """Track HTTP request"""
        self.http_requests_total.labels(
            service=service,
            endpoint=endpoint,
            method=method,
            status_code=str(status_code)
        ).inc()
    
    def track_http_duration(
        self,
        service: str,
        endpoint: str,
        method: str,
        duration: float
    ):
        """Track HTTP request duration"""
        self.http_request_duration_seconds.labels(
            service=service,
            endpoint=endpoint,
            method=method
        ).observe(duration)
    
    def set_service_health(self, service: str, is_up: bool):
        """Set service health status"""
        self.service_up.labels(service=service).set(1 if is_up else 0)
    
    def register_service(self, service_name: str):
        """Register a service as active"""
        from datetime import datetime
        if service_name not in self._services:
            self._services[service_name] = {"last_seen": datetime.utcnow().isoformat(), "count": 0}
        self._services[service_name]["last_seen"] = datetime.utcnow().isoformat()
        self._services[service_name]["count"] += 1
    
    def get_tracked_services(self) -> list[str]:
        """Get list of tracked services"""
        return list(self._services.keys())
    
    def get_service_info(self, service_name: str) -> dict:
        """Get service info"""
        return self._services.get(service_name, )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/service/test_metrics.py -v
```

Expected: PASS (all 3 tests)

- [ ] **Step 6: Commit metrics registry**

```bash
git add service/metrics.py tests/service/test_metrics.py
git commit -m "feat(service): add Prometheus metrics registry"
```

## Task 5: Configuration Loader

**Files:**
- Create: `service/config.py`
- Create: `tests/service/test_config.py`

- [ ] **Step 1: Write test for config loading**

```python
# tests/service/test_config.py
import pytest
import yaml
import tempfile
from pathlib import Path
from service.config import load_pricing_config

def test_load_pricing_config():
    """Test loading pricing config from YAML"""
    pricing_yaml = """
openai:
  gpt-4o:
    prompt: 0.000005
    completion: 0.000015
  gpt-4o-mini:
    prompt: 0.00000015
    completion: 0.0000006
deepseek:
  deepseek-chat:
    prompt: 0.00000014
    completion: 0.00000028
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(pricing_yaml)
        f.flush()
        
        pricing = load_pricing_config(f.name)
        
        assert "openai" in pricing
        assert "gpt-4o" in pricing["openai"]
        assert pricing["openai"]["gpt-4o"]["prompt"] == 0.000005
        assert pricing["openai"]["gpt-4o"]["completion"] == 0.000015
        
        assert "deepseek" in pricing
        assert pricing["deepseek"]["deepseek-chat"]["prompt"] == 0.00000014
        
        Path(f.name).unlink()

def test_load_pricing_config_file_not_found():
    """Test loading non-existent config returns empty dict"""
    pricing = load_pricing_config("/nonexistent/file.yaml")
    assert pricing == {}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/service/test_config.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'service.config'"

- [ ] **Step 3: Implement config loader**

```python
# service/config.py
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def load_pricing_config(config_path: str) -> Dict[str, Any]:
    """
    Load LLM pricing configuration from YAML file
    
    Args:
        config_path: Path to pricing.yaml file
    
    Returns:
        Pricing dictionary
    """
    try:
        with open(config_path, 'r') as f:
            pricing = yaml.safe_load(f)
            logger.info(f"Loaded pricing config from {config_path}")
            return pricing or {}
    except FileNotFoundError:
        logger.warning(f"Pricing config not found at {config_path}, using empty pricing")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse pricing config: {e}")
        return {}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/service/test_config.py -v
```

Expected: PASS (both tests)

- [ ] **Step 5: Commit config loader**

```bash
git add service/config.py tests/service/test_config.py
git commit -m "feat(service): add configuration loader for pricing"
```

## Task 6: FastAPI Service - Main Application

**Files:**
- Create: `service/main.py`
- Create: `tests/service/test_main.py`

- [ ] **Step 1: Write test for /health endpoint**

```python
# tests/service/test_main.py
import pytest
from fastapi.testclient import TestClient
from service.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test /health endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "services_tracked" in data
    assert "metrics_received_last_minute" in data

def test_metrics_endpoint():
    """Test /metrics endpoint returns Prometheus format"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    # Should contain at least some metric definitions
    assert "# HELP" in response.text or "# TYPE" in response.text

def test_ingest_llm_call():
    """Test /ingest endpoint accepts LLM call metrics"""
    payload = {
        "service_name": "ai-market-studio",
        "metric_type": "llm_call",
        "trace_id": "test-trace-123",
        "timestamp": "2026-04-18T10:30:00Z",
        "data": {
            "provider": "openai",
            "model": "gpt-4o",
            "prompt_tokens": 150,
            "completion_tokens": 80,
            "duration_seconds": 1.2,
            "status": "success"
        }
    }
    
    response = client.post("/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["trace_id"] == "test-trace-123"

def test_services_endpoint():
    """Test /services endpoint returns tracked services"""
    response = client.get("/services")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert isinstance(data["services"], list)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/service/test_main.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'service.main'"

- [ ] **Step 3: Implement FastAPI application (part 1 - setup)**

```python
# service/main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import logging
import os
from datetime import datetime

from service.models import (
    MetricIngestRequest,
    MetricIngestResponse,
    HealthResponse,
    ServicesResponse,
    ServiceInfo,
    LLMCallData
)
from service.metrics import MetricsRegistry
from service.cost_calculator import CostCalculator
from service.config import load_pricing_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI SRE Observability Service",
    description="Centralized observability for AI services",
    version="0.1.0"
)

# Load pricing config
pricing_config_path = os.getenv("PRICING_CONFIG_PATH", "/config/pricing.yaml")
pricing = load_pricing_config(pricing_config_path)
logger.info(f"Loaded pricing for {len(pricing)} providers")

# Initialize components
metrics_registry = MetricsRegistry()
cost_calculator = CostCalculator(pricing)

# Track metrics received in last minute (for health check)
metrics_received_count = 0
last_reset_time = datetime.utcnow()
```

- [ ] **Step 4: Implement FastAPI application (part 2 - endpoints)**

```python
# service/main.py (continued)

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    global metrics_received_count, last_reset_time
    
    # Reset counter if more than 1 minute has passed
    now = datetime.utcnow()
    if (now - last_reset_time).total_seconds() > 60:
        metrics_received_count = 0
        last_reset_time = now
    
    return HealthResponse(
        status="ok",
        services_tracked=metrics_registry.get_tracked_services(),
        metrics_received_last_minute=metrics_received_count
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(
        content=generate_latest().decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/services", response_model=ServicesResponse)
async def services():
    """List tracked services"""
    service_list = []
    for service_name in metrics_registry.get_tracked_services():
        info = metrics_registry.get_service_info(service_name)
        if info:
            service_list.append(ServiceInfo(
                name=service_name,
                last_seen=info["last_seen"],
                metrics_count=info["count"]
            ))
    
    return ServicesResponse(services=service_list)

@app.post("/ingest", response_model=MetricIngestResponse)
async def ingest(request: MetricIngestRequest):
    """Ingest metrics from SDK clients"""
    global metrics_received_count
    
    try:
        # Register service
        metrics_registry.register_service(request.service_name)
        metrics_received_count += 1
        
        # Process based on metric type
        if request.metric_type == "llm_call" and isinstance(request.data, LLMCallData):
            # Track LLM request
            metrics_registry.track_llm_request(
                service=request.service_name,
                provider=request.data.provider,
                model=request.data.model,
                status=request.data.status
            )
            
            # Track tokens
            metrics_registry.track_llm_tokens(
                service=request.service_name,
                provider=request.data.provider,
                model=request.data.model,
                token_type="prompt",
                count=request.data.prompt_tokens
            )
            metrics_registry.track_llm_tokens(
                service=request.service_name,
                provider=request.data.provider,
                model=request.data.model,
                token_type="completion",
                count=request.data.completion_tokens
            )
            
            # Calculate and track cost
            cost = cost_calculator.calculate_cost(
                provider=request.data.provider,
                model=request.data.model,
                prompt_tokens=request.data.prompt_tokens,
                completion_tokens=request.data.completion_tokens
            )
            metrics_registry.track_llm_cost(
                service=request.service_name,
                provider=request.data.provider,
                model=request.data.model,
                cost=cost
            )
            
            # Track duration
            metrics_registry.track_llm_duration(
                service=request.service_name,
                provider=request.data.provider,
                model=request.data.model,
                duration=request.data.duration_seconds
            )
            
            # Track error if status is error
            if request.data.status == "error" and request.data.error_type:
                metrics_registry.track_llm_error(
                    service=request.service_name,
                    provider=request.data.provider,
                    model=request.data.model,
                    error_type=request.data.error_type
                )
        
        return MetricIngestResponse(
            status="ok",
            trace_id=request.trace_id
        )
    
    except Exception as e:
        logger.error(f"Failed to ingest metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("AI SRE Observability Service started")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("AI SRE Observability Service shutting down")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/service/test_main.py -v
```

Expected: PASS (all 4 tests)

- [ ] **Step 6: Commit FastAPI service**

```bash
git add service/main.py tests/service/test_main.py
git commit -m "feat(service): add FastAPI application with endpoints"
```

## Task 7: SDK - Data Models and Transport

**Files:**
- Create: `sdk/ai_sre_observability/models.py`
- Create: `sdk/ai_sre_observability/transport.py`
- Create: `tests/sdk/test_transport.py`

- [ ] **Step 1: Create SDK data models**

```python
# sdk/ai_sre_observability/models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class LLMCallMetric(BaseModel):
    """LLM call metric data"""
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    duration_seconds: float
    status: str = "success"
    error_type: Optional[str] = None

class MetricPayload(BaseModel):
    """Metric payload sent to observability service"""
    service_name: str
    metric_type: str
    trace_id: str
    timestamp: str
    data: Dict[str, Any]
```

- [ ] **Step 2: Write test for async transport**

```python
# tests/sdk/test_transport.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from sdk.ai_sre_observability.transport import AsyncTransport

@pytest.mark.asyncio
async def test_send_metric_success():
    """Test sending metric successfully"""
    transport = AsyncTransport("http://localhost:8080")
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "ok", "trace_id": "123"}
        
        result = await transport.send_metric({
            "service_name": "test",
            "metric_type": "llm_call",
            "trace_id": "123",
            "timestamp": "2026-04-18T10:00:00Z",
            "data": {}
        })
        
        assert result is True
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_send_metric_failure_graceful():
    """Test sending metric fails gracefully"""
    transport = AsyncTransport("http://localhost:8080")
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Network error")
        
        result = await transport.send_metric({"test": "data"})
        
        assert result is False  # Should not raise, just return False

@pytest.mark.asyncio
async def test_send_batch():
    """Test sending batch of metrics"""
    transport = AsyncTransport("http://localhost:8080")
    
    metrics = [
        {"service_name": "test", "metric_type": "llm_call", "trace_id": "1", "timestamp": "2026-04-18T10:00:00Z", "data": {}},
        {"service_name": "test", "metric_type": "llm_call", "trace_id": "2", "timestamp": "2026-04-18T10:00:01Z", "data": {}}
    ]
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "ok"}
        
        await transport.send_batch(metrics)
        
        assert mock_post.call_count == 2
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/sdk/test_transport.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'sdk.ai_sre_observability.transport'"

- [ ] **Step 4: Implement async transport**

```python
# sdk/ai_sre_observability/transport.py
import httpx
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AsyncTransport:
    """Async HTTP transport for sending metrics"""
    
    def __init__(self, observability_url: str, timeout: float = 5.0):
        """
        Initialize transport
        
        Args:
            observability_url: Base URL of observability service
            timeout: Request timeout in seconds
        """
        self.observability_url = observability_url
        self.timeout = timeout
        self._client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def send_metric(self, metric: Dict[str, Any]) -> bool:
        """
        Send a single metric to observability service
        
        Args:
            metric: Metric payload
        
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.observability_url}/ingest",
                json=metric
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Failed to send metric: {e}")
            return False
    
    async def send_batch(self, metrics: List[Dict[str, Any]]):
        """
        Send batch of metrics
        
        Args:
            metrics: List of metric payloads
        """
        for metric in metrics:
            await self.send_metric(metric)
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/sdk/test_transport.py -v
```

Expected: PASS (all 3 tests)

- [ ] **Step 6: Commit SDK models and transport**

```bash
git add sdk/ai_sre_observability/models.py sdk/ai_sre_observability/transport.py tests/sdk/test_transport.py
git commit -m "feat(sdk): add data models and async HTTP transport"
```

## Task 8: SDK - Observability Client

**Files:**
- Create: `sdk/ai_sre_observability/client.py`
- Create: `tests/sdk/test_client.py`

- [ ] **Step 1: Write test for ObservabilityClient**

```python
# tests/sdk/test_client.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from sdk.ai_sre_observability.client import ObservabilityClient

@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initializes correctly"""
    client = ObservabilityClient(
        service_name="test-service",
        observability_url="http://localhost:8080"
    )
    
    assert client.service_name == "test-service"
    assert client.observability_url == "http://localhost:8080"
    assert client._batch == []

@pytest.mark.asyncio
async def test_track_llm_call_context_manager():
    """Test track_llm_call context manager"""
    client = ObservabilityClient("test-service", "http://localhost:8080")
    
    with patch.object(client, '_add_to_batch') as mock_add:
        with client.track_llm_call(provider="openai", model="gpt-4o") as tracker:
            trace_id = tracker.trace_id
            assert trace_id is not None
            
            tracker.record_tokens(prompt_tokens=100, completion_tokens=50)
        
        # Verify metric was added to batch
        mock_add.assert_called_once()
        call_args = mock_add.call_args[0][0]
        assert call_args["service_name"] == "test-service"
        assert call_args["metric_type"] == "llm_call"
        assert call_args["data"]["provider"] == "openai"
        assert call_args["data"]["model"] == "gpt-4o"
        assert call_args["data"]["prompt_tokens"] == 100
        assert call_args["data"]["completion_tokens"] == 50

@pytest.mark.asyncio
async def test_increment_metric():
    """Test increment counter metric"""
    client = ObservabilityClient("test-service", "http://localhost:8080")
    
    with patch.object(client, '_add_to_batch') as mock_add:
        client.increment("pdf_exports_total", labels={"type": "fx-insight"})
        
        mock_add.assert_called_once()
        call_args = mock_add.call_args[0][0]
        assert call_args["metric_type"] == "business"
        assert call_args["data"]["metric_name"] == "pdf_exports_total"
        assert call_args["data"]["value"] == 1.0
        assert call_args["data"]["labels"]["type"] == "fx-insight"

@pytest.mark.asyncio
async def test_histogram_metric():
    """Test histogram metric"""
    client = ObservabilityClient("test-service", "http://localhost:8080")
    
    with patch.object(client, '_add_to_batch') as mock_add:
        client.histogram("request_duration_seconds", value=1.5)
        
        mock_add.assert_called_once()
        call_args = mock_add.call_args[0][0]
        assert call_args["data"]["value"] == 1.5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/sdk/test_client.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'sdk.ai_sre_observability.client'"

- [ ] **Step 3: Implement ObservabilityClient (part 1 - setup)**

```python
# sdk/ai_sre_observability/client.py
import asyncio
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager

from sdk.ai_sre_observability.transport import AsyncTransport

logger = logging.getLogger(__name__)

class LLMCallTracker:
    """Context manager for tracking LLM calls"""
    
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.start_time = None
        self.duration_seconds = 0.0
        self.status = "success"
        self.error_type = None
    
    def record_tokens(self, prompt_tokens: int, completion_tokens: int):
        """Record token counts"""
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
    
    def record_error(self, error_type: str):
        """Record error"""
        self.status = "error"
        self.error_type = error_type

class ObservabilityClient:
    """Client for sending metrics to observability service"""
    
    def __init__(
        self,
        service_name: str,
        observability_url: str,
        batch_interval: float = 5.0
    ):
        """
        Initialize observability client
        
        Args:
            service_name: Name of the service
            observability_url: URL of observability service
            batch_interval: Interval for sending batches (seconds)
        """
        self.service_name = service_name
        self.observability_url = observability_url
        self.batch_interval = batch_interval
        
        self._batch = []
        self._lock = asyncio.Lock()
        self._transport = AsyncTransport(observability_url)
        self._batch_task = None
        self._running = False
    
    def start(self):
        """Start background batch sender"""
        if not self._running:
            self._running = True
            self._batch_task = asyncio.create_task(self._batch_sender())
    
    async def stop(self):
        """Stop background batch sender and flush remaining metrics"""
        self._running = False
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining metrics
        await self._flush_batch()
        await self._transport.close()
```

- [ ] **Step 4: Implement ObservabilityClient (part 2 - tracking methods)**

```python
# sdk/ai_sre_observability/client.py (continued)
    
    @contextmanager
    def track_llm_call(self, provider: str, model: str):
        """
        Context manager for tracking LLM calls
        
        Args:
            provider: LLM provider (openai, deepseek)
            model: Model name (gpt-4o, deepseek-chat)
        
        Yields:
            LLMCallTracker instance
        """
        trace_id = str(uuid.uuid4())
        tracker = LLMCallTracker(trace_id)
        tracker.start_time = datetime.utcnow()
        
        try:
            yield tracker
        except Exception as e:
            tracker.record_error(type(e).__name__)
            raise
        finally:
            # Calculate duration
            if tracker.start_time:
                duration = (datetime.utcnow() - tracker.start_time).total_seconds()
                tracker.duration_seconds = duration
            
            # Add to batch
            self._add_to_batch({
                "service_name": self.service_name,
                "metric_type": "llm_call",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": {
                    "provider": provider,
                    "model": model,
                    "prompt_tokens": tracker.prompt_tokens,
                    "completion_tokens": tracker.completion_tokens,
                    "duration_seconds": tracker.duration_seconds,
                    "status": tracker.status,
                    "error_type": tracker.error_type
                }
            })
    
    def increment(self, metric_name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric
        
        Args:
            metric_name: Name of the metric
            value: Value to increment by
            labels: Optional labels
        """
        self._add_to_batch({
            "service_name": self.service_name,
            "metric_type": "business",
            "trace_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": {
                "metric_name": metric_name,
                "value": value,
                "labels": labels or {}
            }
        })
    
    def histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Record a histogram metric
        
        Args:
            metric_name: Name of the metric
            value: Value to record
            labels: Optional labels
        """
        self._add_to_batch({
            "service_name": self.service_name,
            "metric_type": "business",
            "trace_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": {
                "metric_name": metric_name,
                "value": value,
                "labels": labels or {}
            }
        })
    
    def _add_to_batch(self, metric: Dict[str, Any]):
        """Add metric to batch (non-async)"""
        self._batch.append(metric)
    
    async def _batch_sender(self):
        """Background task to send batches periodically"""
        while self._running:
            await asyncio.sleep(self.batch_interval)
            await self._flush_batch()
    
    async def _flush_batch(self):
        """Flush current batch to observability service"""
        async with self._lock:
            if self._batch:
                batch_to_send = self._batch.copy()
                self._batch.clear()
                
                try:
                    await self._transport.send_batch(batch_to_send)
                    logger.debug(f"Sent batch of {len(batch_to_send)} metrics")
                except Exception as e:
                    logger.warning(f"Failed to send batch: {e}")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/sdk/test_client.py -v
```

Expected: PASS (all 4 tests)

- [ ] **Step 6: Commit ObservabilityClient**

```bash
git add sdk/ai_sre_observability/client.py tests/sdk/test_client.py
git commit -m "feat(sdk): add ObservabilityClient with batching"
```

## Task 9: SDK - Decorator and Public API

**Files:**
- Create: `sdk/ai_sre_observability/decorators.py`
- Create: `sdk/ai_sre_observability/__init__.py`
- Create: `tests/sdk/test_decorators.py`

- [ ] **Step 1: Write test for @track_llm_call decorator**

```python
# tests/sdk/test_decorators.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from sdk.ai_sre_observability import setup_observability, track_llm_call, get_client

@pytest.mark.asyncio
async def test_track_llm_call_decorator():
    """Test @track_llm_call decorator tracks calls"""
    setup_observability("test-service", "http://localhost:8080")
    client = get_client()
    
    @track_llm_call(provider="openai", model="gpt-4o")
    async def mock_llm_call():
        return {"usage": {"prompt_tokens": 100, "completion_tokens": 50}}
    
    with patch.object(client, 'track_llm_call') as mock_track:
        mock_tracker = MagicMock()
        mock_track.return_value.__enter__ = MagicMock(return_value=mock_tracker)
        mock_track.return_value.__exit__ = MagicMock(return_value=False)
        
        result = await mock_llm_call()
        
        assert result["usage"]["prompt_tokens"] == 100
        mock_track.assert_called_once_with(provider="openai", model="gpt-4o")

def test_setup_observability():
    """Test setup_observability creates global client"""
    setup_observability("test-service", "http://localhost:8080")
    client = get_client()
    
    assert client is not None
    assert client.service_name == "test-service"
    assert client.observability_url == "http://localhost:8080"

def test_get_client_before_setup_raises():
    """Test get_client before setup raises error"""
    # Reset global client
    import sdk.ai_sre_observability as obs_module
    obs_module._global_client = None
    
    with pytest.raises(RuntimeError, match="setup_observability"):
        get_client()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/sdk/test_decorators.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'sdk.ai_sre_observability.decorators'"

- [ ] **Step 3: Implement decorator**

```python
# sdk/ai_sre_observability/decorators.py
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

def track_llm_call(provider: str, model: str):
    """
    Decorator to track LLM calls
    
    Args:
        provider: LLM provider (openai, deepseek)
        model: Model name (gpt-4o, deepseek-chat)
    
    Usage:
        @track_llm_call(provider="openai", model="gpt-4o")
        async def call_llm(messages):
            response = await client.chat.completions.create(...)
            return response
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            from sdk.ai_sre_observability import get_client
            
            client = get_client()
            
            with client.track_llm_call(provider=provider, model=model) as tracker:
                try:
                    result = await func(*args, **kwargs)
                    
                    # Try to extract token counts from result
                    if hasattr(result, 'usage'):
                        tracker.record_tokens(
                            prompt_tokens=result.usage.prompt_tokens,
                            completion_tokens=result.usage.completion_tokens
                        )
                    
                    return result
                except Exception as e:
                    tracker.record_error(type(e).__name__)
                    raise
        
        return wrapper
    return decorator
```

- [ ] **Step 4: Implement public API**

```python
# sdk/ai_sre_observability/__init__.py
"""AI SRE Observability SDK"""

from sdk.ai_sre_observability.client import ObservabilityClient
from sdk.ai_sre_observability.decorators import track_llm_call

__version__ = "0.1.0"

# Global client instance
_global_client: ObservabilityClient = None

def setup_observability(service_name: str, observability_url: str):
    """
    Setup global observability client
    
    Args:
        service_name: Name of the service
        observability_url: URL of observability service
    
    Example:
        setup_observability(
            service_name="ai-market-studio",
            observability_url="http://ai-sre-observability.default.svc.cluster.local:8080"
        )
    """
    global _global_client
    _global_client = ObservabilityClient(service_name, observability_url)
    _global_client.start()

def get_client() -> ObservabilityClient:
    """
    Get global observability client
    
    Returns:
        ObservabilityClient instance
    
    Raises:
        RuntimeError: If setup_observability has not been called
    """
    if _global_client is None:
        raise RuntimeError(
            "Observability client not initialized. "
            "Call setup_observability() first."
        )
    return _global_client

__all__ = [
    "setup_observability",
    "get_client",
    "track_llm_call",
    "ObservabilityClient"
]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/sdk/test_decorators.py -v
```

Expected: PASS (all 3 tests)

- [ ] **Step 6: Commit decorator and public API**

```bash
git add sdk/ai_sre_observability/decorators.py sdk/ai_sre_observability/__init__.py tests/sdk/test_decorators.py
git commit -m "feat(sdk): add @track_llm_call decorator and public API"
```

## Task 10: SDK Package Setup

**Files:**
- Create: `sdk/setup.py`
- Create: `sdk/README.md`
- Create: `sdk/ai_sre_observability/pricing.py`

- [ ] **Step 1: Create SDK setup.py**

```python
# sdk/setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-sre-observability-sdk",
    version="0.1.0",
    author="AI SRE Team",
    description="Lightweight SDK for AI service observability",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "httpx>=0.26.0",
        "pydantic>=2.5.0",
    ],
)
```

- [ ] **Step 2: Create SDK README**

```markdown
# AI SRE Observability SDK

Lightweight Python SDK for instrumenting AI services with observability metrics.

## Installation

```bash
pip install ai-sre-observability-sdk
```

## Quick Start

```python
from ai_sre_observability import setup_observability, track_llm_call

# Setup once at application startup
setup_observability(
    service_name="ai-market-studio",
    observability_url="http://ai-sre-observability.default.svc.cluster.local:8080"
)

# Track LLM calls with decorator
@track_llm_call(provider="openai", model="gpt-4o")
async def call_llm(messages):
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return response

# Track custom metrics
from ai_sre_observability import get_client

obs = get_client()
obs.increment("pdf_exports_total", labels={"type": "fx-insight"})
obs.histogram("dashboard_generation_seconds", value=2.3)
```

## Features

- **Async fire-and-forget** - Never blocks your service code
- **Automatic batching** - Reduces network overhead
- **Graceful degradation** - Continues working if observability service is down
- **Trace ID generation** - Automatic request correlation
- **<1% overhead** - Minimal performance impact

## API Reference

### setup_observability(service_name, observability_url)

Initialize the global observability client.

**Parameters:**
- `service_name` (str): Name of your service
- `observability_url` (str): URL of the observability service

### @track_llm_call(provider, model)

Decorator to automatically track LLM calls.

**Parameters:**
- `provider` (str): LLM provider (openai, deepseek)
- `model` (str): Model name (gpt-4o, deepseek-chat)

### get_client()

Get the global observability client for custom metrics.

**Returns:** ObservabilityClient instance

## License

MIT
```

- [ ] **Step 3: Create pricing constants file**

```python
# sdk/ai_sre_observability/pricing.py
"""LLM pricing constants for local fallback"""

PRICING = {
    "openai": {
        "gpt-4o": {
            "prompt": 0.000005,
            "completion": 0.000015
        },
        "gpt-4o-mini": {
            "prompt": 0.00000015,
            "completion": 0.0000006
        }
    },
    "deepseek": {
        "deepseek-chat": {
            "prompt": 0.00000014,
            "completion": 0.00000028
        }
    }
}
```

- [ ] **Step 4: Test SDK package installation**

```bash
cd sdk
pip install -e .
python -c "from ai_sre_observability import setup_observability; print('SDK installed successfully')"
```

Expected: "SDK installed successfully"

- [ ] **Step 5: Commit SDK package setup**

```bash
git add sdk/setup.py sdk/README.md sdk/ai_sre_observability/pricing.py
git commit -m "feat(sdk): add package setup and documentation"
```

## Task 11: Service Dockerfile

**Files:**
- Create: `service/Dockerfile`

- [ ] **Step 1: Create multi-stage Dockerfile**

```dockerfile
# service/Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8080/health', timeout=2.0)" || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

- [ ] **Step 2: Test Docker build**

```bash
cd service
docker build -t ai-sre-observability:test .
```

Expected: Build succeeds

- [ ] **Step 3: Test Docker run locally**

```bash
docker run -p 8080:8080 -e PRICING_CONFIG_PATH=/app/pricing.yaml ai-sre-observability:test
```

Expected: Service starts and responds to http://localhost:8080/health

- [ ] **Step 4: Stop test container**

```bash
docker ps | grep ai-sre-observability | awk '{print $1}' | xargs docker stop
```

- [ ] **Step 5: Commit Dockerfile**

```bash
git add service/Dockerfile
git commit -m "feat(service): add multi-stage Dockerfile"
```

## Task 12: Kubernetes Manifests

**Files:**
- Create: `k8s/configmap.yaml`
- Create: `k8s/deployment.yaml`
- Create: `k8s/service.yaml`

- [ ] **Step 1: Create ConfigMap with pricing data**

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-sre-observability-config
  namespace: default
data:
  pricing.yaml: |
    openai:
      gpt-4o:
        prompt: 0.000005
        completion: 0.000015
      gpt-4o-mini:
        prompt: 0.00000015
        completion: 0.0000006
    deepseek:
      deepseek-chat:
        prompt: 0.00000014
        completion: 0.00000028
```

- [ ] **Step 2: Create Deployment manifest**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-sre-observability
  namespace: default
  labels:
    app: ai-sre-observability
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ai-sre-observability
  template:
    metadata:
      labels:
        app: ai-sre-observability
    spec:
      containers:
      - name: observability-service
        image: gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: SERVICE_NAME
          value: "ai-sre-observability"
        - name: PRICING_CONFIG_PATH
          value: "/config/pricing.yaml"
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: config
          mountPath: /config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: ai-sre-observability-config
```

- [ ] **Step 3: Create Service manifest**

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-sre-observability
  namespace: default
  labels:
    app: ai-sre-observability
spec:
  type: ClusterIP
  selector:
    app: ai-sre-observability
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
    name: http
```

- [ ] **Step 4: Validate manifests**

```bash
kubectl apply --dry-run=client -f k8s/configmap.yaml
kubectl apply --dry-run=client -f k8s/deployment.yaml
kubectl apply --dry-run=client -f k8s/service.yaml
```

Expected: All manifests validate successfully

- [ ] **Step 5: Commit Kubernetes manifests**

```bash
git add k8s/
git commit -m "feat(k8s): add Kubernetes deployment manifests"
```

## Task 13: Deploy to GKE

**Files:**
- None (deployment task)

- [ ] **Step 1: Build and push Docker image**

```bash
cd service
docker build -t gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest .
docker push gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest
```

Expected: Image pushed successfully

- [ ] **Step 2: Apply ConfigMap**

```bash
kubectl apply -f k8s/configmap.yaml
```

Expected: `configmap/ai-sre-observability-config created`

- [ ] **Step 3: Apply Deployment**

```bash
kubectl apply -f k8s/deployment.yaml
```

Expected: `deployment.apps/ai-sre-observability created`

- [ ] **Step 4: Apply Service**

```bash
kubectl apply -f k8s/service.yaml
```

Expected: `service/ai-sre-observability created`

- [ ] **Step 5: Verify deployment**

```bash
kubectl get pods -l app=ai-sre-observability
kubectl logs -l app=ai-sre-observability --tail=50
```

Expected: Pod running, logs show "AI SRE Observability Service started"

- [ ] **Step 6: Test health endpoint**

```bash
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://ai-sre-observability.default.svc.cluster.local:8080/health
```

Expected: `{"status":"ok","services_tracked":[],"metrics_received_last_minute":0}`

- [ ] **Step 7: Test metrics endpoint**

```bash
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://ai-sre-observability.default.svc.cluster.local:8080/metrics
```

Expected: Prometheus metrics output

- [ ] **Step 8: Document deployment**

```bash
cat > DEPLOYMENT.md << 'EOF'
# Deployment Guide

## Prerequisites

- GKE cluster: `helloworld-cluster` (us-central1)
- GCP project: `gen-lang-client-0896070179`
- kubectl configured with cluster credentials

## Deploy Observability Service

```bash
# Build and push image
cd service
docker build -t gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest .
docker push gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest

# Apply manifests
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Verify
kubectl get pods -l app=ai-sre-observability
kubectl logs -l app=ai-sre-observability
```

## Service URL

Internal: `http://ai-sre-observability.default.svc.cluster.local:8080`

## Endpoints

- `/health` - Health check
- `/metrics` - Prometheus metrics
- `/services` - List tracked services
- `/ingest` - Ingest metrics (POST)

## Update Deployment

```bash
# Rebuild and push image
docker build -t gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest .
docker push gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest

# Rolling restart
kubectl rollout restart deployment/ai-sre-observability
kubectl rollout status deployment/ai-sre-observability
```
EOF
```

- [ ] **Step 9: Commit deployment documentation**

```bash
git add DEPLOYMENT.md
git commit -m "docs: add deployment guide for GKE"
```

## Task 14: Grafana Dashboard - Service Overview

**Files:**
- Create: `grafana/dashboards/service-overview.json`

- [ ] **Step 1: Create Service Overview dashboard JSON**

```json
{
  "dashboard": {
    "title": "AI Services Overview",
    "tags": ["ai", "observability"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Service Health Status",
        "type": "table",
        "targets": [
          {
            "expr": "service_up",
            "format": "table",
            "instant": true
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Request Rate by Service",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 3,
        "title": "Error Rate by Service",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m])",
            "legendFormat": "{{service}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      },
      {
        "id": 4,
        "title": "P95 Latency by Service",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{service}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
      },
      {
        "id": 5,
        "title": "Requests per Minute Heatmap",
        "type": "heatmap",
        "targets": [
          {
            "expr": "rate(http_requests_total[1m])"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
      }
    ],
    "templating": {
      "list": [
        {
          "name": "service",
          "type": "query",
          "query": "label_values(service_up, service)"
        }
      ]
    }
  }
}
```

- [ ] **Step 2: Commit Service Overview dashboard**

```bash
git add grafana/dashboards/service-overview.json
git commit -m "feat(grafana): add Service Overview dashboard"
```

## Task 15: Grafana Dashboard - LLM Cost & Usage

**Files:**
- Create: `grafana/dashboards/llm-cost.json`

- [ ] **Step 1: Create LLM Cost dashboard JSON**

```json
{
  "dashboard": {
    "title": "LLM Cost & Usage",
    "tags": ["ai", "llm", "cost"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Total LLM Cost Today",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(increase(llm_cost_usd_total[24h]))",
            "format": "time_series"
          }
        ],
        "gridPos": {"h": 4, "w": 24, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Cost by Service",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (service) (increase(llm_cost_usd_total[24h]))"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4}
      },
      {
        "id": 3,
        "title": "Cost by Model",
        "type": "bargauge",
        "targets": [
          {
            "expr": "sum by (model) (increase(llm_cost_usd_total[24h]))"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4}
      },
      {
        "id": 4,
        "title": "Token Usage Over Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_tokens_total{token_type=\"prompt\"}[5m])",
            "legendFormat": "Prompt - {{service}}"
          },
          {
            "expr": "rate(llm_tokens_total{token_type=\"completion\"}[5m])",
            "legendFormat": "Completion - {{service}}"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 12},
        "stack": true
      },
      {
        "id": 5,
        "title": "Requests per Model",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_requests_total[5m])",
            "legendFormat": "{{model}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 20}
      },
      {
        "id": 6,
        "title": "Average Cost per Request",
        "type": "gauge",
        "targets": [
          {
            "expr": "sum(rate(llm_cost_usd_total[5m])) / sum(rate(llm_requests_total[5m]))"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 20}
      }
    ],
    "templating": {
      "list": [
        {
          "name": "service",
          "type": "query",
          "query": "label_values(llm_requests_total, service)"
        },
        {
          "name": "provider",
          "type": "query",
          "query": "label_values(llm_requests_total, provider)"
        },
        {
          "name": "model",
          "type": "query",
          "query": "label_values(llm_requests_total, model)"
        }
      ]
    }
  }
}
```

- [ ] **Step 2: Commit LLM Cost dashboard**

```bash
git add grafana/dashboards/llm-cost.json
git commit -m "feat(grafana): add LLM Cost & Usage dashboard"
```

## Task 16: Grafana Dashboard - Request Tracing

**Files:**
- Create: `grafana/dashboards/request-tracing.json`

- [ ] **Step 1: Create Request Tracing dashboard JSON**

```json
{
  "dashboard": {
    "title": "Request Tracing & Debugging",
    "tags": ["ai", "tracing", "debugging"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Recent Requests",
        "type": "table",
        "targets": [
          {
            "expr": "http_requests_total",
            "format": "table",
            "instant": true
          }
        ],
        "gridPos": {"h": 10, "w": 24, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Slowest Endpoints (P95)",
        "type": "bargauge",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 10}
      },
      {
        "id": 3,
        "title": "Error Breakdown",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (status_code) (rate(http_requests_total{status_code=~\"[45]..\"}[5m]))"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 10}
      },
      {
        "id": 4,
        "title": "LLM Call Duration Distribution",
        "type": "heatmap",
        "targets": [
          {
            "expr": "rate(llm_request_duration_seconds_bucket[5m])"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 18}
      }
    ],
    "templating": {
      "list": [
        {
          "name": "trace_id",
          "type": "textbox",
          "label": "Trace ID"
        },
        {
          "name": "status_code",
          "type": "query",
          "query": "label_values(http_requests_total, status_code)"
        }
      ]
    }
  }
}
```

- [ ] **Step 2: Commit Request Tracing dashboard**

```bash
git add grafana/dashboards/request-tracing.json
git commit -m "feat(grafana): add Request Tracing dashboard"
```

- [ ] **Step 3: Create dashboard README**

```markdown
# Grafana Dashboards

Three pre-built dashboards for AI service observability.

## Dashboards

### 1. Service Overview (`service-overview.json`)

Unified visibility across all AI services.

**Panels:**
- Service Health Status (table)
- Request Rate by Service (graph)
- Error Rate by Service (graph)
- P95 Latency by Service (graph)
- Requests per Minute Heatmap

**Variables:**
- `$service` - Filter by service name

### 2. LLM Cost & Usage (`llm-cost.json`)

LLM cost tracking and optimization.

**Panels:**
- Total LLM Cost Today (single stat)
- Cost by Service (pie chart)
- Cost by Model (bar chart)
- Token Usage Over Time (stacked area)
- Requests per Model (time series)
- Average Cost per Request (gauge)

**Variables:**
- `$service` - Filter by service
- `$provider` - Filter by LLM provider
- `$model` - Filter by model name

### 3. Request Tracing (`request-tracing.json`)

Debugging and request correlation.

**Panels:**
- Recent Requests (table)
- Slowest Endpoints (bar chart)
- Error Breakdown (pie chart)
- LLM Call Duration Distribution (heatmap)

**Variables:**
- `$trace_id` - Search by trace ID
- `$status_code` - Filter by HTTP status

## Import to Grafana

```bash
# Via ConfigMap (auto-provisioning)
kubectl create configmap grafana-dashboards \
  --from-file=grafana/dashboards/ \
  -n monitoring

# Restart Grafana
kubectl rollout restart deployment/grafana -n monitoring
```

## Manual Import

1. Open Grafana UI
2. Go to Dashboards → Import
3. Upload JSON file or paste JSON content
4. Select Prometheus data source
5. Click Import
```

- [ ] **Step 4: Commit dashboard README**

```bash
git add grafana/dashboards/README.md
git commit -m "docs(grafana): add dashboard documentation"
```

## Task 17: Final Integration Testing

**Files:**
- Create: `tests/integration/test_end_to_end.py`

- [ ] **Step 1: Write end-to-end integration test**

```python
# tests/integration/test_end_to_end.py
import pytest
import asyncio
import httpx
from sdk.ai_sre_observability import setup_observability, track_llm_call, get_client

@pytest.mark.asyncio
async def test_end_to_end_flow():
    """Test complete flow: SDK -> Service -> Metrics"""
    
    # Setup SDK pointing to deployed service
    setup_observability(
        service_name="test-integration",
        observability_url="http://ai-sre-observability.default.svc.cluster.local:8080"
    )
    
    client = get_client()
    
    # Track an LLM call
    with client.track_llm_call(provider="openai", model="gpt-4o") as tracker:
        tracker.record_tokens(prompt_tokens=100, completion_tokens=50)
    
    # Wait for batch to be sent
    await asyncio.sleep(6)
    
    # Verify metrics appear in service
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            "http://ai-sre-observability.default.svc.cluster.local:8080/metrics"
        )
        assert response.status_code == 200
        metrics_text = response.text
        
        # Check that our metric appears
        assert "llm_requests_total" in metrics_text
        assert "test-integration" in metrics_text
        assert "openai" in metrics_text
        assert "gpt-4o" in metrics_text
    
    # Verify service tracked us
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            "http://ai-sre-observability.default.svc.cluster.local:8080/services"
        )
        assert response.status_code == 200
        data = response.json()
        
        service_names = [s["name"] for s in data["services"]]
        assert "test-integration" in service_names
    
    # Cleanup
    await client.stop()

@pytest.mark.asyncio
async def test_decorator_integration():
    """Test @track_llm_call decorator integration"""
    
    setup_observability(
        service_name="test-decorator",
        observability_url="http://ai-sre-observability.default.svc.cluster.local:8080"
    )
    
    @track_llm_call(provider="openai", model="gpt-4o")
    async def mock_llm_call():
        # Simulate LLM response
        class MockResponse:
            class Usage:
                prompt_tokens = 150
                completion_tokens = 80
            usage = Usage()
        return MockResponse()
    
    result = await mock_llm_call()
    assert result.usage.prompt_tokens == 150
    
    # Wait for batch
    await asyncio.sleep(6)
    
    # Verify metrics
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            "http://ai-sre-observability.default.svc.cluster.local:8080/metrics"
        )
        assert "test-decorator" in response.text
    
    client = get_client()
    await client.stop()
```

- [ ] **Step 2: Run integration tests (requires deployed service)**

```bash
pytest tests/integration/test_end_to_end.py -v
```

Expected: PASS (both tests) - requires service deployed to GKE

- [ ] **Step 3: Commit integration tests**

```bash
git add tests/integration/
git commit -m "test: add end-to-end integration tests"
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass

- [ ] **Step 5: Final commit and tag**

```bash
git tag -a v0.1.0 -m "Release v0.1.0: AI SRE Observability Platform MVP"
git push origin main --tags
```

---

## Plan Review Checklist

### Spec Coverage

- [x] **Observability Service** - FastAPI with /ingest, /metrics, /health, /services endpoints
- [x] **Cost Calculator** - LLM cost calculation from token counts
- [x] **Prometheus Metrics** - All metric types (HTTP, LLM, business, health)
- [x] **SDK Library** - Client, decorators, transport, batching
- [x] **Trace ID** - UUID generation for request correlation
- [x] **Kubernetes Deployment** - ConfigMap, Deployment, Service manifests
- [x] **Grafana Dashboards** - Service overview, LLM cost, request tracing
- [x] **Docker** - Multi-stage Dockerfile
- [x] **Tests** - Unit tests for all components
- [x] **Integration Tests** - End-to-end flow testing
- [x] **Documentation** - README, deployment guide, dashboard docs

### No Placeholders

- [x] All code blocks contain actual implementation
- [x] All test cases have complete assertions
- [x] All commands have expected outputs
- [x] All file paths are exact
- [x] No "TBD", "TODO", or "implement later"

### Type Consistency

- [x] MetricIngestRequest/Response models consistent across service and SDK
- [x] LLMCallData structure matches between models.py files
- [x] Function signatures match between declarations and usage
- [x] Prometheus metric names consistent across metrics.py and dashboards

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-18-ai-sre-observability.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**

