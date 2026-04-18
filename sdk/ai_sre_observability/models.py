"""SDK data models for AI SRE Observability Platform."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LLMCallMetric(BaseModel):
    """Model for LLM call metrics."""

    provider: str = Field(..., description="LLM provider (e.g., 'openai', 'anthropic')")
    model: str = Field(..., description="Model name (e.g., 'gpt-4', 'claude-3')")
    prompt_tokens: int = Field(..., ge=0, description="Number of prompt tokens")
    completion_tokens: int = Field(..., ge=0, description="Number of completion tokens")
    duration_seconds: float = Field(..., ge=0, description="Call duration in seconds")
    status: str = Field(..., description="Call status (e.g., 'success', 'error')")
    error_type: Optional[str] = Field(None, description="Error type if status is 'error'")


class MetricPayload(BaseModel):
    """Payload for sending metrics to the observability platform."""

    service_name: str = Field(..., description="Name of the service sending the metric")
    metric_type: str = Field(..., description="Type of metric (e.g., 'llm_call')")
    trace_id: str = Field(..., description="Trace ID for correlation")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metric timestamp")
    data: Dict[str, Any] = Field(..., description="Metric data")
