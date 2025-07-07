"""
Edge cases and stress tests for VibeCoding Logger

These tests cover challenging scenarios including error conditions,
resource limits, security issues, and performance edge cases.
"""

import json
import os
import tempfile
import threading
import time
import uuid
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from vibelogger import (
    VibeLogger,
    LogLevel,
    VibeLoggerConfig,
    create_logger,
    create_file_logger
)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_extremely_large_context(self):
        """Test logging with extremely large context data."""
        logger = create_logger()
        
        # Create a large context (1MB of data)
        large_data = "x" * (1024 * 1024)
        large_context = {
            "large_field": large_data,
            "nested": {
                "data": [large_data] * 10
            }
        }
        
        # Should handle large data without crashing
        entry = logger.info("test_op", "Large context test", context=large_context)
        assert entry.context["large_field"] == large_data
        assert len(logger.logs) == 1
    
    def test_unicode_and_special_characters(self):
        """Test logging with various Unicode and special characters."""
        logger = create_logger()
        
        unicode_data = {
            "emoji": "🚀🎉💻🔥",
            "chinese": "你好世界",
            "arabic": "مرحبا بالعالم",
            "japanese": "こんにちは世界",
            "special_chars": "!@#$%^&*()[]{}|\\;':\",./<>?",
            "null_char": "\x00",
            "newlines": "line1\nline2\rline3\r\nline4",
            "tabs": "col1\tcol2\tcol3"
        }
        
        entry = logger.info("unicode_test", "Testing Unicode support", context=unicode_data)
        
        # Verify all Unicode data is preserved
        assert entry.context["emoji"] == "🚀🎉💻🔥"
        assert entry.context["chinese"] == "你好世界"
        assert entry.context["special_chars"] == "!@#$%^&*()[]{}|\\;':\",./<>?"
    
    def test_circular_reference_in_context(self):
        """Test handling circular references in context data."""
        logger = create_logger()
        
        # Create circular reference
        circular_data = {"name": "test"}
        circular_data["self"] = circular_data
        
        # Should handle circular reference gracefully (may truncate or error)
        try:
            entry = logger.info("circular_test", "Circular reference test", 
                              context={"data": circular_data})
            # If no exception, verify entry was created
            assert entry is not None
        except (ValueError, TypeError, RecursionError):
            # Acceptable to fail on circular references
            pass
    
    def test_none_and_empty_values(self):
        """Test handling of None and empty values."""
        logger = create_logger()
        
        # Test with None values
        entry = logger.info(
            operation=None,  # This should be handled
            message="",      # Empty message
            context={
                "null_value": None,
                "empty_string": "",
                "empty_list": [],
                "empty_dict": {},
                "zero": 0,
                "false": False
            }
        )
        
        assert entry.message == ""
        assert entry.context["null_value"] is None
        assert entry.context["empty_string"] == ""
        assert entry.context["zero"] == 0
        assert entry.context["false"] is False


