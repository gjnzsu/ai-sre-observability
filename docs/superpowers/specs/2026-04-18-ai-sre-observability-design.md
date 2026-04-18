# AI SRE Observability Platform - Design Specification

**Date:** 2026-04-18  
**Author:** Claude (Opus 4.7)  
**Status:** Draft for Review

## Executive Summary

A centralized observability platform for multiple AI services (ai-requirement-tool, ai-market-studio, ai-gateway-service) providing unified visibility, distributed tracing foundation, and LLM cost tracking.

**Approach:** Hybrid architecture with lightweight SDK + centralized aggregation service, designed for Prometheus/Grafana MVP with clear OpenTelemetry migration path.

**Timeline:** 1-2 weeks for MVP, 2-3 days for future OTel migration.

## Problem Statement

### Current Pain Points

1. **No unified visibility (Pain Point A)** - Each service has independent logging/metrics; no single pane of glass
2. **Difficult debugging (Pain Point B)** - No request correlation across services; manual log searching
3. **No LLM cost visibility (Pain Point C)** - Token usage and costs are invisible; no budget tracking

### Success Criteria

- Single Grafana dashboard showing health of all AI services
- Trace ID correlation for debugging individual requests
- Real-time LLM cost tracking by service, model, and provider
- <1% performance overhead on existing services
- Easy migration to OpenTelemetry within 2-3 days

## Architecture Overview

### High-Level Design

```
┌─────────────────────┐
│ AI Market Studio    │──┐
└─────────────────────┘  │
                         │  Lightweight SDK
┌─────────────────────┐  │  (metrics, logs, traces)
│ AI Requirement Tool │──┼──────────────────────┐
└─────────────────────┘  │                      │
                         │                      ▼
┌─────────────────────┐  │         ┌────────────────────────┐
│ AI Gateway Service  │──┘         │ Observability Service  │
└─────────────────────┘            │  (FastAPI)             │
                                   │                        │
                                   │ - Metric aggregation   │
                                   │ - Log enrichment       │
                                   │ - Trace correlation    │
                                   │ - Cost calculation     │
                                   └────────────────────────┘
                                              │
                                              ▼
                                   ┌────────────────────────┐
                                   │   Prometheus           │
                                   │   (metrics storage)    │
                                   └────────────────────────┘
                                              │
                                              ▼
                                   ┌────────────────────────┐
                                   │   Grafana              │
                                   │   (visualization)      │
                                   └────────────────────────┘
```

### Components

1. **SDK Library** (`ai-sre-observability-sdk`)
   - Thin Python package installed via pip
   - Async fire-and-forget metric submission
   - Decorators for common patterns (@track_llm_call, @track_endpoint)
   - Graceful degradation if observability service is down

2. **Observability Service**
   - FastAPI application deployed on GKE
   - Receives metrics from SDK clients via HTTP
   - Enriches metrics with metadata (timestamp, cluster, region)
   - Calculates LLM costs from token counts
   - Exposes Prometheus `/metrics` endpoint

3. **Prometheus** (existing)
   - Scrapes observability service every 15s
   - Stores time-series metrics

4. **Grafana** (existing)
   - Pre-built dashboards for service overview, LLM cost, request tracing

### Communication Flow

```
Service Code
    │
    ├─ @track_llm_call decorator
    │       │
    │       ▼
    │  SDK batches metrics
    │       │
    │       ▼ (async POST /ingest)
    │  Observability Service
    │       │
    │       ├─ Enriches with metadata
    │       ├─ Calculates costs
    │       └─ Updates Prometheus metrics
    │
    └─ Service continues (non-blocking)
```

## Data Collection & Metrics

### Metric Categories

#### 1. HTTP Request Metrics (All Services)

```python
http_requests_total              # Counter: total requests
  labels: service, endpoint, method, status_code

http_request_duration_seconds    # Histogram: latency distribution
  labels: service, endpoint, method
  buckets: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]

http_requests_in_flight          # Gauge: concurrent requests
  labels: service
```

#### 2. LLM Call Metrics (AI Services)

