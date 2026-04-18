# AI SRE Observability Platform - Deployment Guide

## Overview

The AI SRE Observability Platform is deployed on Google Kubernetes Engine (GKE) in the `gen-lang-client-0896070179` project.

## Deployment Information

- **GCP Project**: gen-lang-client-0896070179
- **Container Registry**: gcr.io/gen-lang-client-0896070179/ai-sre-observability
- **Kubernetes Namespace**: default
- **Service Name**: ai-sre-observability
- **Service Port**: 8080

## Service Endpoints

### Internal Cluster Access

The service is accessible within the Kubernetes cluster at:

```
http://ai-sre-observability.default.svc.cluster.local:8080
```

### Available Endpoints

- **Health Check**: `GET /health`
  - Returns service health status and basic metrics
  - Example: `{"status":"ok","services_tracked":[],"metrics_received_last_minute":0}`

- **Metrics**: `GET /metrics`
  - Prometheus-compatible metrics endpoint
  - Exposes LLM usage, cost, and performance metrics

- **Ingest Metrics**: `POST /ingest`
  - Accepts LLM metrics from SDK clients
  - Content-Type: application/json

## Deployment Steps

### 1. Build and Push Docker Image

```bash
cd service
docker build -t gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest .
docker push gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest
```

### 2. Deploy Kubernetes Resources

```bash
# Apply ConfigMap (pricing configuration)
kubectl apply -f k8s/configmap.yaml

# Apply Deployment
kubectl apply -f k8s/deployment.yaml

# Apply Service
kubectl apply -f k8s/service.yaml
```

### 3. Verify Deployment

```bash
# Check pod status
kubectl get pods -l app=ai-sre-observability

# View logs
kubectl logs -l app=ai-sre-observability --tail=50

# Test health endpoint
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://ai-sre-observability.default.svc.cluster.local:8080/health

# Test metrics endpoint
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://ai-sre-observability.default.svc.cluster.local:8080/metrics
```

## Resource Configuration

### Pod Resources

- **Requests**: 256Mi memory, 200m CPU
- **Limits**: 512Mi memory, 500m CPU
- **Replicas**: 1

### Health Checks

- **Liveness Probe**: HTTP GET /health (30s initial delay, 10s period)
- **Readiness Probe**: HTTP GET /health (10s initial delay, 5s period)

## Configuration

The service uses a ConfigMap for pricing configuration (`ai-sre-observability-config`). The pricing data is mounted at `/config/pricing.yaml` and includes:

- OpenAI GPT-4o: $2.50/$10.00 per million tokens (input/output)
- OpenAI GPT-4o-mini: $0.15/$0.60 per million tokens (input/output)
- DeepSeek Chat: $0.14/$0.28 per million tokens (input/output)

## Monitoring

The service exposes Prometheus metrics at `/metrics` including:

- `llm_requests_total`: Total LLM API requests by provider, model, and service
- `llm_tokens_total`: Total tokens processed (input/output)
- `llm_cost_usd_total`: Total cost in USD
- `llm_request_duration_seconds`: Request duration histogram
- `llm_errors_total`: Total errors by provider, model, and error type
- `http_requests_total`: HTTP request counter
- `http_request_duration_seconds`: HTTP request duration
- `service_up`: Service health status

## SDK Integration

Applications can send metrics to the service using the Python SDK:

```python
from ai_sre_observability import ObservabilityClient

client = ObservabilityClient(
    service_url="http://ai-sre-observability.default.svc.cluster.local:8080"
)

# Metrics are automatically sent after LLM calls
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app=ai-sre-observability
kubectl describe pod -l app=ai-sre-observability
```

### View Logs

```bash
kubectl logs -l app=ai-sre-observability --tail=100 -f
```

### Test Connectivity

```bash
kubectl run debug --image=curlimages/curl --rm -it --restart=Never -- sh
# Inside the pod:
curl http://ai-sre-observability.default.svc.cluster.local:8080/health
```

## Updating the Deployment

To update the service:

1. Build and push a new Docker image
2. Update the deployment:
   ```bash
   kubectl rollout restart deployment/ai-sre-observability
   ```
3. Monitor the rollout:
   ```bash
   kubectl rollout status deployment/ai-sre-observability
   ```

## Deployment Status

- **Deployed**: 2026-04-19
- **Image**: gcr.io/gen-lang-client-0896070179/ai-sre-observability:latest
- **Status**: Running and healthy
