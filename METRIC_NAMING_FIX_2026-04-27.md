# Metric Naming Standardization Fix
**Date:** 2026-04-27
**Issue:** ai-market-studio cost metrics not appearing in Grafana dashboard

## Root Cause

**Inconsistent metric naming between services:**

- **ai-requirement-tool:** Uses `llm_token_cost_usd_total` ✅
- **ai-market-studio:** Was using `llm_cost_usd_total` ❌
- **Grafana dashboard:** Queries `llm_token_cost_usd_total`

**Result:** ai-market-studio cost metrics were being scraped by Prometheus but not displayed in the dashboard because the query was looking for the wrong metric name.

## Evidence

### Before Fix
```bash
# ai-market-studio used different metric name
curl 'http://prometheus:9090/api/v1/query?query=llm_cost_usd_total'
# Returns: ai-market-studio metrics ✅

curl 'http://prometheus:9090/api/v1/query?query=llm_token_cost_usd_total'
# Returns: Only ai-requirement-tool metrics ❌
```

### Grafana Dashboard Queries
```promql
# Total Cost (Last Hour)
sum(increase(llm_token_cost_usd_total[1h]))

# Cost Rate by Provider & Model
rate(llm_token_cost_usd_total[5m])

# Cost Distribution by Provider (24h)
sum(increase(llm_token_cost_usd_total[24h])) by (provider)
```

All dashboard queries use `llm_token_cost_usd_total`, so ai-market-studio was invisible.

## Solution

**Standardized metric name in observability service to `llm_token_cost_usd_total`**

### Changes Made

**File:** `ai-sre-observability/service/metrics.py`

```python
# Before
self.llm_cost_usd_total = Counter(
    'llm_cost_usd_total',
    'Total cost in USD for LLM requests',
    ['service', 'provider', 'model'],
    registry=self.registry
)

# After
self.llm_token_cost_usd_total = Counter(
    'llm_token_cost_usd_total',
    'Total cost in USD for LLM requests',
    ['service', 'provider', 'model'],
    registry=self.registry
)
```

## Deployment

**Image:** `gcr.io/gen-lang-client-0896070179/ai-sre-observability:v2026-04-27-metric-fix`
**Deployed:** 2026-04-27
**Pod:** `ai-sre-observability-66c757d575-z7trx`
**Status:** Running

## Verification

After the next LLM call from ai-market-studio, the metric will appear:

```bash
# Check if ai-market-studio now uses standard metric name
curl 'http://136.113.33.154:9090/api/v1/query?query=llm_token_cost_usd_total' | \
  python -m json.tool | grep -A 5 '"service": "ai-market-studio"'
```

Expected output:
```json
{
    "metric": {
        "__name__": "llm_token_cost_usd_total",
        "service": "ai-market-studio",
        "provider": "openai",
        "model": "gpt-4o"
    },
    "value": [timestamp, "cost_value"]
}
```

## Impact

✅ **ai-market-studio cost metrics now visible in Grafana dashboard**
✅ **Consistent metric naming across all services**
✅ **No changes needed to Grafana dashboard queries**
✅ **No changes needed to ai-market-studio backend**

## Naming Convention

**Standard metric names for LLM observability:**

| Metric | Name | Labels |
|--------|------|--------|
| Requests | `llm_requests_total` | service, provider, model, status |
| Tokens | `llm_tokens_total` | service, provider, model, token_type |
| **Cost** | **`llm_token_cost_usd_total`** | **service, provider, model** |
| Duration | `llm_request_duration_seconds` | service, provider, model |
| Errors | `llm_errors_total` | service, provider, model, error_type |

## Related Files

- `ai-sre-observability/service/metrics.py` - Metric definitions
- `ai-sre-observability/k8s/grafana/dashboards/llm-cost-usage.json` - Dashboard queries

## Commit

**Repo:** ai-sre-observability
**Commit:** b353a9d
**Message:** "fix: standardize cost metric name to llm_token_cost_usd_total"