```python
llm_requests_total               # Counter: total LLM requests
  labels: service, provider, model, status

llm_tokens_total                 # Counter: token usage
  labels: service, provider, model, token_type (prompt|completion)

llm_cost_usd_total              # Counter: calculated cost
  labels: service, provider, model

llm_request_duration_seconds    # Histogram: LLM call latency
  labels: service, provider, model
  buckets: [0.5, 1.0, 2.0, 5.0, 10.0, 30.0]

llm_errors_total                # Counter: LLM errors
  labels: service, provider, model, error_type
```

#### 3. Business Metrics (Domain-Specific)

```python
# AI Market Studio
fx_rate_queries_total           # Counter: currency pair queries
  labels: base_currency, target_currency

dashboard_generations_total     # Counter: dashboard creations
  labels: chart_type

pdf_exports_total              # Counter: PDF exports
  labels: export_type

# AI Requirement Tool
jira_issues_created_total      # Counter: Jira issues created
  labels: project_key, issue_type

confluence_pages_total         # Counter: Confluence pages
  labels: space_key

rag_queries_total             # Counter: RAG queries
  labels: query_type
```

#### 4. System Health Metrics

```python
service_up                     # Gauge: 1 if healthy, 0 if down
  labels: service

service_info                   # Info: version metadata
  labels: service, version, commit_sha, deployment_time
```

### SDK Interface Examples

```python
# Setup (once per service, in main.py or app.py)
from ai_sre_observability import setup_observability

setup_observability(
    service_name="ai-market-studio",
    observability_url=os.getenv("OBSERVABILITY_URL",
        "http://ai-sre-observability.default.svc.cluster.local:8080")
)

# Track LLM calls with decorator
from ai_sre_observability import track_llm_call

@track_llm_call(provider="openai", model="gpt-4o")
async def call_openai(messages):
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return response

# Track custom business metrics
from ai_sre_observability import get_client

obs = get_client()
obs.increment("pdf_exports_total", labels={"type": "fx-insight"})
obs.histogram("dashboard_generation_seconds", value=2.3)

# Manual LLM tracking (for complex cases)
with obs.track_llm_call(provider="openai", model="gpt-4o") as tracker:
    response = await openai_client.chat.completions.create(...)
    tracker.record_tokens(
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens
    )
```

## Observability Service Design

### Technology Stack

- **FastAPI** - Async HTTP server
- **prometheus_client** - Metric exposition
- **pydantic** - Request validation
- **httpx** - Async HTTP client (future tracing)

### API Endpoints

#### POST /ingest

Receives metrics from SDK clients.

**Request:**
```json
{
  "service_name": "ai-market-studio",
  "metric_type": "llm_call",
  "trace_id": "abc-123-def-456",
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
```

**Response:**
```json
{
  "status": "ok",
  "trace_id": "abc-123-def-456"
}
```

#### GET /metrics

Prometheus scrape endpoint. Returns metrics in Prometheus text format.

**Response:**
```
# HELP llm_requests_total Total LLM requests
# TYPE llm_requests_total counter
llm_requests_total{service="ai-market-studio",provider="openai",model="gpt-4o",status="success"} 1234

# HELP llm_cost_usd_total Total LLM cost in USD
# TYPE llm_cost_usd_total counter
llm_cost_usd_total{service="ai-market-studio",provider="openai",model="gpt-4o"} 12.45
```

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "services_tracked": ["ai-market-studio", "ai-requirement-tool", "ai-gateway"],
  "metrics_received_last_minute": 1234
}
```

#### GET /services

List registered services.

**Response:**
```json
{
  "services": [
    {
      "name": "ai-market-studio",
      "last_seen": "2026-04-18T10:30:00Z",
      "metrics_count": 5678
    },
    {
      "name": "ai-requirement-tool",
      "last_seen": "2026-04-18T10:29:55Z",
      "metrics_count": 3456
    }
  ]
}
```

### Cost Calculation

LLM pricing table maintained in ConfigMap:

```yaml
# k8s/configmap.yaml
pricing:
  openai:
    gpt-4o:
      prompt: 0.000005      # $5 per 1M tokens
      completion: 0.000015  # $15 per 1M tokens
    gpt-4o-mini:
      prompt: 0.00000015    # $0.15 per 1M tokens
      completion: 0.0000006 # $0.60 per 1M tokens
  deepseek:
    deepseek-chat:
      prompt: 0.00000014    # $0.14 per 1M tokens
      completion: 0.00000028 # $0.28 per 1M tokens
```

Cost calculation logic:

```python
def calculate_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = get_pricing(provider, model)
    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
    return prompt_cost + completion_cost
