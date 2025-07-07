"""
Standard Logging Integration Examples for VibeCoding Logger

This file demonstrates various ways to integrate VibeCoding Logger with
Python's standard logging module for different use cases.
"""

import logging
import logging.config
import time
import threading
from contextlib import contextmanager

from vibelogger import create_file_logger, VibeLoggerConfig
from vibelogger.handlers import VibeLoggingHandler, VibeLoggerAdapter, setup_vibe_logging
from vibelogger.formatters import VibeJSONFormatter, create_structured_logger


# Example 1: Basic Integration with Standard Logging
def example_basic_integration():
    """Basic integration example - adding VibeCoding to existing logging."""
    
    print("=== Example 1: Basic Integration ===")
    
    # Create VibeCoding Logger
    vibe_logger = create_file_logger("basic_integration")
    
    # Set up standard logging with VibeCoding handler
    handler = VibeLoggingHandler(vibe_logger)
    
    # Configure standard logger
    logger = logging.getLogger("myapp")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Use standard logging - automatically enhanced with VibeCoding
    logger.info("Application started")
    logger.info("User login attempt", extra={
        'operation': 'user_login',
        'context': {'user_id': '123', 'ip': '192.168.1.1'},
        'human_note': 'Monitor login patterns for security'
    })
    
    try:
        # Simulate an error
        raise ValueError("Simulated error")
    except Exception as e:
        logger.exception("Login failed", extra={
            'operation': 'user_login',
            'context': {'user_id': '123', 'error_type': 'validation'},
            'ai_todo': 'Analyze login failure patterns and suggest improvements'
        })
    
    print(f"Logs saved to: {vibe_logger.log_file}")
    print()


# Example 2: Enhanced Logger Adapter
def example_enhanced_adapter():
    """Using VibeLoggerAdapter for enhanced logging methods."""
    
    print("=== Example 2: Enhanced Logger Adapter ===")
    
    # Set up enhanced adapter
    vibe_logger = create_file_logger("adapter_example")
    logger = setup_vibe_logging(vibe_logger, "enhanced_app")
    
    # Use VibeCoding-specific methods
    logger.vibe_info(
        operation="data_processing",
        message="Starting data processing job",
        context={'batch_size': 1000, 'source': 'api'},
        human_note="Track processing performance"
    )
    
    # Simulate processing with metrics
    start_time = time.time()
    time.sleep(0.1)  # Simulate work
    duration = (time.time() - start_time) * 1000
    
    logger.vibe_info(
        operation="data_processing",
        message="Data processing completed",
        context={
            'records_processed': 1000,
            'duration_ms': duration,
            'success_rate': 98.5
        }
    )
    
    # Log an exception with VibeCoding context
    try:
        raise ConnectionError("Database timeout")
    except Exception:
        logger.vibe_exception(
            operation="data_processing",
            message="Database connection failed",
            context={'retry_count': 3, 'timeout_ms': 5000},
            ai_todo="Investigate database connection issues and suggest retry strategy"
        )
    
    print(f"Enhanced logs saved to: {vibe_logger.log_file}")
    print()


# Example 3: JSON Formatter Integration
def example_json_formatter():
    """Using VibeCoding JSON formatter with standard logging."""
    
    print("=== Example 3: JSON Formatter ===")
    
    # Set up JSON formatter
    formatter = VibeJSONFormatter(
        include_extra=True,
        include_env=True,
        correlation_id="json-example-123"
    )
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Set up logger
    logger = logging.getLogger("json_app")
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    
    # Log with structured data
    logger.info("Processing API request", extra={
        'operation': 'api_request',
        'context': {
            'endpoint': '/api/users',
            'method': 'GET',
            'user_id': '456'
        },
        'human_note': 'Track API usage patterns'
    })
    
    print("JSON formatted logs printed to console above")
    print()


# Example 4: Structured Logger with Context Management
def example_structured_logger():
    """Using structured logger with automatic context management."""
    
    print("=== Example 4: Structured Logger ===")
    
    vibe_logger = create_file_logger("structured_example")
    struct_logger = create_structured_logger("payment_service", vibe_logger)
    
    # Add persistent context
    struct_logger.add_context(
        service_version="1.2.3",
        deployment="production"
    )
    
    # Use operation context
    with struct_logger.operation_context("process_payment") as ctx:
        struct_logger.info(
            "Starting payment processing",
            amount=99.99,
            currency="USD",
            payment_method="credit_card"
        )
        
        # Simulate payment steps
        struct_logger.debug("Validating payment details")
        time.sleep(0.05)
        
        struct_logger.debug("Charging payment provider")
        time.sleep(0.1)
        
        # Log metrics
        struct_logger.metric("payment_amount", 99.99, "USD")
        struct_logger.performance("payment_processing", 150.5)
        
        struct_logger.success(
            "Payment processed successfully",
            transaction_id="txn_123456",
            human_note="Monitor for fraud patterns"
        )
    
    print(f"Structured logs saved to: {vibe_logger.log_file}")
    print()


