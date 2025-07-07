"""
Test cases specifically for AI feedback improvements

This module tests the improvements made based on AI code review feedback:
1. DRY principle implementation (_process_entry method)
2. Robust caller info detection
3. Enhanced file loading with error recovery
"""

import json
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from vibelogger import (
    VibeLogger,
    VibeLoggerConfig,
    create_logger,
    create_file_logger,
    EnvironmentInfo
)


class TestDRYPrincipleImplementation:
    """Test DRY principle improvements with _process_entry method."""

    def test_process_entry_method_exists(self):
        """Test that _process_entry method exists and is used."""
        logger = create_logger()
        
        # Check that the method exists
        assert hasattr(logger, '_process_entry')
        assert callable(getattr(logger, '_process_entry'))

    def test_process_entry_memory_handling(self):
        """Test _process_entry handles memory operations correctly."""
        config = VibeLoggerConfig(keep_logs_in_memory=True, max_memory_logs=3)
        logger = create_logger(config=config)
        
        # Create test entries
        from vibelogger.logger import LogEntry, LogLevel
        from datetime import datetime, timezone
        
        entries = []
        for i in range(5):
            entry = LogEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                level=LogLevel.INFO.value,
                correlation_id=logger.correlation_id,
                operation=f"test_op_{i}",
                message=f"Test message {i}",
                context={},
                environment=logger.environment
            )
            entries.append(entry)
            logger._process_entry(entry)
        
        # Should only keep the last 3 entries due to memory limit
        assert len(logger.logs) == 3
        assert logger.logs[0].operation == "test_op_2"
        assert logger.logs[1].operation == "test_op_3"
        assert logger.logs[2].operation == "test_op_4"

    def test_process_entry_no_memory_storage(self):
        """Test _process_entry with memory storage disabled."""
        config = VibeLoggerConfig(keep_logs_in_memory=False)
        logger = create_logger(config=config)
        
        from vibelogger.logger import LogEntry, LogLevel
        from datetime import datetime, timezone
        
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=LogLevel.INFO.value,
            correlation_id=logger.correlation_id,
            operation="no_memory_test",
            message="Should not be stored",
            context={},
            environment=logger.environment
        )
        
        logger._process_entry(entry)
        
        # Should not be stored in memory
        assert len(logger.logs) == 0

    def test_log_and_log_exception_use_process_entry(self):
        """Test that both log() and log_exception() use _process_entry."""
        logger = create_logger()
        
        # Patch _process_entry to verify it's called
        with patch.object(logger, '_process_entry') as mock_process:
            # Test regular logging
            logger.info("test_op", "Test message")
            assert mock_process.call_count == 1
            
            # Test exception logging
            try:
                raise ValueError("Test exception")
            except Exception as e:
                logger.log_exception("exception_op", e)
            
            assert mock_process.call_count == 2


class TestRobustCallerInfo:
    """Test robust caller information detection."""

    def test_caller_info_detection_accuracy(self):
        """Test that caller info accurately detects source outside logger."""
        
        def level_1_function():
            def level_2_function():
                def level_3_function():
                    logger = create_logger()
                    return logger.info("caller_test", "Deep nested call")
                return level_3_function()
            return level_2_function()
        
        entry = level_1_function()
        
        # Should detect level_3_function as the caller, not internal logger methods
        assert entry.source is not None
        assert 'test_ai_feedback_improvements.py' in entry.source
        assert 'level_3_function' in entry.source
        assert 'logger.py' not in entry.source  # Should not reference internal logger file

    def test_caller_info_with_different_call_patterns(self):
        """Test caller info detection with various call patterns."""
        logger = create_logger()
        
        # Direct call
        entry1 = logger.debug("direct", "Direct call")
        assert 'test_ai_feedback_improvements.py' in entry1.source
        
        # Through variable
        log_func = logger.warning
        entry2 = log_func("indirect", "Indirect call")
        assert 'test_ai_feedback_improvements.py' in entry2.source
        
        # Through exception
        try:
            raise RuntimeError("Test error")
        except Exception as e:
            entry3 = logger.log_exception("exception", e)
            assert 'test_ai_feedback_improvements.py' in entry3.source

    def test_caller_info_robustness_edge_cases(self):
        """Test caller info detection in edge cases."""
        
        # Test when called from different contexts
        def recursive_function(depth):
            if depth == 0:
                logger = create_logger()
                return logger.error("recursive", f"Recursive call depth {depth}")
            return recursive_function(depth - 1)
        
        entry = recursive_function(3)
        
        # Should still detect the correct caller
        assert entry.source is not None
        assert 'recursive_function' in entry.source

    def test_caller_info_fallback(self):
        """Test caller info fallback for edge cases."""
        logger = create_logger()
        
        # Mock inspect.getsourcefile to return None (edge case)
        with patch('inspect.getsourcefile', return_value=None):
            entry = logger.info("fallback_test", "Testing fallback")
            # Should not crash and should have some source info
            assert entry.source == "Unknown source" or entry.source is not None


