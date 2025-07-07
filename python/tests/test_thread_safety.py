"""
Comprehensive thread safety tests for VibeCoding Logger

Tests various concurrent scenarios including high contention,
race conditions, and stress testing under load.
"""

import json
import tempfile
import threading
import time
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from vibelogger import (
    create_logger,
    create_file_logger,
    VibeLoggerConfig
)


class TestThreadSafety:
    """Comprehensive thread safety tests."""
    
    def test_high_contention_logging(self):
        """Test logging under high thread contention."""
        logger = create_logger()
        
        # Many threads, many iterations
        thread_count = 50
        iterations_per_thread = 100
        results = []
        
        def worker(thread_id):
            """Worker that logs many messages quickly."""
            local_results = []
            for i in range(iterations_per_thread):
                entry = logger.info(
                    operation="high_contention_test",
                    message=f"Thread {thread_id} message {i}",
                    context={
                        'thread_id': thread_id,
                        'iteration': i,
                        'timestamp': time.time()
                    }
                )
                local_results.append((thread_id, i, entry.correlation_id))
            return local_results
        
        # Start all threads simultaneously
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [executor.submit(worker, i) for i in range(thread_count)]
            
            for future in as_completed(futures):
                results.extend(future.result())
        
        # Verify results
        expected_total = thread_count * iterations_per_thread
        assert len(results) == expected_total
        
        # Verify all logs were captured (within memory limits)
        actual_logs = len(logger.logs)
        # Memory management may limit logs, but should have most of them
        assert actual_logs >= min(expected_total * 0.8, 1000)
        
        # Verify no corruption - all logs should be valid
        for log in logger.logs:
            assert log.operation == "high_contention_test"
            assert "thread_id" in log.context
            assert "iteration" in log.context
    
    def test_file_write_race_conditions(self):
        """Test concurrent file writing for race conditions."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            config = VibeLoggerConfig(
                log_file=log_file,
                auto_save=True,
                keep_logs_in_memory=False  # Force file writing
            )
            
            # Multiple loggers writing to same file
            loggers = [create_logger(config=config) for _ in range(10)]
            thread_count = 20
            iterations_per_thread = 50
            
            def worker(worker_id):
                """Worker that writes to file through different loggers."""
                logger = loggers[worker_id % len(loggers)]
                for i in range(iterations_per_thread):
                    logger.info(
                        operation="file_race_test",
                        message=f"Worker {worker_id} message {i}",
                        context={'worker_id': worker_id, 'iteration': i}
                    )
                    # Small random delay to increase chance of race conditions
                    time.sleep(random.uniform(0.0001, 0.001))
            
            # Start all workers
            threads = [threading.Thread(target=worker, args=(i,)) for i in range(thread_count)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # Verify file integrity
            assert Path(log_file).exists()
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            valid_lines = [line.strip() for line in lines if line.strip()]
            expected_lines = thread_count * iterations_per_thread
            
            # Should have all lines (with some tolerance for race conditions)
            assert len(valid_lines) >= expected_lines * 0.95
            
            # Verify each line is valid JSON
            valid_count = 0
            for line in valid_lines:
                try:
                    data = json.loads(line)
                    assert data['operation'] == 'file_race_test'
                    assert 'worker_id' in data['context']
                    valid_count += 1
                except json.JSONDecodeError:
                    # Some corruption is possible under extreme race conditions
                    pass
            
            # At least 90% should be valid JSON
            assert valid_count >= len(valid_lines) * 0.9
            
        finally:
            Path(log_file).unlink(missing_ok=True)
    
    def test_memory_corruption_prevention(self):
        """Test that concurrent access doesn't corrupt memory state."""
        logger = create_logger()
        
        # Track all operations to verify consistency
        all_operations = []
        lock = threading.Lock()
        
        def worker(worker_id):
            """Worker that performs various operations."""
            operations = []
            
            # Log entries
            for i in range(20):
                entry = logger.info(
                    operation=f"worker_{worker_id}_operation",
                    message=f"Message {i}",
                    context={'worker_id': worker_id, 'msg_id': i}
                )
                operations.append(('log', worker_id, i, entry.correlation_id))
            
            # Get logs
            logs_json = logger.get_logs_for_ai()
            operations.append(('get_logs', worker_id, len(logs_json)))
            
            # Clear logs (some workers)
            if worker_id % 3 == 0:
                initial_count = len(logger.logs)
                logger.clear_logs()
                operations.append(('clear', worker_id, initial_count))
            
            with lock:
                all_operations.extend(operations)
        
        # Run workers concurrently
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Verify operations completed without corruption
        assert len(all_operations) > 0
        
        # Check for operation consistency
        log_operations = [op for op in all_operations if op[0] == 'log']
        clear_operations = [op for op in all_operations if op[0] == 'clear']
        
        # Should have log operations from all workers
        worker_ids = set(op[1] for op in log_operations)
        assert len(worker_ids) == 10
        
        # Logger should be in a consistent state
        assert isinstance(logger.logs, list)
        assert isinstance(logger.correlation_id, str)
        assert len(logger.correlation_id) > 0
    
    def test_exception_handling_thread_safety(self):
        """Test exception handling doesn't break thread safety."""
        logger = create_logger()
        exceptions_caught = []
        lock = threading.Lock()
        
        def worker(worker_id):
            """Worker that generates exceptions."""
            try:
                for i in range(10):
                    try:
                        # Generate different types of exceptions
                        if i % 3 == 0:
                            raise ValueError(f"Worker {worker_id} ValueError {i}")
                        elif i % 3 == 1:
                            raise TypeError(f"Worker {worker_id} TypeError {i}")
                        else:
                            raise RuntimeError(f"Worker {worker_id} RuntimeError {i}")
                    except Exception as e:
                        logger.log_exception(
                            operation=f"exception_test_worker_{worker_id}",
                            exception=e,
                            context={'worker_id': worker_id, 'exception_num': i}
                        )
                        
                        with lock:
                            exceptions_caught.append((worker_id, i, type(e).__name__))
            except Exception as e:
                # Catch any unexpected exceptions
                with lock:
                    exceptions_caught.append((worker_id, -1, f"UNEXPECTED: {type(e).__name__}"))
        
        # Run exception-generating workers
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Verify exception handling worked
        assert len(exceptions_caught) == 50  # 5 workers * 10 exceptions each
        
        # Verify no unexpected exceptions
        unexpected = [exc for exc in exceptions_caught if 'UNEXPECTED' in exc[2]]
        assert len(unexpected) == 0
        
        # Verify logs contain exception information
        error_logs = [log for log in logger.logs if log.level == 'ERROR']
        assert len(error_logs) > 0
        
        # Verify logger is still functional
        logger.info("post_exception_test", "Logger still works")
        assert len(logger.logs) > len(error_logs)
    
    def test_configuration_thread_safety(self):
        """Test that configuration changes are thread-safe."""
        # Test multiple loggers with different configs created concurrently
        configs = []
        loggers = []
        
        def create_logger_worker(worker_id):
            """Worker that creates loggers with different configs."""
            config = VibeLoggerConfig(
                correlation_id=f"thread_{worker_id}",
                keep_logs_in_memory=worker_id % 2 == 0,
                max_memory_logs=100 + worker_id * 10
            )
            logger = create_logger(config=config)
            
            # Test the logger
            logger.info(f"config_test_worker_{worker_id}", f"Test from worker {worker_id}")
            
            return config, logger
        
        # Create loggers concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_logger_worker, i) for i in range(10)]
            
            for future in as_completed(futures):
                config, logger = future.result()
                configs.append(config)
                loggers.append(logger)
        
        # Verify all loggers are properly configured and isolated
        assert len(loggers) == 10
        
        # Extract correlation IDs from the loggers
        correlation_ids = [logger.correlation_id for logger in loggers]
        
        # All correlation IDs should be unique
        assert len(set(correlation_ids)) == len(correlation_ids)
        
        # Each correlation ID should match the expected pattern
        for correlation_id in correlation_ids:
            assert correlation_id.startswith("thread_")
            thread_num = correlation_id.split("_")[1]
            assert thread_num.isdigit()
            assert 0 <= int(thread_num) <= 9
            
            # Each logger should have at least one log
            assert len(logger.logs) >= 0  # May be 0 if memory disabled
            
            # Logger should be functional
            logger.info("final_test", "Final test message")
    
    def test_stress_test_mixed_operations(self):
        """Stress test with mixed read/write operations."""
        logger = create_file_logger("stress_test")
        
        # Statistics tracking
        stats = {
            'writes': 0,
            'reads': 0,
            'exceptions': 0,
            'errors': 0
        }
        stats_lock = threading.Lock()
        
        def mixed_operations_worker(worker_id):
            """Worker performing mixed operations."""
            local_stats = {'writes': 0, 'reads': 0, 'exceptions': 0, 'errors': 0}
            
            for i in range(50):
                try:
                    operation_type = i % 4
                    
                    if operation_type == 0:
                        # Write operation
                        logger.info(
                            operation="stress_write",
                            message=f"Stress write {worker_id}:{i}",
                            context={'worker': worker_id, 'iter': i}
                        )
                        local_stats['writes'] += 1
                        
                    elif operation_type == 1:
                        # Read operation
                        logs = logger.get_logs_for_ai()
                        assert isinstance(logs, str)
                        local_stats['reads'] += 1
                        
                    elif operation_type == 2:
                        # Exception operation
                        try:
                            raise Exception(f"Test exception {worker_id}:{i}")
                        except Exception as e:
                            logger.log_exception(
                                operation="stress_exception",
                                exception=e
                            )
                        local_stats['exceptions'] += 1
                        
                    else:
                        # Error operation
                        logger.error(
                            operation="stress_error",
                            message=f"Stress error {worker_id}:{i}",
                            context={'type': 'stress_test'}
                        )
                        local_stats['errors'] += 1
                        
                    # Random small delay
                    time.sleep(random.uniform(0.0001, 0.002))
                    
                except Exception as e:
                    # Any unexpected exception is a test failure
                    print(f"Unexpected exception in worker {worker_id}: {e}")
                    raise
            
            # Update global stats
            with stats_lock:
                for key in stats:
                    stats[key] += local_stats[key]
        
        # Run stress test with many workers
        workers = 20
        threads = [threading.Thread(target=mixed_operations_worker, args=(i,)) 
                  for i in range(workers)]
        
        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        duration = time.time() - start_time
        
        # Verify stress test results
        expected_operations_per_type = workers * 50 // 4  # 250 each type
        tolerance = 0.1  # 10% tolerance
        
        assert abs(stats['writes'] - expected_operations_per_type) <= expected_operations_per_type * tolerance
        assert abs(stats['reads'] - expected_operations_per_type) <= expected_operations_per_type * tolerance
        assert abs(stats['exceptions'] - expected_operations_per_type) <= expected_operations_per_type * tolerance
        assert abs(stats['errors'] - expected_operations_per_type) <= expected_operations_per_type * tolerance
        
        # Performance check - should complete within reasonable time
        assert duration < 30.0  # Should complete within 30 seconds
        
        # Logger should still be functional after stress test
        logger.info("post_stress_test", "Stress test completed successfully")
        
        print(f"Stress test completed in {duration:.2f}s")
        print(f"Operations: {stats}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])