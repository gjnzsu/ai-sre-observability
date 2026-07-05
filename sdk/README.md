# AI SRE Observability SDK

Python SDK for tracking LLM calls and system metrics in AI-powered SRE applications.

## Installation

```bash
pip install ai-sre-observability-sdk
```

For development:
```bash
cd sdk
pip install -e .
```

## Quick Start

```python
from ai_sre_observability import setup_observability, track_llm_call

# Initialize the SDK
setup_observability(
    service_name="my-ai-service",
    observability_url="http://localhost:8000"
)

# Track LLM calls with decorator
@track_llm_call(model="gpt-4o")
async def analyze_logs(prompt: str):
    # Your LLM call logic here
    response = await llm_client.chat(prompt)
    return response

# Use the function
result = await analyze_logs("Analyze these error logs...")
```

## Features

- Automatic LLM call tracking with decorators
- Token usage and cost calculation
- Latency monitoring
- Error tracking and retry logic
- Async and sync support
- Built-in pricing for OpenAI and DeepSeek models

## API Reference

### setup_observability

Initialize the observability client.

```python
setup_observability(
    service_name: str,
    observability_url: str,
    batch_interval: float = 5.0,
    timeout: float = 5.0,
    api_key: str | None = None
)
```

**Parameters:**
- `service_name`: Name of your service
- `observability_url`: Backend API endpoint
- `batch_interval`: Batch flush interval in seconds (default: 5.0)
- `timeout`: Request timeout in seconds (default: 5.0)
- `api_key`: Optional API key for authenticated ingestion. If omitted, the SDK reads `OBSERVABILITY_API_KEY`.

### Authentication

API key authentication is opt-in on the observability service. Existing clients keep working when the service does not set `OBSERVABILITY_API_KEYS`.

When authentication is enabled, configure clients with either an environment variable:

```bash
export OBSERVABILITY_API_KEY="your-api-key"
```

Or pass it explicitly:

```python
setup_observability(
    service_name="my-ai-service",
    observability_url="http://ai-sre-observability.default.svc.cluster.local:8080",
    api_key="your-api-key"
)
```

### @track_llm_call

Decorator for tracking LLM function calls.

```python
@track_llm_call(
    model: str,
    operation: str = "chat"
)
```

**Parameters:**
- `model`: LLM model name (e.g., "gpt-4o", "deepseek-chat")
- `operation`: Operation type (default: "chat")

**Returns:**
The decorated function will automatically track:
- Input tokens and cost
- Output tokens and cost
- Total cost
- Latency
- Success/failure status

### ObservabilityClient

Low-level client for manual tracking.

```python
from ai_sre_observability import ObservabilityClient

client = ObservabilityClient(
    service_name="my-service",
    observability_url="http://localhost:8000"
)

# Track LLM call manually
await client.track_llm_call(
    model="gpt-4o",
    operation="chat",
    input_tokens=100,
    output_tokens=50,
    latency_ms=1500,
    success=True
)
```

## Supported Models

### OpenAI
- gpt-4o
- gpt-4o-mini

### DeepSeek
- deepseek-chat

## License

MIT