class TestRobustFileLoading:
    """Test enhanced file loading with error recovery."""

    def test_load_corrupted_json_file(self):
        """Test loading file with various types of corruption."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
            
            # Write mixed valid and corrupted data
            test_lines = [
                # Valid JSON
                '{"timestamp": "2025-07-07T10:00:00Z", "level": "INFO", "correlation_id": "test-1", "operation": "valid_op", "message": "Valid message", "context": {}, "environment": {"python_version": "3.9", "os": "test", "platform": "test", "architecture": "test"}}',
                
                # Invalid JSON (missing closing brace)
                '{"timestamp": "2025-07-07T10:00:01Z", "level": "ERROR", "correlation_id": "test-2"',
                
                # Missing required fields
                '{"timestamp": "2025-07-07T10:00:02Z", "context": {}}',
                
                # Empty line
                '',
                
                # Another valid entry
                '{"timestamp": "2025-07-07T10:00:03Z", "level": "WARNING", "correlation_id": "test-3", "operation": "another_valid", "message": "Another valid", "context": {}, "environment": {"python_version": "3.9", "os": "test", "platform": "test", "architecture": "test"}}',
                
                # Invalid environment data
                '{"timestamp": "2025-07-07T10:00:04Z", "level": "DEBUG", "correlation_id": "test-4", "operation": "invalid_env", "message": "Invalid env data", "context": {}, "environment": {"invalid_field": "bad_data"}}',
                
                # No environment field
                '{"timestamp": "2025-07-07T10:00:05Z", "level": "CRITICAL", "correlation_id": "test-5", "operation": "no_env", "message": "No environment", "context": {}}'
            ]
            
            for line in test_lines:
                f.write(line + '\n')
        
        try:
            logger = create_logger()
            
            # Capture stdout to check warning messages
            import io
            import sys
            from contextlib import redirect_stdout
            
            captured_output = io.StringIO()
            with redirect_stdout(captured_output):
                logger.load_logs_from_file(log_file)
            
            output = captured_output.getvalue()
            
            # Should load valid entries + entries with recovered environment
            # 2 fully valid + 2 with environment issues that get default env = 4 total
            assert len(logger.logs) == 4
            
            # Check that valid entries are present
            operations = [log.operation for log in logger.logs]
            assert "valid_op" in operations
            assert "another_valid" in operations
            assert "invalid_env" in operations  # Should be recovered
            assert "no_env" in operations       # Should be recovered
            
            # Check that warnings were printed
            assert "Warning:" in output or "Loaded" in output
            
        finally:
            Path(log_file).unlink(missing_ok=True)

    def test_load_completely_corrupted_file(self):
        """Test loading file that is completely corrupted."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
            
            # Write completely invalid data
            f.write("This is not JSON at all\n")
            f.write("Neither is this line\n")
            f.write("{ incomplete json\n")
            f.write("42\n")  # Valid JSON but not a log entry
        
        try:
            logger = create_logger()
            
            # Should not crash and should load 0 entries
            logger.load_logs_from_file(log_file)
            assert len(logger.logs) == 0
            
        finally:
            Path(log_file).unlink(missing_ok=True)

    def test_load_mixed_format_file(self):
        """Test loading file with mixed old and new formats."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
            
            # Write entries with different field combinations
            test_entries = [
                # Complete entry
                {
                    "timestamp": "2025-07-07T10:00:00Z",
                    "level": "INFO",
                    "correlation_id": "test-1",
                    "operation": "complete",
                    "message": "Complete entry",
                    "context": {"key": "value"},
                    "environment": {
                        "python_version": "3.9",
                        "os": "test",
                        "platform": "test",
                        "architecture": "test"
                    },
                    "source": "test.py:10",
                    "human_note": "Test note",
                    "ai_todo": "Test task"
                },
                
                # Minimal entry
                {
                    "timestamp": "2025-07-07T10:00:01Z",
                    "level": "ERROR",
                    "correlation_id": "test-2",
                    "operation": "minimal",
                    "message": "Minimal entry",
                    "context": {},
                    "environment": {
                        "python_version": "3.9",
                        "os": "test",
                        "platform": "test",
                        "architecture": "test"
                    }
                }
            ]
            
            for entry in test_entries:
                f.write(json.dumps(entry) + '\n')
        
        try:
            logger = create_logger()
            logger.load_logs_from_file(log_file)
            
            assert len(logger.logs) == 2
            
            # Check that both entries were loaded correctly
            operations = [log.operation for log in logger.logs]
            assert "complete" in operations
            assert "minimal" in operations
            
            # Check that optional fields are preserved
            complete_log = next(log for log in logger.logs if log.operation == "complete")
            assert complete_log.human_note == "Test note"
            assert complete_log.ai_todo == "Test task"
            
            minimal_log = next(log for log in logger.logs if log.operation == "minimal")
            assert minimal_log.human_note is None
            assert minimal_log.ai_todo is None
            
        finally:
            Path(log_file).unlink(missing_ok=True)

    def test_environment_recovery(self):
        """Test that missing or invalid environment data gets recovered."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
            
            # Entry with missing environment
            entry_no_env = {
                "timestamp": "2025-07-07T10:00:00Z",
                "level": "INFO",
                "correlation_id": "test-1",
                "operation": "no_env_test",
                "message": "No environment",
                "context": {}
            }
            
            # Entry with invalid environment
            entry_bad_env = {
                "timestamp": "2025-07-07T10:00:01Z",
                "level": "WARNING",
                "correlation_id": "test-2",
                "operation": "bad_env_test",
                "message": "Bad environment",
                "context": {},
                "environment": {"wrong": "format", "missing": "required_fields"}
            }
            
            f.write(json.dumps(entry_no_env) + '\n')
            f.write(json.dumps(entry_bad_env) + '\n')
        
        try:
            logger = create_logger()
            logger.load_logs_from_file(log_file)
            
            assert len(logger.logs) == 2
            
            # Both entries should have valid environment info (recovered)
            for log in logger.logs:
                assert log.environment is not None
                assert hasattr(log.environment, 'python_version')
                assert hasattr(log.environment, 'os')
                assert hasattr(log.environment, 'platform')
                assert hasattr(log.environment, 'architecture')
            
        finally:
            Path(log_file).unlink(missing_ok=True)


