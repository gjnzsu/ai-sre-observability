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
    api_url="http://localhost:8000",
    service_name="my-ai-service"
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
    api_url: str,
    service_name: str,
    timeout: float = 30.0
)
```

**Parameters:**
- `api_url`: Backend API endpoint
- `service_name`: Name of your service
- `timeout`: Request timeout in seconds (default: 30.0)

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
    api_url="http://localhost:8000",
    service_name="my-service"
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
