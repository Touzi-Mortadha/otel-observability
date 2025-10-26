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

    def test_trace_propagator_decorator(self):
        """Test trace_propagator decorator basic functionality."""
        from unittest.mock import Mock, patch

        @ObservabilityDecorators.trace_propagator()
        def test_function(*args, **kwargs):
            return "test_result"

        # The decorator should wrap the function and preserve metadata
        assert callable(test_function)
        # functools.wraps preserves the original function name
        assert test_function.__name__ == "test_function"

    def test_trace_propagator_with_trace_context(self):
        """Test trace_propagator with trace context in arguments."""
        from unittest.mock import Mock, patch
        from opentelemetry.trace import SpanContext, SpanKind, TraceFlags
        from opentelemetry.trace import NonRecordingSpan
        import opentelemetry.context as context

        # Create a mock trace context
        trace_id = 0x6e0c63257de34c926f9efcd03927272e
        span_id = 0x34ebf0c2f0f4732a
        trace_flags = TraceFlags(0x01)

        # Mock the traceparent header format
        traceparent = f"00-{trace_id:032x}-{span_id:016x}-{trace_flags:02x}"

        with patch('otel_observability.observability_manager.get_traces') as mock_get_traces:
            mock_tracer = Mock()
            mock_span = Mock()
            mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
            mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
            mock_get_traces.return_value = mock_tracer

            @ObservabilityDecorators.trace_propagator()
            def test_function(carrier, other_arg):
                return f"result: {other_arg}"

            # Test with trace context in arguments
            result = test_function({"traceparent": traceparent}, "test_value")

            # Verify the function was called and returned correct result
            assert result == "result: test_value"
            
            # Verify tracer was obtained
            mock_get_traces.assert_called_once()
            
            # Verify span was created
            mock_tracer.start_as_current_span.assert_called_once_with("test_function")

    def test_trace_propagator_without_trace_context(self):
        """Test trace_propagator when no trace context is provided."""
        from unittest.mock import Mock, patch

        with patch('otel_observability.observability_manager.get_traces') as mock_get_traces:
            mock_tracer = Mock()
            mock_span = Mock()
            mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
            mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
            mock_get_traces.return_value = mock_tracer

            @ObservabilityDecorators.trace_propagator()
            def test_function(arg1, arg2):
                return arg1 + arg2

            # Test without trace context
            result = test_function(1, 2)

            # Verify the function was called and returned correct result
            assert result == 3
            
            # Verify tracer was obtained
            mock_get_traces.assert_called_once()
            
            # Verify span was created (even without trace context)
            mock_tracer.start_as_current_span.assert_called_once_with("test_function")

    def test_trace_propagator_with_exception(self):
        """Test trace_propagator when the decorated function raises an exception."""
        from unittest.mock import Mock, patch

        with patch('otel_observability.observability_manager.get_traces') as mock_get_traces:
            mock_tracer = Mock()
            mock_span = Mock()
            mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
            mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
            mock_get_traces.return_value = mock_tracer

            @ObservabilityDecorators.trace_propagator()
            def test_function():
                raise ValueError("Test error")

            # Test that exception is propagated
            try:
                test_function()
                assert False, "Expected exception was not raised"
            except ValueError as e:
                assert str(e) == "Test error"

            # Verify span was still created despite the exception
            mock_tracer.start_as_current_span.assert_called_once_with("test_function")

    def test_trace_propagator_carrier_extraction(self):
        """Test that trace_propagator correctly extracts carrier from different argument positions."""
        from unittest.mock import Mock, patch

        traceparent = "00-6e0c63257de34c926f9efcd03927272e-34ebf0c2f0f4732a-01"

        with patch('otel_observability.observability_manager.get_traces') as mock_get_traces:
            mock_tracer = Mock()
            mock_span = Mock()
            mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
            mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
            mock_get_traces.return_value = mock_tracer

            @ObservabilityDecorators.trace_propagator()
            def test_function(arg1, arg2, arg3):
                # Filter out carrier dictionaries from the output
                args_list = []
                for arg in [arg1, arg2, arg3]:
                    if isinstance(arg, dict) and "traceparent" in arg:
                        args_list.append("carrier")
                    else:
                        args_list.append(str(arg))
                return "-".join(args_list)

            # Test with carrier as first argument
            result1 = test_function({"traceparent": traceparent}, "b", "c")
            assert result1 == "carrier-b-c"

            # Test with carrier as second argument
            result2 = test_function("a", {"traceparent": traceparent}, "c")
            assert result2 == "a-carrier-c"

            # Test with carrier as third argument
            result3 = test_function("a", "b", {"traceparent": traceparent})
            assert result3 == "a-b-carrier"

            # Verify span was created for each call
            assert mock_tracer.start_as_current_span.call_count == 3

    def test_trace_propagator_preserves_function_metadata(self):
        """Test that trace_propagator preserves function metadata using functools.wraps."""

        def original_function(x, y=10):
            """This is a test function."""
            return x + y

        decorated_function = ObservabilityDecorators.trace_propagator()(original_function)

        # Verify metadata is preserved - functools.wraps preserves the original function name
        assert decorated_function.__name__ == "original_function"
        assert decorated_function.__doc__ == "This is a test function."

    def test_trace_propagator_with_kwargs(self):
        """Test trace_propagator with keyword arguments."""
        from unittest.mock import Mock, patch

        traceparent = "00-6e0c63257de34c926f9efcd03927272e-34ebf0c2f0f4732a-01"

        with patch('otel_observability.observability_manager.get_traces') as mock_get_traces:
            mock_tracer = Mock()
            mock_span = Mock()
            mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
            mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
            mock_get_traces.return_value = mock_tracer

            @ObservabilityDecorators.trace_propagator()
            def test_function(a, b, carrier=None):
                return a + b

            # Test with carrier in kwargs
            result = test_function(1, 2, carrier={"traceparent": traceparent})
            assert result == 3

            # Verify span was created
            mock_tracer.start_as_current_span.assert_called_once_with("test_function")
