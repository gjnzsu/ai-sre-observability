# Kubernetes Manifests for AI SRE Observability Platform

This directory contains all Kubernetes manifests for deploying the complete observability stack.

## Directory Structure

```
k8s/
├── observability-service/   # AI SRE Observability Service (metrics aggregation)
├── prometheus/              # Prometheus (metrics collection & storage)
└── grafana/                 # Grafana (visualization & dashboards)
```

## Components

### 1. Observability Service (`observability-service/`)

The central metrics aggregation service that collects LLM metrics from instrumented services.

**Files:**
- `deployment.yaml` - Service deployment
- `service.yaml` - ClusterIP service (internal only)
- `configmap.yaml` - Pricing configuration

**Endpoints:**
- Internal: `http://ai-sre-observability.default.svc.cluster.local:8080`
- Metrics: `http://ai-sre-observability.default.svc.cluster.local:8080/metrics`

### 2. Prometheus (`prometheus/`)

Metrics collection and time-series database.

**Files:**
- `prometheus-deployment.yaml` - Prometheus deployment
- `prometheus-service.yaml` - LoadBalancer service (external access)
- `prometheus-config.yaml` - Scrape configuration for all monitored services

**Monitored Services:**
- ai-requirement-tool
- ai-sre-observability
- ai-market-studio
- rag-service
- ai-gateway

**Access:**
- External: http://136.113.33.154:9090
- Internal: `http://prometheus-service.default.svc.cluster.local:9090`

### 3. Grafana (`grafana/`)

Visualization platform with pre-configured dashboards.

**Files:**
- `grafana-deployment.yaml` - Grafana deployment
- `grafana-service.yaml` - LoadBalancer service (external access)
- `grafana-dashboard.yaml` - Dashboard definitions (ConfigMaps)

**Dashboards:**
1. **Service Overview** - Health, HTTP metrics, error rates
2. **LLM Cost & Usage** - Cost tracking by provider/model, token usage
3. **Request Tracing** - Latency heatmaps, trace search, success rates

**Access:**
- External: http://136.114.77.0
- Credentials: admin / newpassword123

## Deployment

### Deploy All Components

```bash
# Deploy in order (dependencies matter)
kubectl apply -f prometheus/prometheus-config.yaml
kubectl apply -f prometheus/prometheus-deployment.yaml
kubectl apply -f prometheus/prometheus-service.yaml

kubectl apply -f observability-service/configmap.yaml
kubectl apply -f observability-service/deployment.yaml
kubectl apply -f observability-service/service.yaml

kubectl apply -f grafana/grafana-dashboard.yaml
kubectl apply -f grafana/grafana-deployment.yaml
kubectl apply -f grafana/grafana-service.yaml
```

### Deploy Individual Components

```bash
# Prometheus only
kubectl apply -f prometheus/

# Grafana only
kubectl apply -f grafana/

# Observability service only
kubectl apply -f observability-service/
```

### Update Dashboards

```bash
kubectl apply -f grafana/grafana-dashboard.yaml
kubectl rollout restart deployment/grafana -n default
```

### Update Prometheus Scrape Config

```bash
kubectl apply -f prometheus/prometheus-config.yaml
kubectl rollout restart deployment/prometheus -n default
```

## Adding New Services to Monitor

1. **Instrument your service** with the AI SRE Observability SDK
2. **Add scrape config** to `prometheus/prometheus-config.yaml`:
   ```yaml
   - job_name: 'your-service-name'
     static_configs:
       - targets: ['your-service.namespace.svc.cluster.local:port']
     metrics_path: /metrics
   ```
3. **Apply changes**:
   ```bash
   kubectl apply -f prometheus/prometheus-config.yaml
   kubectl rollout restart deployment/prometheus -n default
   ```

## Monitoring the Observability Stack

### Check Component Health

```bash
# Prometheus
kubectl get pods -l app=prometheus -n default
kubectl logs -l app=prometheus -n default --tail=50

# Grafana
kubectl get pods -l app=grafana -n default
kubectl logs -l app=grafana -n default --tail=50

# Observability Service
kubectl get pods -l app=ai-sre-observability -n default
kubectl logs -l app=ai-sre-observability -n default --tail=50
```

### Verify Metrics Collection

```bash
# Check Prometheus targets
curl http://136.113.33.154:9090/api/v1/targets

# Query metrics
curl 'http://136.113.33.154:9090/api/v1/query?query=up'
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitored Services                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AI Req Tool  │  │ Market Studio│  │  RAG Service │ ...  │
│  │   /metrics   │  │   /metrics   │  │   /metrics   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          │                  ▼                  │
          │         ┌─────────────────┐         │
          │         │ Observability   │         │
          │         │    Service      │         │
          │         │   /metrics      │         │
          │         └────────┬────────┘         │
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                    ┌─────────────────┐
                    │   Prometheus    │
                    │  (scrapes all)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Grafana      │
                    │  (visualizes)   │
                    └─────────────────┘
```

## GKE Cluster Info

- **Cluster**: helloworld-cluster
- **Region**: us-central1
- **Project**: gen-lang-client-0896070179
- **Namespace**: default (observability-service, prometheus, grafana)

## Troubleshooting

### Grafana shows "No data"
1. Check Prometheus is scraping: http://136.113.33.154:9090/targets
2. Verify service endpoints are reachable from Prometheus pod
3. Check Grafana datasource configuration

### Prometheus not scraping a service
1. Verify service DNS: `kubectl exec -it prometheus-pod -- nslookup service-name`
2. Check service has `/metrics` endpoint
3. Verify network policies allow traffic

### Dashboard not updating
1. Restart Grafana: `kubectl rollout restart deployment/grafana -n default`
2. Check ConfigMap was applied: `kubectl get configmap grafana-dashboards -o yaml`
3. Verify dashboard provisioning: `kubectl logs -l app=grafana | grep provisioning`
