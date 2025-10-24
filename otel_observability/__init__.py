"""OTEL Observability Package.

A unified OpenTelemetry observability package for Python applications that provides
easy-to-use logging, metrics, and tracing with best practices.

Example usage:
    >>> from otel_observability import initialize_observability, get_logger
    >>> manager = initialize_observability()
    >>> logger = get_logger(__name__)
    >>> logger.info("Application started")
"""

from otel_observability.config import (
    ExporterType,
    ObservabilityConfig,
)
from otel_observability.observability_manager import (
    ObservabilityDecorators,
    ObservabilityManager,
    get_logger,
    get_metrics,
    get_traces,
    initialize_observability,
)

__version__ = "0.1.4"
__author__ = "Mortada Touzi"
__email__ = "mortada.touzi@gmail.com"

__all__ = [
    # Configuration
    "ExporterType",
    "ObservabilityConfig",

    # Decorators
    "ObservabilityDecorators",

    # Main manager and functions
    "ObservabilityManager",
    "get_logger",
    "get_metrics",
    "get_traces",
    "initialize_observability",
]
