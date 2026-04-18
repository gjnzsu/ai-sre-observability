from pydantic import BaseModel, Field
from datetime import datetime
from typing import Union, Optional, Dict


class LLMCallData(BaseModel):
    """LLM call metric data"""
    provider: str = Field(..., description="LLM provider (e.g., openai, anthropic)")
    model: str = Field(..., description="Model name (e.g., gpt-4o, claude-3-opus)")
    prompt_tokens: int = Field(..., ge=0, description="Number of prompt tokens")
    completion_tokens: int = Field(..., ge=0, description="Number of completion tokens")
    duration_seconds: float = Field(..., ge=0, description="Duration of the call in seconds")
    status: str = Field(..., description="Status of the call (success, error)")
    error_type: Optional[str] = Field(None, description="Type of error if status is error")


class HTTPRequestData(BaseModel):
    """HTTP request metrics"""
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    status_code: int = Field(..., ge=100, le=599, description="HTTP status code")
    duration_seconds: float = Field(..., ge=0, description="Request duration in seconds")


class BusinessMetricData(BaseModel):
    """Business metrics"""
    metric_name: str = Field(..., description="Name of the business metric")
    value: float = Field(..., description="Metric value")
    labels: Dict[str, str] = Field(default_factory=dict, description="Additional labels for the metric")


class MetricIngestRequest(BaseModel):
    """Request model for /ingest endpoint"""
    service_name: str = Field(..., description="Name of the service sending the metric")
    metric_type: str = Field(..., description="Type of metric (llm_call, http_request, business_metric)")
    trace_id: str = Field(..., description="Trace ID for correlation")
    timestamp: datetime = Field(..., description="Timestamp of the metric")
    data: Union[LLMCallData, HTTPRequestData, BusinessMetricData] = Field(..., description="Metric data")


class MetricIngestResponse(BaseModel):
    """Response model for /ingest endpoint"""
    status: str = Field(..., description="Status of the ingestion (success, error)")
    trace_id: str = Field(..., description="Trace ID for correlation")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Health status (healthy, unhealthy)")
    services_tracked: list[str] = Field(default_factory=list, description="List of service names being tracked")
    metrics_received_last_minute: int = Field(..., ge=0, description="Number of metrics received in the last minute")


class ServiceInfo(BaseModel):
    """Service information"""
    name: str = Field(..., description="Service name")
    last_seen: datetime = Field(..., description="Last time a metric was received from this service")
    metrics_count: int = Field(..., ge=0, description="Total number of metrics received from this service")


class ServicesResponse(BaseModel):
    """Services list response"""
    services: list[ServiceInfo] = Field(default_factory=list, description="List of tracked services")
