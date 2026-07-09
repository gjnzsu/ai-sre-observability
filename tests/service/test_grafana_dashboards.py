import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _target_exprs(dashboard: dict) -> list[str]:
    exprs = []
    for panel in dashboard.get("panels", []):
        for target in panel.get("targets", []):
            expr = target.get("expr")
            if expr:
                exprs.append(expr)
    return exprs


def _provisioned_dashboard(name: str) -> dict:
    path = ROOT / "k8s" / "grafana" / "grafana-dashboard.yaml"
    docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    dashboards = next(doc for doc in docs if doc["metadata"]["name"] == "grafana-dashboards")

    return json.loads(dashboards["data"][name])


def test_ai_market_studio_cost_attribution_dashboard_json():
    path = ROOT / "grafana" / "ai-market-studio-cost-attribution.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    dashboard = payload["dashboard"]

    assert dashboard["uid"] == "ai-market-studio-cost-attribution"
    assert dashboard["title"] == "AI Market Studio - Cost Attribution"
    assert len(dashboard["panels"]) >= 10

    exprs = "\n".join(_target_exprs(dashboard))
    assert "llm_token_cost_usd_total" in exprs
    assert "llm_tokens_total" in exprs
    assert 'service="ai-gateway-service", consumer="ai-market-studio"' in exprs
    assert 'service=~"ai-market-studio|ai-gateway-service"' not in exprs
    assert "business_metric_total" in exprs
    assert 'metric_name="ai_cost_attribution_requests_total"' in exprs
    assert "by (use_case)" in exprs
    assert "by (feature, model)" in exprs
    assert "by (service, consumer, model)" in exprs


def test_ai_market_studio_cost_attribution_dashboard_is_provisioned():
    dashboard = _provisioned_dashboard("ai-market-studio-cost-attribution.json")

    assert dashboard["uid"] == "ai-market-studio-cost-attribution"
    assert dashboard["title"] == "AI Market Studio - Cost Attribution"

    exprs = "\n".join(_target_exprs(dashboard))
    assert "business_metric_total" in exprs
    assert "llm_token_cost_usd_total" in exprs
    assert 'service="ai-gateway-service", consumer="ai-market-studio"' in exprs
    assert 'service=~"ai-market-studio|ai-gateway-service"' not in exprs


def test_llm_cost_usage_dashboard_uses_current_cost_metric_name():
    path = ROOT / "grafana" / "llm-cost-usage.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    exprs = "\n".join(_target_exprs(payload["dashboard"]))

    assert "llm_token_cost_usd_total" in exprs
    assert "llm_cost_usd_total" not in exprs


def test_provisioned_service_overview_uses_count_for_top_request_stat():
    dashboard = _provisioned_dashboard("service-overview.json")
    panels = {panel["title"]: panel for panel in dashboard["panels"]}

    assert "Total LLM Requests (Last Hour)" in panels
    exprs = "\n".join(_target_exprs(dashboard))
    assert "sum(increase(llm_requests_total[1h])) or vector(0)" in exprs
    assert "LLM Request Rate" not in panels


def test_provisioned_llm_cost_usage_aggregates_attribution_labels():
    dashboard = _provisioned_dashboard("llm-cost-usage.json")
    target_exprs = _target_exprs(dashboard)
    exprs = "\n".join(target_exprs)

    assert "sum(rate(llm_token_cost_usd_total[5m])) by (provider, model)" in exprs
    assert "sum(rate(llm_tokens_total[5m])) by (provider, model, token_type)" in exprs
    assert 'llm_tokens_total{token_type="total"}[1h]' in exprs
    assert 'llm_tokens_total{token_type="total"}[24h]' in exprs
    assert "rate(llm_token_cost_usd_total[5m])" not in target_exprs
    assert "rate(llm_tokens_total[5m])" not in target_exprs


def test_provisioned_request_tracing_uses_count_for_top_request_stat():
    dashboard = _provisioned_dashboard("request-tracing.json")
    panels = {panel["title"]: panel for panel in dashboard["panels"]}

    assert "Total Requests (Last Hour)" in panels
    assert "Request Rate" not in panels
    exprs = "\n".join(_target_exprs(dashboard))
    assert "sum(increase(llm_requests_total[1h])) or vector(0)" in exprs
    assert "sum(rate(llm_requests_total[5m])) by (status, service, provider, model)" in exprs
