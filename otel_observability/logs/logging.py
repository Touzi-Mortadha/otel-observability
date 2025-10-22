"""Logging initializer for OpenTelemetry integration.

This module provides a logging initializer that sets up OpenTelemetry
logging with support for various exporters (OTLP, HTTP, Console).
"""

from __future__ import annotations

import logging

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter as GrpcOTLPLogExporter,
)
from opentelemetry.exporter.otlp.proto.http._log_exporter import (
    OTLPLogExporter as HttpOTLPLogExporter,
)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter

from otel_observability.config import ComponentInitializer, ExporterType


class LoggingInitializer(ComponentInitializer):
    """Initializer for OpenTelemetry logging."""

    def _setup_provider(self) -> None:
        """Set up the logging provider and handlers."""
        # Create and set logger provider
        logger_provider = LoggerProvider(
            resource=self.config.create_resource(),
        )
        set_logger_provider(logger_provider)

        # Add appropriate exporter
        if self.config.exporter_type == ExporterType.OTLP:
            exporter = GrpcOTLPLogExporter(
                endpoint=self.config.otlp_endpoint,
                insecure=self.config.insecure,
            )
        elif self.config.exporter_type == ExporterType.HTTP:
            exporter = HttpOTLPLogExporter(
                endpoint=self.config.http_logs_url,
            )
        else:
            exporter = ConsoleLogExporter()

        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(exporter),
        )

        # Configure root logger
        self._configure_root_logger(logger_provider)

    def _configure_root_logger(self, logger_provider: LoggerProvider) -> None:
        """Configure the root logger with OpenTelemetry handler."""
        root_logger = logging.getLogger()

        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()

        # Add OpenTelemetry handler
        otel_handler = LoggingHandler(logger_provider=logger_provider)
        otel_handler.setLevel(self.config.log_level)
        root_logger.addHandler(otel_handler)

        # Set root logger level
        root_logger.setLevel(self.config.log_level)

        # Add console handler for debugging if enabled
        if self.config.enable_console_debug:
            self._add_console_handler(root_logger)

    def _add_console_handler(self, logger: logging.Logger) -> None:
        """Add a console handler for debug output."""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.config.log_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