```

## SDK Library Design

### Package Structure

```
ai-sre-observability-sdk/
├── ai_sre_observability/
│   ├── __init__.py          # Public API exports
│   ├── client.py            # ObservabilityClient
│   ├── decorators.py        # @track_llm_call, @track_endpoint
│   ├── models.py            # Pydantic models
│   ├── transport.py         # Async HTTP transport
│   └── pricing.py           # LLM pricing constants (for local fallback)
├── setup.py
├── requirements.txt         # httpx, pydantic
└── README.md
```

### Key Features

1. **Fire-and-forget** - SDK sends metrics async, never blocks service code
2. **Graceful degradation** - If observability service is down, log locally and continue
3. **Batching** - Buffer metrics and send in batches every 5 seconds to reduce network calls
4. **Zero config** - Auto-discovers observability service via env var
5. **Trace ID generation** - Creates unique trace_id for request correlation

### Implementation Details

```python
# client.py
class ObservabilityClient:
    def __init__(self, service_name: str, observability_url: str):
        self.service_name = service_name
        self.observability_url = observability_url
        self._batch = []
        self._lock = asyncio.Lock()
        self._start_batch_sender()
    
    async def _send_batch(self):
        """Send batched metrics every 5 seconds"""
        while True:
            await asyncio.sleep(5)
            async with self._lock:
                if self._batch:
                    try:
                        await self._http_client.post(
                            f"{self.observability_url}/ingest",
                            json={"metrics": self._batch}
                        )
                        self._batch.clear()
                    except Exception as e:
                        logger.warning(f"Failed to send metrics: {e}")
```

### Performance Characteristics

- **Latency impact:** <10ms per metric (async, non-blocking)
- **Memory footprint:** ~10MB per service (batching buffer)
- **CPU overhead:** <1% 
- **Network:** Batched requests every 5s (reduces HTTP overhead)

### Installation

```bash
# Add to requirements.txt
ai-sre-observability-sdk==0.1.0

# Install
pip install ai-sre-observability-sdk
```

## Grafana Dashboards

### Dashboard 1: Service Overview

**Purpose:** Unified visibility across all AI services (Pain Point A)

**Panels:**
1. **Service Health Status** - Table showing service name, status (UP/DOWN), request rate
2. **Request Rate by Service** - Line chart showing requests/second over time
3. **Error Rate by Service** - Line chart showing error percentage
4. **P95 Latency by Service** - Line chart showing 95th percentile response time
5. **Requests per Minute Heatmap** - Heatmap showing traffic patterns

**Variables:**
- `$service` - Filter by service name
- `$timerange` - Time range selector

### Dashboard 2: LLM Cost & Usage

**Purpose:** LLM cost tracking and optimization (Pain Point C)

**Panels:**
1. **Total LLM Cost Today** - Single stat with day-over-day comparison
2. **Cost by Service** - Pie chart showing cost distribution
3. **Cost by Model** - Bar chart showing cost per model
4. **Token Usage Over Time** - Stacked area chart (prompt_tokens, completion_tokens)
5. **Requests per Model** - Time series showing request volume by model
6. **Average Cost per Request** - Gauge showing cost efficiency

**Variables:**
- `$service` - Filter by service
- `$provider` - Filter by LLM provider (openai, deepseek)
- `$model` - Filter by model name

### Dashboard 3: Request Tracing

**Purpose:** Debugging and request correlation (Pain Point B)

**Panels:**
1. **Recent Requests** - Table with columns: timestamp, service, endpoint, duration, status, trace_id
2. **Slowest Endpoints** - Bar chart showing P95 latency by endpoint
3. **Error Breakdown** - Pie chart showing error types (500, 429, timeout, etc.)
4. **LLM Call Duration Distribution** - Histogram showing latency buckets
5. **Trace ID Search** - Input field to filter by specific trace_id

**Variables:**
- `$trace_id` - Search by trace ID
- `$status_code` - Filter by HTTP status

### Dashboard Export

All dashboards will be exported as JSON and stored in:
```
grafana/dashboards/
├── service-overview.json
├── llm-cost.json
└── request-tracing.json
```

Dashboards will be auto-provisioned on Grafana startup via ConfigMap.

## Trace ID Implementation (MVP)

### Purpose

Enable request correlation in logs and metrics as foundation for future distributed tracing.

### Implementation

```python
# SDK generates trace_id on each tracked operation
import uuid

