# OTEL Observability Package
[![Pytest](https://github.com/Touzi-Mortadha/otel-observability/actions/workflows/pytest.yml/badge.svg)](https://github.com/Touzi-Mortadha/otel-observability/actions/workflows/pytest.yml)
[![Pylint](https://github.com/Touzi-Mortadha/otel-observability/actions/workflows/pylint.yml/badge.svg)](https://github.com/Touzi-Mortadha/otel-observability/actions/workflows/pylint.yml)
[![Upload Python Package](https://github.com/Touzi-Mortadha/otel-observability/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Touzi-Mortadha/otel-observability/actions/workflows/python-publish.yml)

A unified OpenTelemetry observability package for Python applications that provides easy-to-use logging, metrics, and tracing with best practices.

## Features

- **Unified Configuration**: Configure all observability components through environment variables or programmatic configuration
- **Multiple Exporters**: Support for OTLP (gRPC), HTTP, and Console exporters
- **Thread-Safe**: Singleton pattern ensures thread-safe initialization
- **Easy Integration**: Simple API for logging, metrics, and tracing
- **Decorators**: Built-in decorators for automatic tracing and logging

## Installation

### From PyPI

```bash
pip install otel-observability
```

### From Source

```bash
git clone https://github.com/Touzi-Mortadha/otel-observability.git
cd otel-observability
pip install -e .
```

## Quick Start

### Basic Usage with Environment Variables

```python
from otel_observability import initialize_observability, get_logger, get_metrics, get_traces

# Initialize observability (reads from environment variables)
manager = initialize_observability()

# Get a logger
logger = get_logger(__name__)
logger.info("Application started")

# Get a meter for metrics
meter = get_metrics("my_app")
request_counter = meter.create_counter("requests_total", description="Total requests")
request_counter.add(1, {"endpoint": "/api"})

# Get a tracer for distributed tracing
tracer = get_traces("my_app")
with tracer.start_as_current_span("process_request") as span:
    span.set_attribute("user.id", "123")
    logger.info("Processing request")
```

### Programmatic Configuration

```python
from otel_observability import ObservabilityManager, ObservabilityConfig

# Create custom configuration
config = ObservabilityConfig(
    app_name="my-app",
    component="test-component",
    otlp_endpoint="localhost:4317",  # OTLP gRPC endpoint
    log_level=LogLevel.INFO,
    insecure=True,
)

# Initialize with custom config
manager = ObservabilityManager(config)
manager.initialize_all()

# Use the manager directly
logger = manager.get_logger(__name__)
meter = manager.get_meter("my_app")
tracer = manager.get_tracer("my_app")
```

### Using Decorators

```python
from otel_observability import ObservabilityDecorators

@ObservabilityDecorators.trace_method()
@ObservabilityDecorators.log_execution()
def process_data(data):
    """Process data with automatic tracing and logging."""
    logger.info(f"Processing data: {data}")
    return {"processed": True, **data}

result = process_data({"input": "test"})
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_APP_NAME` | App name for resource attributes | `unknown-service` |
| `OTEL_COMPONENT_NAME` | service name for resource attributes | `unknown-component` |
| `OTEL_GRPC_URL` | OTLP gRPC endpoint URL | None |
| `OTEL_HTTP_URL` | Base HTTP URL for OTLP HTTP exporters | None |
| `OTEL_HTTP_LOGS_URL` | Specific HTTP URL for logs | `{OTEL_HTTP_URL}/v1/logs` |
| `OTEL_HTTP_TRACES_URL` | Specific HTTP URL for traces | `{OTEL_HTTP_URL}/v1/traces` |
| `OTEL_HTTP_METRICS_URL` | Specific HTTP URL for metrics | `{OTEL_HTTP_URL}/v1/metrics` |
| `OTEL_INSECURE` | Use insecure connection for gRPC | `true` |
| `LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` |
| `OTEL_METRIC_EXPORT_INTERVAL_MS` | Metrics export interval in milliseconds | `60000` |
| `ENABLE_CONSOLE_DEBUG` | Enable console output for debugging | `false` |

### Programmatic Configuration

Create an `ObservabilityConfig` instance with the following parameters:

- `app_name`: Your app name (required)
- `component`: Your service name (required)
- `otlp_endpoint`: OTLP gRPC endpoint URL
- `http_logs_url`: HTTP endpoint for logs
- `http_traces_url`: HTTP endpoint for traces  
- `http_metrics_url`: HTTP endpoint for metrics
- `insecure`: Use insecure connection (default: True)
- `log_level`: Log level (default: LogLevel.INFO)
- `metric_export_interval_ms`: Metrics export interval (default: 60000)
- `enable_console_debug`: Enable console debugging (default: False)

## API Reference

### Core Functions

- `initialize_observability()`: Initialize all components and return manager
- `get_logger(name)`: Get a configured logger instance
- `get_metrics(name, version)`: Get a meter for creating metrics
- `get_traces(name, version)`: Get a tracer for creating spans

### ObservabilityManager

The main manager class providing:

- `get_logger(name)`: Get logger by name
- `get_meter(name, version)`: Get meter by name and version
- `get_tracer(name, version)`: Get tracer by name and version
- `create_counter()`: Create a counter metric
- `create_histogram()`: Create a histogram metric
- `shutdown()`: Gracefully shutdown all providers

### ObservabilityDecorators

- `@trace_method()`: Automatically trace method execution
- `@log_execution()`: Automatically log method execution

## Examples

### Flask Application

```python
from flask import Flask
from otel_observability import initialize_observability, get_logger, ObservabilityDecorators

app = Flask(__name__)
manager = initialize_observability()
logger = get_logger(__name__)

@app.route('/')
@ObservabilityDecorators.trace_method()
def hello():
    logger.info("Hello endpoint called")
    return "Hello World!"

if __name__ == '__main__':
    app.run()
```

### FastAPI Application

```python
from fastapi import FastAPI
from otel_observability import initialize_observability, get_logger, get_traces

app = FastAPI()
manager = initialize_observability()
logger = get_logger(__name__)
tracer = get_traces("fastapi_app")

@app.get("/")
async def read_root():
    with tracer.start_as_current_span("read_root"):
        logger.info("Root endpoint called")
        return {"Hello": "World"}
