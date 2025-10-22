"""
Tests for the observability component initializers.
"""

import logging
from unittest.mock import Mock, patch

from otel_observability.config import ObservabilityConfig
from otel_observability.logs.logging import LoggingInitializer
from otel_observability.metrics.metrics import MetricsInitializer
from otel_observability.traces.traces import TracingInitializer


class TestLoggingInitializer:
    """Test cases for LoggingInitializer."""

    def setup_method(self):
        """Setup test fixtures."""
        self.config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            log_level=logging.DEBUG,
        )

    @patch("otel_observability.logs.logging.set_logger_provider")
    @patch("otel_observability.logs.logging.LoggerProvider")
    @patch("otel_observability.logs.logging.BatchLogRecordProcessor")
    @patch("otel_observability.logs.logging.LoggingHandler")
    def test_console_exporter_setup(self, mock_handler, mock_processor, mock_provider, mock_set_provider):
        """Test logging setup with console exporter."""
        # Mock the provider instance
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        initializer = LoggingInitializer(self.config)
        initializer._setup_provider()

        # Verify provider was created and set
        mock_provider.assert_called_once()
        mock_set_provider.assert_called_once_with(mock_provider_instance)

        # Verify console exporter was used (default when no endpoints)
        mock_processor.assert_called_once()

    @patch("otel_observability.logs.logging.set_logger_provider")
    @patch("otel_observability.logs.logging.LoggerProvider")
    @patch("otel_observability.logs.logging.GrpcOTLPLogExporter")
    @patch("otel_observability.logs.logging.BatchLogRecordProcessor")
    def test_otlp_exporter_setup(self, mock_processor, mock_exporter, mock_provider, mock_set_provider):
        """Test logging setup with OTLP exporter."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            otlp_endpoint="localhost:4317",
            insecure=True,
        )

        # Mock the provider instance
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        initializer = LoggingInitializer(config)
        initializer._setup_provider()

        # Verify OTLP exporter was used
        mock_exporter.assert_called_once_with(
            endpoint="localhost:4317",
            insecure=True,
        )

    @patch("otel_observability.logs.logging.set_logger_provider")
    @patch("otel_observability.logs.logging.LoggerProvider")
    @patch("otel_observability.logs.logging.HttpOTLPLogExporter")
    @patch("otel_observability.logs.logging.BatchLogRecordProcessor")
    def test_http_exporter_setup(self, mock_processor, mock_exporter, mock_provider, mock_set_provider):
        """Test logging setup with HTTP exporter."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            http_logs_url="http://localhost:4318/v1/logs",
        )

        # Mock the provider instance
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        initializer = LoggingInitializer(config)
        initializer._setup_provider()

        # Verify HTTP exporter was used
        mock_exporter.assert_called_once_with(
            endpoint="http://localhost:4318/v1/logs",
        )

    def test_initializer_thread_safety(self):
        """Test thread-safe initialization."""
        initializer = LoggingInitializer(self.config)

        # First call should initialize
        with patch.object(initializer, "_setup_provider") as mock_setup:
            initializer.initialize()
            mock_setup.assert_called_once()

        # Second call should not re-initialize
        with patch.object(initializer, "_setup_provider") as mock_setup:
            initializer.initialize()
            mock_setup.assert_not_called()


