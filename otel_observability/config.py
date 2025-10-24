"""Unified Observability System for OpenTelemetry.

Implements logging, metrics, and tracing with best practices.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from threading import Lock

from opentelemetry.sdk.resources import Resource


class ExporterType(Enum):
    """Enum for exporter types."""

    CONSOLE = "console"
    OTLP = "otlp"
    HTTP = "http"


@dataclass
class ObservabilityConfig:
    """Configuration for observability components."""

    app_name: str
    component: str
    otlp_endpoint: str | None = None
    otel_http_url: str | None = None
    http_logs_url: str | None = None
    http_traces_url: str | None = None
    http_metrics_url: str | None = None
    insecure: bool = True
    log_level: int = logging.INFO
    metric_export_interval_ms: int = 60000
    enable_console_debug: bool = False

    def __post_init__(self) -> None:
        """Build HTTP URLs from base URL if not explicitly provided."""
        if self.otel_http_url:
            if not self.http_logs_url:
                self.http_logs_url = f"{self.otel_http_url}/v1/logs"
            if not self.http_traces_url:
                self.http_traces_url = f"{self.otel_http_url}/v1/traces"
            if not self.http_metrics_url:
                self.http_metrics_url = f"{self.otel_http_url}/v1/metrics"

    @classmethod
    def from_env(cls, **kwargs) -> ObservabilityConfig:  # noqa: ANN003
        """Create configuration from environment variables."""
        app_name = kwargs.get("app_name") or os.getenv(
            "OTEL_APP_NAME", "unknown-service",
        )
        component = kwargs.get("component") or os.getenv(
            "OTEL_COMPONENT_NAME", "unknown-component",
        )
        otlp_endpoint = kwargs.get("otlp_endpoint") or os.getenv("OTEL_GRPC_URL")
        otel_http_url = kwargs.get("otel_http_url") or os.getenv("OTEL_HTTP_URL")

        # Build URLs from base HTTP URL if provided
        http_logs_url = None
        http_traces_url = None
        http_metrics_url = None
        if otel_http_url:
            http_logs_url = f"{otel_http_url}/v1/logs"
            http_traces_url = f"{otel_http_url}/v1/traces"
            http_metrics_url = f"{otel_http_url}/v1/metrics"

        # Override with specific URLs if provided
        http_logs_url = os.getenv("OTEL_HTTP_LOGS_URL", http_logs_url)
        http_traces_url = os.getenv("OTEL_HTTP_TRACES_URL", http_traces_url)
        http_metrics_url = os.getenv("OTEL_HTTP_METRICS_URL", http_metrics_url)

        # Parse log level from environment using standard logging levels
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = kwargs.get("log_level") or getattr(logging, log_level_str, logging.INFO)

        true_string = "true"
        insecure = kwargs.get("insecure") or os.getenv(
            "OTEL_INSECURE", true_string,
        ).lower() == true_string
        metric_export_interval_ms = kwargs.get("metric_export_interval_ms") or int(
            os.getenv("OTEL_METRIC_EXPORT_INTERVAL_MS", "60000"),
        )
        enable_console_debug = kwargs.get("enable_console_debug") or os.getenv(
            "ENABLE_CONSOLE_DEBUG", "false",
        ).lower() == true_string

        return cls(
            app_name=app_name,
            component=component,
            otlp_endpoint=otlp_endpoint,
            otel_http_url=otel_http_url,
            http_logs_url=http_logs_url,
            http_traces_url=http_traces_url,
            http_metrics_url=http_metrics_url,
            insecure=insecure,
            log_level=log_level,
            metric_export_interval_ms=metric_export_interval_ms,
            enable_console_debug=enable_console_debug,
        )

    def create_resource(self) -> Resource:
        """Create an OpenTelemetry Resource with service identification."""
        return Resource.create(
            {
                "service.name": self.app_name,
                "service.component": self.component,
                "service.version": "1.0.0",  # Could be made configurable
            },
        )

    @property
    def exporter_type(self) -> ExporterType:
        """Determine the exporter type based on configuration."""
        if self.otlp_endpoint:
            return ExporterType.OTLP
        if self.http_logs_url or self.http_traces_url or self.http_metrics_url:
            return ExporterType.HTTP
        return ExporterType.CONSOLE


class ComponentInitializer(ABC):
    """Abstract base class for component initializers."""

    def __init__(self, config: ObservabilityConfig) -> None:
        """Initialize the component initializer with configuration."""
        self.config = config
        self._initialized = False
        self._lock = Lock()

    @abstractmethod
    def _setup_provider(self) -> None:
        """Set up the provider for the component."""

    def initialize(self) -> None:
        """Thread-safe initialization."""
        if self._initialized:
            return

        with self._lock:
            if not self._initialized:
                self._setup_provider()
                self._initialized = True