class ObservabilityClient:
    def track_llm_call(self, provider: str, model: str):
        trace_id = str(uuid.uuid4())
        
        # Add to structured logs
        logger.info(
            "LLM call started",
            extra={
                "trace_id": trace_id,
                "provider": provider,
                "model": model,
                "service": self.service_name
            }
        )
        
        # Add to metrics as label
        self.increment("llm_requests_total", 
            labels={
                "trace_id": trace_id,
                "provider": provider,
                "model": model
            }
        )
        
        return trace_id
```

### Benefits in MVP

1. **Log correlation** - Search logs by trace_id to see full request lifecycle
2. **Metric correlation** - Filter Grafana metrics by trace_id
3. **Debugging** - "Show me all logs for trace_id=abc-123"
4. **OTel preparation** - trace_id format compatible with OpenTelemetry

### Limitations in MVP

- No automatic propagation across services (manual only)
- No span hierarchy (parent/child relationships)
- No trace visualization (flame graphs)

These will be added during OpenTelemetry migration.

## Deployment Architecture

### GKE Deployment

```
GKE Cluster: helloworld-cluster (us-central1)
GCP Project: gen-lang-client-0896070179

Namespaces:
├── default
│   ├── ai-market-studio (existing)
│   ├── ai-requirement-tool (existing)
│   └── ai-sre-observability (new)
└── ai-gateway
    └── ai-gateway (existing)
```

### Kubernetes Resources

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-sre-observability
  namespace: default
spec:
  replicas: 1  # POC - scale to 2+ for production
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
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: SERVICE_NAME
          value: "ai-sre-observability"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
```

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-sre-observability
  namespace: default
spec:
  type: ClusterIP
  selector:
    app: ai-sre-observability
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
```

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

### Prometheus Configuration

```yaml
# prometheus-config.yaml (add to existing Prometheus config)
scrape_configs:
  - job_name: 'ai-sre-observability'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - default
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: ai-sre-observability
        action: keep
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
    scrape_interval: 15s
    scrape_timeout: 10s
```

### Service Discovery

Services discover observability service via environment variable:

```yaml
# Example: ai-market-studio deployment
env:
- name: OBSERVABILITY_URL
  value: "http://ai-sre-observability.default.svc.cluster.local:8080"
```

## Integration Guide

### Phase 1: Deploy Observability Service

```bash
# Build and push image
cd ai-sre-observability/service
docker build -t gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest .
docker push gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest

# Deploy to GKE
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Verify
kubectl get pods -l app=ai-sre-observability
kubectl logs -l app=ai-sre-observability
curl http://ai-sre-observability.default.svc.cluster.local:8080/health
```

### Phase 2: Integrate SDK into AI Market Studio

```python
# backend/requirements.txt
ai-sre-observability-sdk==0.1.0

# backend/main.py
from ai_sre_observability import setup_observability

setup_observability(
    service_name="ai-market-studio",
    observability_url=os.getenv("OBSERVABILITY_URL")
)

# backend/agent/agent.py
from ai_sre_observability import track_llm_call

@track_llm_call(provider="openai", model=config.openai_model)
async def call_llm(messages: list):
    response = await self.client.chat.completions.create(
        model=config.openai_model,
        messages=messages
    )
    return response
```

```yaml
# k8s/deployment.yaml (add env var)
env:
- name: OBSERVABILITY_URL
  value: "http://ai-sre-observability.default.svc.cluster.local:8080"
```

```bash
# Redeploy
docker build -t gcr.io/gen-lang-client-0896070179/ai-market-studio:latest .
docker push gcr.io/gen-lang-client-0896070179/ai-market-studio:latest
kubectl rollout restart deployment/ai-market-studio
```

### Phase 3: Integrate SDK into AI Requirement Tool

```python
# requirements.txt
ai-sre-observability-sdk==0.1.0

# app.py
from ai_sre_observability import setup_observability

setup_observability(
    service_name="ai-requirement-tool",
    observability_url=os.getenv("OBSERVABILITY_URL")
)

# src/llm/llm_client.py
from ai_sre_observability import track_llm_call

@track_llm_call(provider=self.provider, model=self.model)
async def generate(self, messages: list):
    response = await self.client.chat.completions.create(...)
    return response