class TestMetricsInitializer:
    """Test cases for MetricsInitializer."""

    def setup_method(self):
        """Setup test fixtures."""
        self.config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
        )

    @patch("otel_observability.metrics.metrics.metrics.set_meter_provider")
    @patch("otel_observability.metrics.metrics.MeterProvider")
    @patch("otel_observability.metrics.metrics.PeriodicExportingMetricReader")
    @patch("otel_observability.metrics.metrics.ConsoleMetricExporter")
    def test_console_exporter_setup(self, mock_exporter, mock_reader, mock_provider, mock_set_provider):
        """Test metrics setup with console exporter."""
        # Mock the provider instance
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        # Mock existing meter provider to return None (not set)
        with patch("otel_observability.metrics.metrics.metrics.get_meter_provider", return_value=None):
            initializer = MetricsInitializer(self.config)
            initializer._setup_provider()

        # Verify console exporter was used
        mock_exporter.assert_called_once()
        mock_reader.assert_called_once()
        mock_provider.assert_called_once()
        mock_set_provider.assert_called_once_with(mock_provider_instance)

    @patch("otel_observability.metrics.metrics.metrics.set_meter_provider")
    @patch("otel_observability.metrics.metrics.MeterProvider")
    @patch("otel_observability.metrics.metrics.PeriodicExportingMetricReader")
    @patch("otel_observability.metrics.metrics.GrpcOTLPMetricExporter")
    def test_otlp_exporter_setup(self, mock_exporter, mock_reader, mock_provider, mock_set_provider):
        """Test metrics setup with OTLP exporter."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            otlp_endpoint="localhost:4317",
            insecure=True,
            metric_export_interval_ms=30000,
        )

        # Mock the provider instance
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        # Mock existing meter provider to return None (not set)
        with patch("otel_observability.metrics.metrics.metrics.get_meter_provider", return_value=None):
            initializer = MetricsInitializer(config)
            initializer._setup_provider()

        # Verify OTLP exporter was used with correct parameters
        mock_exporter.assert_called_once_with(
            endpoint="localhost:4317",
            insecure=True,
        )
        mock_reader.assert_called_once()

        # Verify export interval was used
        call_args = mock_reader.call_args
        assert call_args[1]["export_interval_millis"] == 30000

    def test_initializer_skips_if_provider_already_set(self):
        """Test that initializer skips if provider is already set."""
        mock_provider = Mock()

        with patch("otel_observability.metrics.metrics.metrics.get_meter_provider", return_value=mock_provider):
            with patch("otel_observability.metrics.metrics.MeterProvider") as mock_new_provider:
                initializer = MetricsInitializer(self.config)
                initializer._setup_provider()

                # Should not create new provider
                mock_new_provider.assert_not_called()


class TestTracingInitializer:
    """Test cases for TracingInitializer."""

    def setup_method(self):
        """Setup test fixtures."""
        self.config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
        )

    @patch("otel_observability.traces.traces.trace.set_tracer_provider")
    @patch("otel_observability.traces.traces.TracerProvider")
    @patch("otel_observability.traces.traces.BatchSpanProcessor")
    @patch("otel_observability.traces.traces.ConsoleSpanExporter")
    def test_console_exporter_setup(self, mock_exporter, mock_processor, mock_provider, mock_set_provider):
        """Test tracing setup with console exporter."""
        # Mock the provider instance
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        # Mock existing tracer provider to return None (not set)
        with patch("otel_observability.traces.traces.trace.get_tracer_provider", return_value=None):
            initializer = TracingInitializer(self.config)
            initializer._setup_provider()

        # Verify console exporter was used
        mock_exporter.assert_called_once()
        mock_processor.assert_called_once()
        mock_provider.assert_called_once()
        mock_set_provider.assert_called_once_with(mock_provider_instance)

    @patch("otel_observability.traces.traces.trace.set_tracer_provider")
    @patch("otel_observability.traces.traces.TracerProvider")
    @patch("otel_observability.traces.traces.BatchSpanProcessor")
    @patch("otel_observability.traces.traces.GrpcOTLPSpanExporter")
    def test_otlp_exporter_setup(self, mock_exporter, mock_processor, mock_provider, mock_set_provider):
        """Test tracing setup with OTLP exporter."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            otlp_endpoint="localhost:4317",
            insecure=True,
        )

        # Mock the provider instance
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        # Mock existing tracer provider to return None (not set)
        with patch("otel_observability.traces.traces.trace.get_tracer_provider", return_value=None):
            initializer = TracingInitializer(config)
            initializer._setup_provider()

        # Verify OTLP exporter was used
        mock_exporter.assert_called_once_with(
            endpoint="localhost:4317",
            insecure=True,
        )

    @patch("otel_observability.traces.traces.trace.set_tracer_provider")
    @patch("otel_observability.traces.traces.TracerProvider")
    @patch("otel_observability.traces.traces.BatchSpanProcessor")
    @patch("otel_observability.traces.traces.HttpOTLPSpanExporter")
    def test_http_exporter_setup(self, mock_exporter, mock_processor, mock_provider, mock_set_provider):
        """Test tracing setup with HTTP exporter."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            http_traces_url="http://localhost:4318/v1/traces",
        )

        # Mock the provider instance
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        # Mock existing tracer provider to return None (not set)
        with patch("otel_observability.traces.traces.trace.get_tracer_provider", return_value=None):
            initializer = TracingInitializer(config)
            initializer._setup_provider()

        # Verify HTTP exporter was used
        mock_exporter.assert_called_once_with(
            endpoint="http://localhost:4318/v1/traces",
        )

    def test_initializer_skips_if_provider_already_set(self):
        """Test that initializer skips if provider is already set."""
        mock_provider = Mock()

        with patch("otel_observability.traces.traces.trace.get_tracer_provider", return_value=mock_provider):
            with patch("otel_observability.traces.traces.TracerProvider") as mock_new_provider:
                initializer = TracingInitializer(self.config)
                initializer._setup_provider()

                # Should not create new provider
                mock_new_provider.assert_not_called()


class TestComponentIntegration:
    """Integration tests for component initializers."""

    def test_all_components_can_be_initialized(self):
        """Test that all components can be initialized together."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            log_level=logging.INFO,
        )

        # These should not raise exceptions
        logging_initializer = LoggingInitializer(config)
        metrics_initializer = MetricsInitializer(config)
        tracing_initializer = TracingInitializer(config)

        assert logging_initializer.config == config
        assert metrics_initializer.config == config
        assert tracing_initializer.config == config

        # Test thread-safe initialization
        logging_initializer.initialize()
        metrics_initializer.initialize()
        tracing_initializer.initialize()
