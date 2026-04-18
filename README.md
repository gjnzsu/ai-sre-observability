# AI SRE Observability Platform

A centralized observability platform for monitoring and analyzing AI service performance, providing real-time metrics aggregation and visualization.

## Overview

This platform enables comprehensive monitoring of AI services through:
- Centralized metrics collection and aggregation
- Prometheus-compatible metrics exposure
- Real-time performance tracking
- Grafana-based visualization dashboards

## Components

### Observability Service
FastAPI-based service that:
- Aggregates metrics from multiple AI services
- Exposes Prometheus-compatible `/metrics` endpoint
- Provides health check and status endpoints
- Handles metric validation and storage

### SDK Library
Lightweight Python SDK for instrumenting AI services:
- Simple API for sending metrics
- Minimal dependencies
- Async support with httpx
- Type-safe metric definitions

### Grafana Dashboards
Pre-configured dashboards for:
- AI service performance metrics
- Request latency and throughput
- Error rates and success rates
- Custom business metrics

## Quick Start

For detailed architecture and design specifications, refer to the project design documentation.

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