class TestFileSystemEdgeCases:
    """Test file system related edge cases."""
    
    def test_invalid_file_path(self):
        """Test handling of invalid file paths."""
        # Test with invalid characters in path
        invalid_paths = [
            "/invalid\x00path.log",  # Null character
            "/non/existent/deeply/nested/path/file.log",  # Deep non-existent path
            "",  # Empty path
            "/root/restricted.log" if os.name != 'nt' else "C:\\Windows\\System32\\restricted.log"
        ]
        
        for invalid_path in invalid_paths:
            try:
                config = VibeLoggerConfig(log_file=invalid_path, auto_save=True)
                logger = create_logger(config=config)
                logger.info("test_op", "Test message")
                # If it succeeds, that's also acceptable
            except (OSError, PermissionError, ValueError):
                # Expected to fail on invalid paths
                pass
    
    def test_file_permission_denied(self):
        """Test handling when file cannot be written due to permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a read-only directory
            readonly_dir = Path(temp_dir) / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)  # Read-only
            
            log_file = readonly_dir / "test.log"
            
            try:
                config = VibeLoggerConfig(log_file=str(log_file), auto_save=True)
                logger = create_logger(config=config)
                
                # This should not crash the application
                logger.info("test_op", "Permission test")
                
            except PermissionError:
                # Acceptable to fail
                pass
            finally:
                # Cleanup: restore permissions
                readonly_dir.chmod(0o755)
    
    def test_disk_space_simulation(self):
        """Test behavior when disk is full (simulated)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name
        
        try:
            # Mock the file operations to simulate disk full
            with patch('builtins.open', mock_open()) as mock_file:
                mock_file.return_value.write.side_effect = OSError("No space left on device")
                
                config = VibeLoggerConfig(log_file=log_file, auto_save=True)
                logger = create_logger(config=config)
                
                # Should handle disk full gracefully
                logger.info("test_op", "Disk full test")
                
        finally:
            Path(log_file).unlink(missing_ok=True)
    
    def test_concurrent_file_access(self):
        """Test concurrent access to the same log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            config = VibeLoggerConfig(log_file=log_file, auto_save=True)
            
            def worker(worker_id):
                logger = create_logger(config=config)
                for i in range(50):
                    logger.info("concurrent_test", f"Worker {worker_id} message {i}")
            
            # Start multiple threads writing to same file
            threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # Verify file exists and contains data
            assert Path(log_file).exists()
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
                # Each line should be a complete JSON object
                valid_lines = [line.strip() for line in lines if line.strip()]
                assert len(valid_lines) == 250  # 5 workers * 50 messages each
                
                # Verify each line is valid JSON
                for line in valid_lines:
                    data = json.loads(line)
                    assert "concurrent_test" in data["operation"]
                    
        finally:
            Path(log_file).unlink(missing_ok=True)


class TestMemoryStressTests:
    """Test memory-related stress scenarios."""
    
    def test_memory_leak_prevention(self):
        """Test that logger doesn't leak memory with many log entries."""
        config = VibeLoggerConfig(
            keep_logs_in_memory=True,
            max_memory_logs=100  # Small limit
        )
        logger = create_logger(config=config)
        
        # Generate many log entries
        for i in range(1000):
            logger.info("memory_test", f"Message {i}", context={"iteration": i})
        
        # Should only keep the last 100 entries
        assert len(logger.logs) == 100
        assert logger.logs[0].context["iteration"] == 900  # First kept entry
        assert logger.logs[-1].context["iteration"] == 999  # Last entry
    
    def test_no_memory_logging_performance(self):
        """Test performance when memory logging is disabled."""
        config = VibeLoggerConfig(keep_logs_in_memory=False)
        logger = create_logger(config=config)
        
        start_time = time.time()
        
        # Generate many log entries without storing in memory
        for i in range(1000):
            logger.info("perf_test", f"Message {i}")
        
        duration = time.time() - start_time
        
        # Should complete quickly and use no memory
        assert len(logger.logs) == 0
        assert duration < 1.0  # Should complete in under 1 second
    
    def test_extremely_deep_context_nesting(self):
        """Test handling of extremely deeply nested context objects."""
        logger = create_logger()
        
        # Create deeply nested structure
        deep_context = {"level": 0}
        current = deep_context
        for i in range(100):  # 100 levels deep
            current["nested"] = {"level": i + 1}
            current = current["nested"]
        
        # Should handle deep nesting without stack overflow
        entry = logger.info("deep_test", "Deep nesting test", context=deep_context)
        assert entry.context["level"] == 0