class TestThreadSafetyWithImprovements:
    """Test that improvements maintain thread safety."""

    def test_process_entry_thread_safety(self):
        """Test that _process_entry is thread-safe."""
        config = VibeLoggerConfig(max_memory_logs=50)
        logger = create_logger(config=config)
        
        def worker(worker_id):
            for i in range(20):
                logger.info(f"thread_test_{worker_id}", f"Message {i}", 
                           context={'worker': worker_id, 'iteration': i})
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have logged entries from all threads
        assert len(logger.logs) == 50  # Limited by max_memory_logs
        
        # Verify all worker IDs are represented
        worker_ids = set()
        for log in logger.logs:
            worker_ids.add(log.context['worker'])
        
        assert len(worker_ids) == 5  # All 5 workers should be represented

    def test_concurrent_caller_info_detection(self):
        """Test caller info detection under concurrent access."""
        logger = create_logger()
        caller_sources = []
        lock = threading.Lock()
        
        def worker(worker_id):
            def nested_call():
                entry = logger.error("concurrent_caller", f"Worker {worker_id}")
                with lock:
                    caller_sources.append(entry.source)
        
            nested_call()
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should have detected the same source pattern
        assert len(caller_sources) == 10
        for source in caller_sources:
            assert 'nested_call' in source
            assert 'test_ai_feedback_improvements.py' in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])