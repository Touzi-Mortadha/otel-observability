"""Unified Observability System for OpenTelemetry.

Implements logging, metrics, and tracing with best practices.
"""

from __future__ import annotations

import logging
from threading import Lock
from typing import TYPE_CHECKING, Self

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider

from otel_observability.config import ExporterType, ObservabilityConfig
from otel_observability.logs.logging import LoggingInitializer
from otel_observability.metrics.metrics import MetricsInitializer
from otel_observability.traces.traces import TracingInitializer

if TYPE_CHECKING:
    from collections.abc import Callable


class ObservabilityManager:
    """Singleton manager for all observability components.

    Provides unified access to logging, metrics, and tracing.
    """

    _instance: ObservabilityManager | None = None
    _lock = Lock()

    def __new__(cls, config: ObservabilityConfig | None = None) -> Self:
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # Initialize the instance if config is provided
                    if config is not None:
                        cls._instance._initialize(config)  # noqa: SLF001
        return cls._instance

    def __init__(self, config: ObservabilityConfig = None) -> None:
        """Initialize the observability manager."""
        # Prevent re-initialization
        if hasattr(self, "_initialized"):
            return

        # Use provided config or create from environment
        if config is None:
            config = ObservabilityConfig.from_env()

        self._initialize(config)

    def _initialize(self, config: ObservabilityConfig) -> None:
        """Initialize internal state with configuration."""
        self.config = config
        self._logging_init = LoggingInitializer(self.config)
        self._metrics_init = MetricsInitializer(self.config)
        self._tracing_init = TracingInitializer(self.config)

        # Cache for created loggers, meters, and tracers
        self._loggers: dict[str, logging.Logger] = {}
        self._meters: dict[str, metrics.Meter] = {}
        self._tracers: dict[str, trace.Tracer] = {}

        self._initialized = True

    def initialize_all(self) -> None:
        """Initialize all observability components at once."""
        self._logging_init.initialize()
        self._metrics_init.initialize()
        self._tracing_init.initialize()

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance with the specified name.

        Args:
            name: The name of the logger (typically __name__)

        Returns:
            A configured logger instance

        """
        if name not in self._loggers:
            self._logging_init.initialize()
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]

    def get_meter(self, name: str, version: str = "1.0.0") -> metrics.Meter:
        """Get a meter instance for creating metrics.

        Args:
            name: The name of the meter
            version: The version of the instrumentation

        Returns:
            A configured meter instance

        """
        cache_key = f"{name}:{version}"
        if cache_key not in self._meters:
            self._metrics_init.initialize()
            self._meters[cache_key] = metrics.get_meter(name, version)
        return self._meters[cache_key]

    def get_tracer(self, name: str, version: str = "1.0.0") -> trace.Tracer:
        """Get a tracer instance for creating spans.

        Args:
            name: The name of the tracer
            version: The version of the instrumentation

        Returns:
            A configured tracer instance

        """
        cache_key = f"{name}:{version}"
        if cache_key not in self._tracers:
            self._tracing_init.initialize()
            self._tracers[cache_key] = trace.get_tracer(name, version)
        return self._tracers[cache_key]

    def create_counter(
        self,
        meter_name: str,
        counter_name: str,
        unit: str = "1",
        description: str = "",
    ) -> metrics.Counter:
        """Create a counter metric.

        Args:
            meter_name: Name of the meter
            counter_name: Name of the counter
            unit: Unit of measurement
            description: Description of the counter

        Returns:
            A counter instance

        """
        meter = self.get_meter(meter_name)
        return meter.create_counter(
            name=counter_name,
            unit=unit,
            description=description,
        )

    def create_histogram(
        self,
        meter_name: str,
        histogram_name: str,
        unit: str = "1",
        description: str = "",
    ) -> metrics.Histogram:
        """Create a histogram metric.

        Args:
            meter_name: Name of the meter
            histogram_name: Name of the histogram
            unit: Unit of measurement
            description: Description of the histogram

        Returns:
            A histogram instance

        """
        meter = self.get_meter(meter_name)
        return meter.create_histogram(
            name=histogram_name,
            unit=unit,
            description=description,
        )

    @property
    def is_otlp_enabled(self) -> bool:
        """Check if OTLP exporting is enabled."""
        return (self.config.exporter_type == ExporterType.OTLP and
                self.config.otlp_endpoint is not None)

    def shutdown(self) -> None:
        """Gracefully shutdown all providers."""
        # Shutdown tracing
        tracer_provider = trace.get_tracer_provider()
        if isinstance(tracer_provider, TracerProvider):
            tracer_provider.shutdown()

        # Shutdown metrics
        meter_provider = metrics.get_meter_provider()
        if isinstance(meter_provider, MeterProvider):
            meter_provider.shutdown()

        # Clear caches
        self._loggers.clear()
        self._meters.clear()
        self._tracers.clear()


# Convenience functions for easy access
_manager_instance: ObservabilityManager | None = None


def _get_manager() -> ObservabilityManager:
    """Get the singleton manager instance (lazy initialization)."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ObservabilityManager()
    return _manager_instance


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: The name of the logger (typically __name__)

    Returns:
        A configured logger instance

    """
    return _get_manager().get_logger(name)


def get_metrics(name: str, version: str = "1.0.0") -> metrics.Meter:
    """Get a meter instance for creating metrics.

    Args:
        name: The name of the meter
        version: The version of the instrumentation

    Returns:
        A configured meter instance

    """
    return _get_manager().get_meter(name, version)


def get_traces(name: str, version: str = "1.0.0") -> trace.Tracer:
    """Get a tracer instance for creating spans.

    Args:
        name: The name of the tracer
        version: The version of the instrumentation

    Returns:
        A configured tracer instance

    """
    return _get_manager().get_tracer(name, version)


def initialize_observability() -> ObservabilityManager:
    """Initialize all observability components and return the manager.

    Returns:
        The ObservabilityManager instance

    """
    manager = _get_manager()
    manager.initialize_all()
    return manager


# Example usage and utilities
class ObservabilityDecorators:
    """Utility decorators for observability."""

    @staticmethod
    def trace_method(name: str | None = None) -> Callable:
        """Automatically trace method execution."""

        def decorator(func: Callable) -> Callable:
            tracer = get_traces(func.__module__)
            span_name = name or f"{func.__module__}.{func.__name__}"

            def wrapper(*args: object, **kwargs: object) -> object:
                with tracer.start_as_current_span(span_name) as span:
                    try:
                        result = func(*args, **kwargs)
                    except Exception as e:
                        span.set_status(
                            trace.Status(trace.StatusCode.ERROR, str(e)),
                        )
                        span.record_exception(e)
                        raise

                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result

            return wrapper

        return decorator

    @staticmethod
    def log_execution(logger_name: str | None = None) -> Callable:
        """Log method execution."""

        def decorator(func: Callable) -> Callable:
            logger = get_logger(logger_name or func.__module__)

            def wrapper(*args: object, **kwargs: object) -> object:
                logger.debug("Executing %s", func.__name__)
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    logger.exception("Error in %s", func.__name__)
                    raise

                logger.debug("Successfully executed %s", func.__name__)
                return result

            return wrapper

        return decorator
