# AI SRE Observability Platform

A centralized observability platform for monitoring and analyzing AI service performance, providing real-time metrics aggregation and visualization.

## Overview

This platform enables comprehensive monitoring of AI services through:
- Centralized metrics collection and aggregation
- Prometheus-compatible metrics exposure
- Real-time performance tracking
- Grafana-based visualization dashboards

**Production Status:** ✅ **Deployed and operational** - Currently monitoring AI Market Studio in production on GKE

## Live Deployment

| Component | URL | Status |
|-----------|-----|--------|
| **Observability Service** | `http://ai-sre-observability.default.svc.cluster.local:8080` (internal) | ✓ Running |
| **Prometheus** | http://136.113.33.154:9090 | ✓ Running |
| **Grafana** | http://136.114.77.0 | ✓ Running |

**Monitored Services:**
- **ai-market-studio** - FX market data platform (6 metrics tracked, ~$0.0072 per query)

**Metrics Collected:**
- `llm_requests_total` - Total LLM API requests by service, model, provider, status
- `llm_tokens_total` - Token usage (prompt, completion, total) by service, model, provider
- `llm_cost_usd_total` - Cumulative cost in USD by service, model, provider
- `llm_request_duration_seconds` - Request latency histogram

**Deployment Date:** 2026-04-23
**GKE Cluster:** helloworld-cluster (us-central1)
**GCP Project:** gen-lang-client-0896070179

## Architecture

![AI SRE Observability Platform Architecture](docs/architecture/ai-sre-observability-architecture.png)

*[View/Edit Diagram](docs/architecture/ai-sre-observability-architecture.drawio)*

The platform consists of five main layers:
1. **Client Layer** - Services instrumented with the SDK
2. **SDK Layer** - `@track_llm_call` decorator, batching client, async transport
3. **Service Layer** - FastAPI service with cost calculator, metrics registry, config loader
4. **Monitoring Layer** - Prometheus metrics exposure and Grafana dashboards
5. **Infrastructure** - Kubernetes/GKE deployment

## Components

### Observability Service
FastAPI-based service that:
- Aggregates metrics from multiple AI services
- Exposes Prometheus-compatible `/metrics` endpoint
- Provides health check and status endpoints
- Handles metric validation and storage
- Calculates LLM costs based on token usage

### SDK Library
Lightweight Python SDK for instrumenting AI services:
- Simple `@track_llm_call` decorator for automatic tracking
- Async batching client (5s interval)
- Minimal dependencies (httpx, pydantic)
- Type-safe metric definitions
- Graceful degradation on failures

### Grafana Dashboards
Pre-configured dashboards for:
- **Service Overview** - Health, HTTP metrics, error rates
- **LLM Cost & Usage** - Cost tracking by provider/model, token usage
- **Request Tracing** - Latency heatmaps, trace search, success rates

## Quick Start

For detailed architecture and design specifications, refer to `docs/superpowers/specs/2026-04-18-ai-sre-observability-design.md`.

## Development

### Install Dependencies

Service dependencies:
```bash
cd service
pip install -r requirements.txt
```

SDK dependencies:
```bash
cd sdk
pip install -r requirements.txt
```

### Run Tests

```bash
pytest tests/
```

## Tech Stack

- FastAPI - Web framework
- Prometheus Client - Metrics exposition
- Pydantic - Data validation
- httpx - HTTP client
- pytest - Testing framework
- Docker - Containerization
- Kubernetes - Orchestration
