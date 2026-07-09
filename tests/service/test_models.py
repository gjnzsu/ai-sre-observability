from service.models import MetricIngestRequest

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
    assert request.data.consumer == "unknown"
    assert request.data.application == "unknown"
    assert request.data.prompt_tokens == 150
    assert request.data.completion_tokens == 80


def test_metric_ingest_request_accepts_llm_ownership_labels():
    data = {
        "service_name": "ai-gateway-service",
        "metric_type": "llm_call",
        "trace_id": "abc-456",
        "timestamp": "2026-04-18T10:30:00Z",
        "data": {
            "provider": "openai",
            "model": "gpt-4o",
            "consumer": "ai-market-studio",
            "application": "ai-market-studio",
            "project": "fx-market-insight",
            "team": "markets",
            "use_case": "fx-data-query",
            "feature": "query-result-generation",
            "prompt_tokens": 150,
            "completion_tokens": 80,
            "duration_seconds": 1.2,
            "status": "success",
        },
    }

    request = MetricIngestRequest(**data)

    assert request.service_name == "ai-gateway-service"
    assert request.data.consumer == "ai-market-studio"
    assert request.data.application == "ai-market-studio"
    assert request.data.project == "fx-market-insight"
    assert request.data.team == "markets"
    assert request.data.use_case == "fx-data-query"
    assert request.data.feature == "query-result-generation"