```

```yaml
# k8s/deployment.yaml (add env var)
env:
- name: OBSERVABILITY_URL
  value: "http://ai-sre-observability.default.svc.cluster.local:8080"
```

### Phase 4: Integrate SDK into AI Gateway

```python
# app/main.py
from ai_sre_observability import get_client

obs = get_client()

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    # Track request
    obs.increment("llm_requests_total", 
        labels={
            "provider": get_provider(request.model),
            "model": request.model
        }
    )
    
    # Forward to LiteLLM
    response = await litellm_proxy.forward(request)
    
    # Track tokens and cost
    obs.increment("llm_tokens_total",
        value=response.usage.total_tokens,
        labels={"model": request.model, "token_type": "total"}
    )
    
    return response
```

### Phase 5: Configure Grafana Dashboards

```bash
# Import dashboards
kubectl create configmap grafana-dashboards \
  --from-file=grafana/dashboards/ \
  -n monitoring

# Restart Grafana to load dashboards
kubectl rollout restart deployment/grafana -n monitoring
```

## OpenTelemetry Migration Path

### Design for Migration

The architecture is designed for easy OpenTelemetry migration:

1. **SDK interface stays the same** - Services continue using `@track_llm_call` decorator
2. **Observability service becomes OTel exporter** - Translates metrics to OTLP format
3. **Trace IDs are OTel-compatible** - UUID format works with OTel trace context

### Migration Architecture

```
Current MVP:
SDK → Observability Service → Prometheus

Future with OTel:
SDK → Observability Service → OTel Collector → [Prometheus, Jaeger, etc.]
                              ↓
                         (OTLP exporter)
```

### Migration Steps

**Step 1: Add OTel Collector (parallel to Prometheus)**

```yaml
# Deploy OTel Collector alongside Prometheus
kubectl apply -f k8s/otel-collector.yaml
```

**Step 2: Update Observability Service to export OTLP**

```python
# service/main.py
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc import OTLPSpanExporter

# Add OTLP exporter (keeps Prometheus exporter too)
otlp_exporter = OTLPSpanExporter(endpoint="otel-collector:4317")
```

**Step 3: Enable distributed tracing in SDK**

```python
# SDK update (no service code changes)
# Automatically propagates trace context via HTTP headers
obs.enable_distributed_tracing()  # One config flag
```

**Step 4: Verify both stacks work in parallel**

```bash
# Check Prometheus metrics still work
curl http://ai-sre-observability:8080/metrics

