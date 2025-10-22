"""
Tests for the observability manager module.
"""

import logging

from otel_observability import (
    ObservabilityConfig,
    ObservabilityDecorators,
    ObservabilityManager,
    get_logger,
    get_metrics,
    get_traces,
    initialize_observability,
)


class TestObservabilityManager:
    """Test cases for ObservabilityManager class."""

    def setup_method(self):
        """Reset the singleton instance before each test."""
        ObservabilityManager._instance = None

    def test_singleton_pattern(self):
        """Test that ObservabilityManager follows singleton pattern."""
        manager1 = ObservabilityManager()
        manager2 = ObservabilityManager()

        assert manager1 is manager2
        assert id(manager1) == id(manager2)

    def test_initialization_with_config(self):
        """Test initialization with custom configuration."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            log_level=logging.DEBUG,
        )

        manager = ObservabilityManager(config)

        assert manager.config.app_name == "test-service"
        assert manager.config.log_level == logging.DEBUG
        assert hasattr(manager, "_initialized")
        assert manager._initialized is True

    def test_initialization_without_config(self):
        """Test initialization without configuration (uses environment)."""
        manager = ObservabilityManager()

        assert hasattr(manager, "config")
        assert hasattr(manager, "_initialized")
        assert manager._initialized is True

    def test_get_logger(self):
        """Test getting logger instances."""
        config = ObservabilityConfig(app_name="test-service", component="test-component",)
        manager = ObservabilityManager(config)

        logger1 = manager.get_logger("test.module1")
        logger2 = manager.get_logger("test.module2")

        assert logger1.name == "test.module1"
        assert logger2.name == "test.module2"
        assert logger1 is not logger2

        # Test caching
        logger1_cached = manager.get_logger("test.module1")
        assert logger1 is logger1_cached

    def test_get_meter(self):
        """Test getting meter instances."""
        config = ObservabilityConfig(app_name="test-service", component="test-component")
        manager = ObservabilityManager(config)

        meter1 = manager.get_meter("test_meter")
        meter2 = manager.get_meter("test_meter", "2.0.0")

        # Test caching
        meter1_cached = manager.get_meter("test_meter")
        assert meter1 is meter1_cached

        # Different versions should be different instances
        meter_different_version = manager.get_meter("test_meter", "3.0.0")
        assert meter1 is not meter_different_version

    def test_get_tracer(self):
        """Test getting tracer instances."""
        config = ObservabilityConfig(app_name="test-service", component="test-component")
        manager = ObservabilityManager(config)

        tracer1 = manager.get_tracer("test_tracer")
        tracer2 = manager.get_tracer("test_tracer", "2.0.0")

        # Test caching
        tracer1_cached = manager.get_tracer("test_tracer")
        assert tracer1 is tracer1_cached

        # Different versions should be different instances
        tracer_different_version = manager.get_tracer("test_tracer", "3.0.0")
        assert tracer1 is not tracer_different_version

    def test_create_counter(self):
        """Test creating counter metrics."""
        config = ObservabilityConfig(app_name="test-service", component="test-component")
        manager = ObservabilityManager(config)

        counter = manager.create_counter(
            meter_name="test_meter",
            counter_name="test_counter",
            unit="1",
            description="Test counter",
        )

        assert counter is not None

    def test_create_histogram(self):
        """Test creating histogram metrics."""
        config = ObservabilityConfig(app_name="test-service", component="test-component")
        manager = ObservabilityManager(config)

        histogram = manager.create_histogram(
            meter_name="test_meter",
            histogram_name="test_histogram",
            unit="ms",
            description="Test histogram",
        )

        assert histogram is not None

    def test_is_otlp_enabled(self):
        """Test OTLP enabled detection."""
        # Reset singleton for clean test
        ObservabilityManager._instance = None

        # Test with OTLP endpoint
        config_otlp = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            otlp_endpoint="localhost:4317",
        )
        manager_otlp = ObservabilityManager(config_otlp)
        assert manager_otlp.is_otlp_enabled is True

        # Reset singleton again
        ObservabilityManager._instance = None

        # Test without OTLP endpoint
        config_no_otlp = ObservabilityConfig(app_name="test-service", component="test-component")
        manager_no_otlp = ObservabilityManager(config_no_otlp)
        assert manager_no_otlp.is_otlp_enabled is False

    def test_shutdown(self):
        """Test shutdown method."""
        config = ObservabilityConfig(app_name="test-service", component="test-component")
        manager = ObservabilityManager(config)

        # Populate caches
        manager.get_logger("test.module")
        manager.get_meter("test_meter")
        manager.get_tracer("test_tracer")

        # Verify caches are populated
        assert len(manager._loggers) > 0
        assert len(manager._meters) > 0
        assert len(manager._tracers) > 0

        # Call shutdown
        manager.shutdown()

        # Verify caches are cleared
        assert len(manager._loggers) == 0
        assert len(manager._meters) == 0
        assert len(manager._tracers) == 0


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    def setup_method(self):
        """Reset the singleton instance before each test."""
        ObservabilityManager._instance = None

    def test_initialize_observability(self):
        """Test initialize_observability function."""
        manager = initialize_observability()

        assert isinstance(manager, ObservabilityManager)
        assert manager._initialized is True

    def test_get_logger_function(self):
        """Test get_logger convenience function."""
        config = ObservabilityConfig(app_name="test-service", component="test-component")
        ObservabilityManager(config)

        logger = get_logger("test.module")
        assert logger.name == "test.module"

    def test_get_metrics_function(self):
        """Test get_metrics convenience function."""
        config = ObservabilityConfig(app_name="test-service", component="test-component")
        ObservabilityManager(config)

        meter = get_metrics("test_meter")
        assert meter is not None

    def test_get_traces_function(self):
        """Test get_traces convenience function."""
        config = ObservabilityConfig(app_name="test-service", component="test-component")
        ObservabilityManager(config)

        tracer = get_traces("test_tracer")
        assert tracer is not None


class TestObservabilityDecorators:
    """Test cases for observability decorators."""

    def test_trace_method_decorator(self):
        """Test trace_method decorator."""

        @ObservabilityDecorators.trace_method()
        def test_function():
            return "test_result"

        # The decorator should wrap the function
        assert callable(test_function)
        assert test_function.__name__ == "wrapper"

    def test_trace_method_decorator_with_name(self):
        """Test trace_method decorator with custom name."""

        @ObservabilityDecorators.trace_method(name="custom_span")
        def test_function():
            return "test_result"

        assert callable(test_function)

    def test_log_execution_decorator(self):
        """Test log_execution decorator."""

        @ObservabilityDecorators.log_execution()
        def test_function():
            return "test_result"

        # The decorator should wrap the function
        assert callable(test_function)
        assert test_function.__name__ == "wrapper"

    def test_log_execution_decorator_with_logger_name(self):
        """Test log_execution decorator with custom logger name."""

        @ObservabilityDecorators.log_execution(logger_name="custom_logger")
        def test_function():
            return "test_result"

        assert callable(test_function)

    def test_combined_decorators(self):
        """Test using both decorators together."""

        @ObservabilityDecorators.trace_method()
        @ObservabilityDecorators.log_execution()
        def test_function():
            return "test_result"

        assert callable(test_function)