# Example 5: Multi-threaded Application Logging
def example_multithreaded_logging():
    """Thread-safe logging in multi-threaded applications."""
    
    print("=== Example 5: Multi-threaded Logging ===")
    
    vibe_logger = create_file_logger("multithreaded_example")
    logger = setup_vibe_logging(vibe_logger, "worker_app")
    
    def worker_task(worker_id, task_count):
        """Simulate worker task with logging."""
        
        for i in range(task_count):
            logger.vibe_info(
                operation="worker_task",
                message=f"Worker {worker_id} processing task {i+1}",
                context={
                    'worker_id': worker_id,
                    'task_number': i+1,
                    'total_tasks': task_count
                }
            )
            
            # Simulate work
            time.sleep(0.01)
            
            if i == task_count - 1:
                logger.vibe_info(
                    operation="worker_task",
                    message=f"Worker {worker_id} completed all tasks",
                    context={
                        'worker_id': worker_id,
                        'tasks_completed': task_count
                    }
                )
    
    # Start multiple worker threads
    threads = []
    for worker_id in range(3):
        thread = threading.Thread(
            target=worker_task,
            args=(worker_id, 5)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all workers to complete
    for thread in threads:
        thread.join()
    
    print(f"Multi-threaded logs saved to: {vibe_logger.log_file}")
    print()


# Example 6: Configuration-based Setup
def example_configuration_setup():
    """Setting up logging through configuration."""
    
    print("=== Example 6: Configuration-based Setup ===")
    
    # Create VibeCoding Logger
    vibe_logger = create_file_logger("config_example")
    
    # Logging configuration dictionary
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'vibe_json': {
                '()': 'vibelogger.formatters.VibeJSONFormatter',
                'include_extra': True,
                'correlation_id': 'config-example'
            },
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'vibe_handler': {
                '()': 'vibelogger.handlers.VibeLoggingHandler',
                'vibe_logger': vibe_logger,
                'level': 'INFO'
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': 'DEBUG'
            }
        },
        'loggers': {
            'myapp': {
                'handlers': ['vibe_handler', 'console'],
                'level': 'DEBUG',
                'propagate': False
            },
            'myapp.models': {
                'handlers': ['vibe_handler'],
                'level': 'INFO',
                'propagate': False
            }
        },
        'root': {
            'handlers': ['console'],
            'level': 'WARNING'
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Use the configured loggers
    app_logger = logging.getLogger('myapp')
    model_logger = logging.getLogger('myapp.models')
    
    app_logger.info("Application configured with VibeCoding logging")
    
    model_logger.info("User model operation", extra={
        'operation': 'user_create',
        'context': {'user_data': {'name': 'John Doe'}},
        'human_note': 'Track user creation patterns'
    })
    
    print(f"Configuration-based logs saved to: {vibe_logger.log_file}")
    print()


# Example 7: Integration with Third-party Libraries
def example_third_party_integration():
    """Integrating VibeCoding with third-party library logging."""
    
    print("=== Example 7: Third-party Library Integration ===")
    
    vibe_logger = create_file_logger("third_party_example")
    
    # Intercept requests library logging (if available)
    try:
        import requests
        requests_logger = logging.getLogger("urllib3.connectionpool")
        requests_logger.addHandler(VibeLoggingHandler(vibe_logger))
        requests_logger.setLevel(logging.DEBUG)
        
        print("Configured requests library logging with VibeCoding")
    except ImportError:
        print("Requests library not available - skipping")
    
    # Set up application logger
    app_logger = setup_vibe_logging(vibe_logger, "integration_app")
    
    app_logger.vibe_info(
        operation="external_api_call",
        message="Making external API request",
        context={
            'api_endpoint': 'https://api.example.com/users',
            'method': 'GET'
        },
        human_note="Monitor external API performance and failures"
    )
    
    # Simulate API call logging (without actual request)
    app_logger.vibe_info(
        operation="external_api_call",
        message="External API call completed",
        context={
            'status_code': 200,
            'response_time_ms': 245,
            'data_size': 1024
        }
    )
    
    print(f"Third-party integration logs saved to: {vibe_logger.log_file}")
    print()


# Example 8: Performance Monitoring Integration
def example_performance_monitoring():
    """Performance monitoring with VibeCoding logging."""
    
    print("=== Example 8: Performance Monitoring ===")
    
    vibe_logger = create_file_logger("performance_example")
    struct_logger = create_structured_logger("performance_service", vibe_logger)
    
    @contextmanager
    def performance_monitor(operation_name):
        """Context manager for performance monitoring."""
        start_time = time.time()
        
        struct_logger.info(f"Starting {operation_name}")
        
        try:
            yield
            duration = (time.time() - start_time) * 1000
            struct_logger.performance(operation_name, duration)
            struct_logger.success(f"Completed {operation_name}")
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            struct_logger.performance(operation_name, duration)
            struct_logger.failure(
                f"Failed {operation_name}: {str(e)}",
                ai_todo=f"Analyze {operation_name} failures and optimize performance"
            )
            raise
    
    # Use performance monitoring
    with performance_monitor("database_query"):
        time.sleep(0.05)  # Simulate database query
        struct_logger.metric("rows_fetched", 150, "rows")
    
    with performance_monitor("image_processing"):
        time.sleep(0.1)  # Simulate image processing
        struct_logger.metric("images_processed", 10, "images")
        struct_logger.metric("total_size", 2.5, "MB")
    
    # Simulate a performance issue
    try:
        with performance_monitor("slow_operation"):
            time.sleep(0.2)  # Simulate slow operation
            raise TimeoutError("Operation timed out")
    except TimeoutError:
        pass  # Expected for demo
    
    print(f"Performance monitoring logs saved to: {vibe_logger.log_file}")
    print()


# Main execution
if __name__ == "__main__":
    print("VibeCoding Logger - Standard Logging Integration Examples")
    print("=" * 60)
    print()
    
    # Run all examples
    example_basic_integration()
    example_enhanced_adapter()
    example_json_formatter()
    example_structured_logger()
    example_multithreaded_logging()
    example_configuration_setup()
    example_third_party_integration()
    example_performance_monitoring()
    
    print("All integration examples completed!")
    print("Check the generated log files in ./logs/ for detailed output.")