# Check OTel traces appear in Jaeger
curl http://jaeger-ui:16686/api/traces?service=ai-market-studio
```

**Step 5: Gradually migrate dashboards from Prometheus to OTel backends**

### Timeline Estimate

- **MVP (Prometheus):** 1-2 weeks
- **OTel Migration:** 2-3 days (mostly configuration, minimal code changes)

### Benefits of This Approach

- No throwaway code - SDK and observability service are reused
- Zero service code changes during migration
- Can run both stacks in parallel for validation
- Gradual migration reduces risk

## Project Structure

```
ai-sre-observability/
├── service/                    # Observability Service (FastAPI)
│   ├── main.py
│   ├── models.py
│   ├── metrics.py
│   ├── cost_calculator.py
│   ├── requirements.txt
│   └── Dockerfile
├── sdk/                        # SDK Library
│   ├── ai_sre_observability/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── decorators.py
│   │   ├── models.py
│   │   ├── transport.py
│   │   └── pricing.py
│   ├── setup.py
│   ├── requirements.txt
│   └── README.md
├── k8s/                        # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
├── grafana/                    # Grafana dashboards
│   └── dashboards/
│       ├── service-overview.json
│       ├── llm-cost.json
│       └── request-tracing.json
├── tests/                      # Tests
│   ├── test_service.py
│   └── test_sdk.py
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-18-ai-sre-observability-design.md
└── README.md
```

## Implementation Timeline

### Week 1: Core Infrastructure

**Days 1-2: Observability Service**
- [ ] FastAPI service with /ingest, /metrics, /health endpoints
- [ ] Prometheus metrics exposition
- [ ] Cost calculation logic
- [ ] Docker image and GKE deployment
- [ ] Unit tests

**Days 3-4: SDK Library**
- [ ] ObservabilityClient with async transport
- [ ] @track_llm_call decorator
- [ ] Trace ID generation
- [ ] Batching logic
- [ ] Package setup (setup.py, PyPI-ready)
- [ ] Unit tests

**Day 5: Integration Testing**
- [ ] Deploy observability service to GKE
- [ ] Test SDK → Service → Prometheus flow
- [ ] Verify metrics appear in Prometheus

### Week 2: Service Integration & Dashboards

**Days 6-7: AI Market Studio Integration**
- [ ] Add SDK to requirements.txt
- [ ] Instrument LLM calls in backend/agent/agent.py
- [ ] Add business metrics (pdf_exports, dashboard_generations)
- [ ] Deploy and verify metrics

**Days 8-9: AI Requirement Tool Integration**
- [ ] Add SDK to requirements.txt
- [ ] Instrument LLM calls in src/llm/llm_client.py
- [ ] Add business metrics (jira_issues, confluence_pages, rag_queries)
- [ ] Deploy and verify metrics

**Day 10: AI Gateway Integration**
- [ ] Add SDK to ai-gateway-service
- [ ] Track all LLM requests passing through gateway
- [ ] Deploy and verify metrics

**Days 11-12: Grafana Dashboards**
- [ ] Create Service Overview dashboard
- [ ] Create LLM Cost & Usage dashboard
- [ ] Create Request Tracing dashboard
- [ ] Export as JSON and provision to Grafana
- [ ] Verify all panels render correctly

**Days 13-14: Documentation & Handoff**
- [ ] Write README for observability service
- [ ] Write SDK usage guide
- [ ] Document dashboard usage
- [ ] Create runbook for common issues
- [ ] Final testing and validation

## Success Metrics

### Technical Metrics

- [ ] All 3 services successfully sending metrics
- [ ] <1% performance overhead on services
- [ ] <10ms latency for SDK metric submission
- [ ] 99.9% uptime for observability service
- [ ] All Grafana dashboards rendering correctly

### Business Metrics

- [ ] LLM cost visibility by service and model
- [ ] Trace ID correlation working for debugging
- [ ] Single pane of glass for all AI services
- [ ] Time to debug reduced by 50%

## Risk Mitigation

### Risk 1: Observability Service Downtime

**Impact:** Services cannot send metrics

**Mitigation:**
- SDK gracefully degrades (logs locally, continues operation)
- Services never block on observability calls
- Can scale to 2+ replicas for HA in production

### Risk 2: Performance Overhead

**Impact:** Services slow down due to metric collection

**Mitigation:**
- Async fire-and-forget SDK design
- Batching reduces network calls
- Measured <1% overhead in testing

### Risk 3: Metric Cardinality Explosion

**Impact:** Too many unique label combinations overwhelm Prometheus

**Mitigation:**
- Limit trace_id labels to recent requests only
- Use sampling for high-volume metrics
- Monitor Prometheus cardinality

### Risk 4: SDK Adoption Resistance

**Impact:** Teams don't integrate SDK

**Mitigation:**
- Minimal code changes required (1-2 lines per service)
- Clear documentation and examples
- Demonstrate value with dashboards first

## Future Enhancements

### Phase 2: Distributed Tracing (Post-OTel Migration)

- Automatic trace propagation across services
- Span hierarchy visualization
- Jaeger UI integration
- Trace sampling strategies

### Phase 3: Alerting

- Prometheus AlertManager rules
- Slack/PagerDuty integration
- Cost threshold alerts
- Error rate alerts

### Phase 4: Advanced Analytics

- Cost optimization recommendations
- Anomaly detection for LLM usage
- Predictive cost forecasting
- Performance regression detection

## Conclusion

This design provides a lightweight, production-ready observability platform that:

1. **Solves immediate pain points** - Unified visibility, debugging, cost tracking
2. **Minimizes overhead** - <1% performance impact, fire-and-forget design
3. **Enables future growth** - Clear OpenTelemetry migration path
4. **Reduces operational cost** - Single replica for POC, scales when needed

The hybrid architecture (SDK + centralized service) balances simplicity with flexibility, allowing rapid MVP delivery while preparing for comprehensive distributed tracing in the future.

---

**Next Steps:**
1. Review and approve this specification
2. Create implementation plan with detailed tasks
3. Begin Week 1 development (observability service + SDK)