class TestSecurityEdgeCases:
    """Test security-related edge cases."""
    
    def test_sensitive_data_in_context(self):
        """Test handling of potentially sensitive data."""
        logger = create_logger()
        
        sensitive_context = {
            "password": "secret123",
            "api_key": "sk-1234567890abcdef",
            "credit_card": "4111-1111-1111-1111",
            "ssn": "123-45-6789",
            "email": "user@example.com",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
        
        # Currently logs sensitive data - this test documents current behavior
        entry = logger.info("security_test", "Sensitive data test", context=sensitive_context)
        
        # Note: In future versions, we should implement PII masking
        assert "password" in entry.context
        assert entry.context["password"] == "secret123"
        
        # TODO: Add PII masking functionality
    
    def test_log_injection_prevention(self):
        """Test prevention of log injection attacks."""
        logger = create_logger()
        
        # Attempt log injection through various fields
        malicious_inputs = [
            "Normal message\n{\"injected\": \"log entry\"}",
            "Message with\r\ncarriage returns",
            "Message with\ttabs\tand\tnewlines\n",
            "Message with null\x00byte",
            "Message with \x1b[31mANSI escape codes\x1b[0m"
        ]
        
        for malicious_input in malicious_inputs:
            entry = logger.info("injection_test", malicious_input)
            
            # Verify the message is stored as-is (not interpreted)
            assert entry.message == malicious_input
            
            # Verify JSON serialization is safe
            json_str = entry.to_json()
            parsed = json.loads(json_str)
            assert parsed["message"] == malicious_input


class TestCorrelationIdEdgeCases:
    """Test correlation ID edge cases."""
    
    def test_invalid_correlation_ids(self):
        """Test handling of invalid correlation IDs."""
        invalid_ids = [
            "",  # Empty string
            None,  # None value
            123,  # Integer
            [],  # List
            {},  # Dict
            "very-long-correlation-id-" + "x" * 1000  # Very long ID
        ]
        
        for invalid_id in invalid_ids:
            try:
                logger = create_logger(correlation_id=invalid_id)
                # Should either accept (and convert to string) or generate a valid ID
                assert isinstance(logger.correlation_id, str)
                assert len(logger.correlation_id) > 0
            except (TypeError, ValueError):
                # Acceptable to reject invalid IDs
                pass
    
    def test_correlation_id_uniqueness(self):
        """Test that correlation IDs are unique across loggers."""
        loggers = [create_logger() for _ in range(100)]
        correlation_ids = [logger.correlation_id for logger in loggers]
        
        # All correlation IDs should be unique
        assert len(set(correlation_ids)) == len(correlation_ids)
    
    def test_correlation_id_persistence(self):
        """Test that correlation ID persists across log entries."""
        correlation_id = "test-correlation-123"
        logger = create_logger(correlation_id=correlation_id)
        
        # Generate multiple log entries
        for i in range(10):
            entry = logger.info("persistence_test", f"Message {i}")
            assert entry.correlation_id == correlation_id


class TestConfigurationEdgeCases:
    """Test configuration edge cases."""
    
    def test_conflicting_configurations(self):
        """Test handling of conflicting configuration options."""
        # Test conflicting memory settings
        config = VibeLoggerConfig(
            keep_logs_in_memory=False,
            max_memory_logs=1000  # This should be ignored
        )
        logger = create_logger(config=config)
        
        # Generate logs
        for i in range(10):
            logger.info("config_test", f"Message {i}")
        
        # Should respect keep_logs_in_memory=False
        assert len(logger.logs) == 0
    
    def test_extreme_configuration_values(self):
        """Test handling of extreme configuration values."""
        extreme_configs = [
            VibeLoggerConfig(max_file_size_mb=0),  # Zero file size
            VibeLoggerConfig(max_file_size_mb=-1),  # Negative file size
            VibeLoggerConfig(max_memory_logs=0),  # Zero memory logs
            VibeLoggerConfig(max_memory_logs=-1),  # Negative memory logs
        ]
        
        for config in extreme_configs:
            try:
                logger = create_logger(config=config)
                logger.info("extreme_test", "Extreme config test")
                # Should handle gracefully
            except (ValueError, TypeError):
                # Acceptable to reject extreme values
                pass


class TestTimestampEdgeCases:
    """Test timestamp-related edge cases."""
    
    def test_timestamp_precision(self):
        """Test timestamp precision and ordering."""
        logger = create_logger()
        
        # Generate multiple entries quickly
        entries = []
        for i in range(100):
            entry = logger.info("timestamp_test", f"Message {i}")
            entries.append(entry)
        
        # Verify timestamps are ordered
        timestamps = [entry.timestamp for entry in entries]
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i-1], f"Timestamp order violation at index {i}"
    
    def test_timezone_consistency(self):
        """Test that all timestamps use UTC."""
        logger = create_logger()
        
        entry = logger.info("timezone_test", "UTC test")
        
        # Should end with Z (UTC indicator) or have +00:00
        assert entry.timestamp.endswith('Z') or '+00:00' in entry.timestamp
        
        # Should be parseable as ISO format
        from datetime import datetime
        parsed = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
        assert parsed.tzinfo is not None


if __name__ == "__main__":
    # Run edge case tests
    pytest.main([__file__, "-v"])