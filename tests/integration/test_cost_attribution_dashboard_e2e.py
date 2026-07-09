import json
from datetime import datetime
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from service.main import app


ROOT = Path(__file__).resolve().parents[2]


def _dashboard_exprs() -> str:
    path = ROOT / "k8s" / "grafana" / "grafana-dashboard.yaml"
    docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    dashboards = next(doc for doc in docs if doc["metadata"]["name"] == "grafana-dashboards")
    dashboard = json.loads(dashboards["data"]["ai-market-studio-cost-attribution.json"])
    exprs = []
    for panel in dashboard["panels"]:
        for target in panel.get("targets", []):
            exprs.append(target.get("expr", ""))
    return "\n".join(exprs)


def test_cost_attribution_dashboard_e2e_metrics_and_queries():
    with TestClient(app) as client:
        business_payload = {
            "service_name": "ai-market-studio",
            "metric_type": "counter",
            "trace_id": "trace-cost-attribution-1",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "metric_name": "ai_cost_attribution_requests_total",
                "value": 1,
                "labels": {
                    "application": "ai-market-studio",
                    "project": "fx-market-insight",
                    "team": "markets",
                    "use_case": "fx-advisory-report",
                    "feature": "advisory-report-generation",
                    "model": "gpt-4o",
                    "status": "success",
                    "tool_used": "generate_market_briefing",
                },
            },
        }
        gateway_llm_payload = {
            "service_name": "ai-gateway-service",
            "metric_type": "llm_call",
            "trace_id": "trace-cost-attribution-1",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "provider": "openai",
                "model": "gpt-4o",
                "consumer": "ai-market-studio",
                "application": "ai-market-studio",
                "project": "fx-market-insight",
                "team": "markets",
                "use_case": "fx-advisory-report",
                "feature": "advisory-report-generation",
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "duration_seconds": 1.0,
                "status": "success",
            },
        }

        assert client.post("/ingest", json=business_payload).status_code == 200
        assert client.post("/ingest", json=gateway_llm_payload).status_code == 200

        metrics = client.get("/metrics").text
        assert "business_metric_total" in metrics
        assert 'use_case="fx-advisory-report"' in metrics
        assert "llm_token_cost_usd_total" in metrics
        assert "llm_tokens_total" in metrics
        assert 'service="ai-gateway-service"' in metrics
        assert 'consumer="ai-market-studio"' in metrics

    exprs = _dashboard_exprs()
    assert "business_metric_total" in exprs
    assert "llm_token_cost_usd_total" in exprs
    assert "llm_tokens_total" in exprs
    assert "ai_cost_attribution_requests_total" in exprs
    assert 'service="ai-gateway-service", consumer="ai-market-studio"' in exprs
    assert 'service=~"ai-market-studio|ai-gateway-service"' not in exprs
