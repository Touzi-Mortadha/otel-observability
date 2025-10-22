#!/usr/bin/env python3
"""Test script for OTEL Observability package against a live OTEL collector.

This script demonstrates how to test all three telemetry signals (logs, metrics, traces)
against an existing OTEL collector deployment.

Usage:
    python test_otel_collector.py --help

Example with environment variables:
    export OTEL_APP_NAME="test-service"
    export OTEL_COMPONENT_NAME="test-component"
    export OTEL_GRPC_URL="localhost:4317"
    export OTEL_INSECURE="true"
    python test_otel_collector.py

Example with command line arguments:
    python test_otel_collector.py --service-name test-service --endpoint localhost:4317 --insecure
"""

import argparse
import logging
import os
import sys
import time
from typing import Optional

# Add the current directory to Python path to import the local package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from otel_observability import ObservabilityConfig
    from otel_observability import ObservabilityManager
    from otel_observability import ObservabilityDecorators
    from otel_observability import get_logger
    from otel_observability import get_metrics
    from otel_observability import get_traces
    from otel_observability import initialize_observability
except ImportError as e:
    print(f"Error importing observability package: {e}")
    print("Make sure you're in the project root directory and the package is installed")
    sys.exit(1)


class OTELCollectorTester:
    """Test class for verifying OTEL collector integration."""

    def __init__(self, app_name: str, endpoint: str, insecure: bool = True):
        """Initialize the tester with configuration."""
        self.app_name = app_name
        self.endpoint = endpoint
        self.insecure = insecure
        
        self.config = ObservabilityConfig(
            app_name=app_name,
            component="test-component",
            otlp_endpoint=endpoint,
            insecure=insecure,
            enable_console_debug=True,  # Also show console output for debugging
        )
        
        # Initialize observability
        self.manager = ObservabilityManager(self.config)
        self.manager.initialize_all()
        
        # Get telemetry components
        self.logger = get_logger(__name__)
        self.meter = get_metrics("otel-collector-test")
        self.tracer = get_traces("otel-collector-test")
        
        # Create metrics
        self.request_counter = self.meter.create_counter(
            "test_requests_total",
            unit="1",
            description="Total number of test requests"
        )
        self.response_time_histogram = self.meter.create_histogram(
            "test_response_time_seconds",
            unit="s",
            description="Response time for test operations"
        )

    def test_logging(self, message: str = "Test log message"):
        """Test logging functionality."""
        print(f"Testing logging with message: {message}")
        
        # Test different log levels
        self.logger.debug(f"DEBUG: {message}")
        self.logger.info(f"INFO: {message}")
        self.logger.warning(f"WARNING: {message}")
        self.logger.error(f"ERROR: {message}")
        
        # Test with structured logging
        self.logger.info(
            "Structured log test",
            extra={
                "user_id": "test-user-123",
                "action": "test_operation",
                "duration_ms": 150
            }
        )

    def test_metrics(self):
        """Test metrics functionality."""
        print("Testing metrics...")
        
        # Record some test metrics
        self.request_counter.add(1, {"endpoint": "/test", "method": "GET", "status": "200"})
        self.request_counter.add(2, {"endpoint": "/test", "method": "POST", "status": "201"})
        self.request_counter.add(1, {"endpoint": "/test", "method": "GET", "status": "404"})
        
        # Record response times
        for response_time in [0.1, 0.2, 0.15, 0.3, 0.25]:
            self.response_time_histogram.record(
                response_time,
                {"endpoint": "/test", "method": "GET"}
            )
        
        print("Metrics recorded successfully")

    def test_tracing(self):
        """Test tracing functionality."""
        print("Testing tracing...")
        
        # Create a simple trace
        with self.tracer.start_as_current_span("test_operation") as span:
            span.set_attribute("test.attribute", "test_value")
            span.set_attribute("user.id", "test-user-456")
            
            # Simulate some work
            time.sleep(0.1)
            
            # Create a child span
            with self.tracer.start_as_current_span("child_operation") as child_span:
                child_span.set_attribute("child.attribute", "child_value")
                time.sleep(0.05)
                
            # Log an event
            span.add_event("operation_completed", {"result": "success"})

    # @ObservabilityDecorators.trace_method()
    # @ObservabilityDecorators.log_execution()
    def test_decorators(self, data: dict):
        """Test decorators with automatic tracing and logging."""
        self.logger.info(f"Processing data with decorators: {data}")
        time.sleep(0.1)  # Simulate work
        return {"processed": True, **data}

    def run_comprehensive_test(self):
        """Run a comprehensive test of all telemetry signals."""
        print(f"\n{'='*60}")
        print(f"Starting OTEL Collector Test")
        print(f"Service: {self.app_name}")
        print(f"Endpoint: {self.endpoint}")
        print(f"Insecure: {self.insecure}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        try:
            # Test 1: Basic logging
            print("\n1. Testing Logging...")
            self.test_logging("Initial test message")
            
            # Test 2: Metrics
            print("\n2. Testing Metrics...")
            self.test_metrics()
            
            # Test 3: Tracing
            print("\n3. Testing Tracing...")
            self.test_tracing()
            
            # Test 4: Decorators
            print("\n4. Testing Decorators...")
            # result = self.test_decorators({"input": "test_data", "value": 42})
            # print(f"Decorator test result: {result}")
            
            # Test 5: Error scenario
            print("\n5. Testing Error Logging...")
            try:
                raise ValueError("This is a test error for observability")
            except ValueError as e:
                self.logger.exception("Test error occurred")
            
            elapsed_time = time.time() - start_time
            
            print(f"\n{'='*60}")
            print("Test completed successfully!")
            print(f"Total duration: {elapsed_time:.2f} seconds")
            print(f"Check your OTEL collector for received telemetry data")
            print(f"{'='*60}")
            
            # Give time for metrics to be exported
            print("\nWaiting for metrics export...")
            time.sleep(2)
            
        except Exception as e:
            self.logger.exception("Test failed with error")
            print(f"\nTest failed: {e}")
            return False
        
        return True

    def shutdown(self):
        """Shutdown the observability system."""
        print("\nShutting down observability...")
        self.manager.shutdown()


def main():

    # Create and run tester
    tester = OTELCollectorTester(
        app_name="DATABRIDGE",
        component="test-component",
        endpoint="http://20.84.88.143:4317",
        insecure=True
    )
    
    try:
        success = tester.run_comprehensive_test()
        return 0 if success else 1
    finally:
        tester.shutdown()


if __name__ == "__main__":
    sys.exit(main())