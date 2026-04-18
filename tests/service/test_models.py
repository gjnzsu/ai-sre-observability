import pytest
from datetime import datetime
from service.models import MetricIngestRequest, LLMCallData

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
    assert request.data.prompt_tokens == 150
    assert request.data.completion_tokens == 80
