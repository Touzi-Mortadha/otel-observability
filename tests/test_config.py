"""
Tests for the observability configuration module.
"""

import logging
import os

from otel_observability.config import ExporterType, ObservabilityConfig


class TestObservabilityConfig:
    """Test cases for ObservabilityConfig class."""

    def test_default_config(self):
        """Test creating config with minimal parameters."""
        config = ObservabilityConfig(app_name="test-service", component="test-component")

        assert config.app_name == "test-service"
        assert config.otlp_endpoint is None
        assert config.otel_http_url is None
        assert config.insecure is True
        assert config.log_level == logging.INFO
        assert config.metric_export_interval_ms == 60000
        assert config.enable_console_debug is False

    def test_full_config(self):
        """Test creating config with all parameters."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            otlp_endpoint="localhost:4317",
            otel_http_url="http://localhost:4318",
            insecure=False,
            log_level=logging.DEBUG,
            metric_export_interval_ms=30000,
            enable_console_debug=True,
        )

        assert config.app_name == "test-service"
        assert config.otlp_endpoint == "localhost:4317"
        assert config.otel_http_url == "http://localhost:4318"
        assert config.insecure is False
        assert config.log_level == logging.DEBUG
        assert config.metric_export_interval_ms == 30000
        assert config.enable_console_debug is True

    def test_url_construction(self):
        """Test automatic URL construction from base HTTP URL."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            otel_http_url="http://otel-collector:4318",
        )

        assert config.http_logs_url == "http://otel-collector:4318/v1/logs"
        assert config.http_traces_url == "http://otel-collector:4318/v1/traces"
        assert config.http_metrics_url == "http://otel-collector:4318/v1/metrics"

    def test_explicit_urls_override_construction(self):
        """Test that explicit URLs override automatic construction."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            otel_http_url="http://otel-collector:4318",
            http_logs_url="http://custom:4318/v1/logs",
        )

        assert config.http_logs_url == "http://custom:4318/v1/logs"
        assert config.http_traces_url == "http://otel-collector:4318/v1/traces"
        assert config.http_metrics_url == "http://otel-collector:4318/v1/metrics"

    def test_exporter_type_otlp(self):
        """Test exporter type detection for OTLP."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            otlp_endpoint="localhost:4317",
        )

        assert config.exporter_type == ExporterType.OTLP

    def test_exporter_type_http(self):
        """Test exporter type detection for HTTP."""
        config = ObservabilityConfig(
            app_name="test-service",
            component="test-component",
            http_logs_url="http://localhost:4318/v1/logs",
        )

        assert config.exporter_type == ExporterType.HTTP

    def test_exporter_type_console(self):
        """Test exporter type detection for console."""
        config = ObservabilityConfig(app_name="test-service", component="test-component",)

        assert config.exporter_type == ExporterType.CONSOLE

    def test_create_resource(self):
        """Test resource creation."""
        config = ObservabilityConfig(app_name="test-service", component="test-component",)
        resource = config.create_resource()

        assert resource.attributes["service.name"] == "test-service"
        assert resource.attributes["service.component"] == "test-component"
        assert resource.attributes["service.version"] == "1.0.0"


class TestObservabilityConfigFromEnv:
    """Test cases for environment-based configuration."""

    def setup_method(self):
        """Clear environment variables before each test."""
        env_vars_to_clear = [
            "OTEL_APP_NAME", "OTEL_GRPC_URL", "OTEL_HTTP_URL",
            "OTEL_HTTP_LOGS_URL", "OTEL_HTTP_TRACES_URL", "OTEL_HTTP_METRICS_URL",
            "LOG_LEVEL", "OTEL_INSECURE", "OTEL_METRIC_EXPORT_INTERVAL_MS",
            "ENABLE_CONSOLE_DEBUG",
        ]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

    def test_from_env_defaults(self):
        """Test from_env with no environment variables."""
        config = ObservabilityConfig.from_env()

        assert config.app_name == "unknown-service"
        assert config.otlp_endpoint is None
        assert config.otel_http_url is None
        assert config.insecure is True
        assert config.log_level == logging.INFO
        assert config.metric_export_interval_ms == 60000
        assert config.enable_console_debug is False

    def test_from_env_custom_app_name(self):
        """Test from_env with custom service name parameter."""
        config = ObservabilityConfig.from_env(app_name="custom-service", component="test-component",)

        assert config.app_name == "custom-service"

    def test_from_env_environment_variables(self):
        """Test from_env with all environment variables set."""
        os.environ.update({
            "OTEL_APP_NAME": "env-service",
            "OTEL_GRPC_URL": "grpc://otel:4317",
            "OTEL_HTTP_URL": "http://otel:4318",
            "LOG_LEVEL": "DEBUG",
            "OTEL_INSECURE": "false",
            "OTEL_METRIC_EXPORT_INTERVAL_MS": "30000",
            "ENABLE_CONSOLE_DEBUG": "true",
        })

        config = ObservabilityConfig.from_env()

        assert config.app_name == "env-service"
        assert config.otlp_endpoint == "grpc://otel:4317"
        assert config.otel_http_url == "http://otel:4318"
        assert config.http_logs_url == "http://otel:4318/v1/logs"
        assert config.http_traces_url == "http://otel:4318/v1/traces"
        assert config.http_metrics_url == "http://otel:4318/v1/metrics"
        assert config.insecure is False
        assert config.log_level == logging.DEBUG
        assert config.metric_export_interval_ms == 30000
        assert config.enable_console_debug is True

    def test_from_env_specific_urls(self):
        """Test from_env with specific HTTP URLs."""
        os.environ.update({
            "OTEL_HTTP_LOGS_URL": "http://logs:4318/v1/logs",
            "OTEL_HTTP_TRACES_URL": "http://traces:4318/v1/traces",
            "OTEL_HTTP_METRICS_URL": "http://metrics:4318/v1/metrics",
        })

        config = ObservabilityConfig.from_env(app_name="test-service", component="test-component",)

        assert config.http_logs_url == "http://logs:4318/v1/logs"
        assert config.http_traces_url == "http://traces:4318/v1/traces"
        assert config.http_metrics_url == "http://metrics:4318/v1/metrics"

    def test_from_env_log_level_parsing(self):
        """Test log level parsing from environment."""
        test_cases = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
            ("INVALID", logging.INFO),  # Default to INFO for invalid values
        ]

        for level_str, expected_level in test_cases:
            os.environ["LOG_LEVEL"] = level_str
            config = ObservabilityConfig.from_env()
            assert config.log_level == expected_level
