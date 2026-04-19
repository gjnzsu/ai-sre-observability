# Grafana Dashboards

This directory contains Grafana dashboard configurations for monitoring the AI SRE Observability Platform.

## Available Dashboards

### Service Overview (`service-overview.json`)

Comprehensive dashboard for monitoring service health and performance metrics.

**Panels:**
1. **Service Health** - Gauge showing service up/down status
2. **HTTP Request Rate** - Request throughput over time (requests/sec)
3. **Active Services** - Count of currently running services
4. **HTTP Request Duration (p95)** - 95th percentile response times
5. **HTTP Requests In-Flight** - Current concurrent requests
6. **Error Rate (5xx)** - Server error rate with alerting

**Metrics Used:**
- `service_up` - Service health status
- `http_requests_total` - Total HTTP requests counter
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_flight` - Current in-flight requests gauge

## Setup Instructions

### 1. Configure Prometheus Data Source

Before importing dashboards, configure Prometheus as a data source in Grafana:

1. Navigate to **Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Configure the connection:
   - **Name:** `Prometheus`
   - **URL:** `http://prometheus-service:9090` (for in-cluster) or `http://localhost:9090` (for local)
5. Click **Save & Test**

### 2. Import Dashboard

**Option A: Via Grafana UI**

1. Navigate to **Dashboards** → **Import**
2. Click **Upload JSON file**
3. Select `service-overview.json`
4. Select the Prometheus data source
5. Click **Import**

**Option B: Via API**

```bash
# Set Grafana credentials
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin"

# Import dashboard
curl -X POST \
  -H "Content-Type: application/json" \
  -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  -d @service-overview.json \
  "${GRAFANA_URL}/api/dashboards/db"
```

**Option C: Via ConfigMap (Kubernetes)**

```bash
# Create ConfigMap with dashboard
kubectl create configmap grafana-dashboard-service-overview \
  --from-file=service-overview.json \
  -n monitoring

# Label for Grafana sidecar auto-discovery
kubectl label configmap grafana-dashboard-service-overview \
  grafana_dashboard=1 \
  -n monitoring
```

### 3. Verify Dashboard

1. Navigate to **Dashboards** → **Browse**
2. Find "AI SRE Observability - Service Overview"
3. Verify all panels are displaying data
4. Adjust time range if needed (default: last 1 hour)

## Dashboard Configuration

### Time Range
- Default: Last 1 hour
- Auto-refresh: 30 seconds
- Configurable refresh intervals: 5s, 10s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 1d

### Alerting

The Error Rate panel includes a pre-configured alert:
- **Condition:** Error rate > 0.1 requests/sec
- **Evaluation:** Every 1 minute
- **State:** Alerting on execution errors

To enable notifications:
1. Configure notification channels in Grafana
2. Edit the dashboard panel
3. Add notification channels to the alert

## Customization

### Adding Variables

To filter by service or environment, add template variables:

1. Dashboard Settings → **Variables** → **Add variable**
2. Configure variable:
   - **Name:** `service`
   - **Type:** Query
   - **Data source:** Prometheus
   - **Query:** `label_values(service_up, service_name)`
3. Update panel queries to use `$service` variable

### Modifying Queries

Edit panel queries to match your metric labels:
- Replace `service_name` with your service label
- Adjust `status_code` regex patterns
- Modify time ranges in `rate()` functions

## Troubleshooting

### No Data Displayed

1. Verify Prometheus is scraping metrics:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

2. Check metric availability:
   ```bash
   curl http://localhost:9090/api/v1/query?query=service_up
   ```

3. Verify service is exposing metrics:
   ```bash
   kubectl port-forward svc/ai-sre-service 8000:8000
   curl http://localhost:8000/metrics
   ```

### Dashboard Not Loading

1. Check Grafana logs:
   ```bash
   kubectl logs -n monitoring deployment/grafana
   ```

2. Verify data source connection in Grafana UI

3. Validate JSON syntax:
   ```bash
   python -m json.tool service-overview.json
   ```

## Next Steps

- Configure alerting rules in Prometheus
- Set up notification channels (Slack, PagerDuty, email)
- Create additional dashboards for LLM-specific metrics
- Add SLO/SLI tracking panels
