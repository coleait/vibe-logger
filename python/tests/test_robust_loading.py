"""
Test robust file loading functionality with corrupted data
"""

import json
import tempfile
from pathlib import Path
from vibelogger import create_logger

def test_robust_file_loading():
    """Test that file loading handles corrupted data gracefully"""
    
    # Create a temporary file with mixed valid and invalid log entries
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = f.name
        
        # Write mixed content: valid, invalid JSON, missing fields, etc.
        test_data = [
            # Valid entry
            '{"timestamp": "2025-07-07T10:00:00Z", "level": "INFO", "correlation_id": "test-1", "operation": "test_op", "message": "Valid message", "context": {}, "environment": {"python_version": "3.9", "os": "test", "platform": "test", "architecture": "test"}}',
            
            # Invalid JSON
            '{"timestamp": "2025-07-07T10:00:01Z", "level": "INFO", "invalid_json',
            
            # Missing required fields
            '{"timestamp": "2025-07-07T10:00:02Z", "level": "INFO"}',
            
            # Another valid entry
            '{"timestamp": "2025-07-07T10:00:03Z", "level": "ERROR", "correlation_id": "test-2", "operation": "test_op2", "message": "Another valid message", "context": {}, "environment": {"python_version": "3.9", "os": "test", "platform": "test", "architecture": "test"}}',
            
            # Empty line (should be skipped)
            '',
            
            # Invalid environment data
            '{"timestamp": "2025-07-07T10:00:04Z", "level": "WARNING", "correlation_id": "test-3", "operation": "test_op3", "message": "Invalid env", "context": {}, "environment": {"invalid": "data"}}',
            
            # Missing environment entirely
            '{"timestamp": "2025-07-07T10:00:05Z", "level": "DEBUG", "correlation_id": "test-4", "operation": "test_op4", "message": "No env", "context": {}}'
        ]
        
        for line in test_data:
            f.write(line + '\n')
    
    try:
        # Create logger and load the corrupted file
        logger = create_logger()
        
        # Capture the output to verify warnings
        import io
        import sys
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            logger.load_logs_from_file(log_file)
        
        output = captured_output.getvalue()
        
        # Should have loaded 2 completely valid entries + 2 with recovered environment
        assert len(logger.logs) == 4
        
        # Verify the valid entries were loaded correctly
        valid_ops = [log.operation for log in logger.logs]
        assert 'test_op' in valid_ops
        assert 'test_op2' in valid_ops
        assert 'test_op3' in valid_ops  # Should be recovered with default environment
        assert 'test_op4' in valid_ops  # Should be recovered with default environment
        
        # Check that warnings were printed for invalid data
        assert 'Warning:' in output or 'Loaded' in output
        
        print("✅ Robust file loading test passed")
        
    finally:
        # Cleanup
        Path(log_file).unlink(missing_ok=True)


def test_caller_info_robustness():
    """Test that caller info detection works reliably"""
    
    def nested_function():
        def deeper_function():
            logger = create_logger()
            return logger.info("caller_test", "Testing caller detection")
        return deeper_function()
    
    entry = nested_function()
    
    # Should detect the correct source (not internal logger functions)
    assert entry.source
    assert 'test_robust_loading.py' in entry.source
    assert 'deeper_function' in entry.source
    
    print("✅ Caller info robustness test passed")


def test_dry_principle_implementation():
    """Test that the DRY principle refactoring works correctly"""
    
    logger = create_logger()
    
    # Test regular logging
    entry1 = logger.info("dry_test", "Regular log message")
    
    # Test exception logging
    try:
        raise ValueError("Test exception")
    except Exception as e:
        entry2 = logger.log_exception("dry_test", e)
    
    # Both should be in logs (memory)
    assert len(logger.logs) == 2
    assert entry1.operation == "dry_test"
    assert entry2.operation == "dry_test"
    assert entry1.level == "INFO"
    assert entry2.level == "ERROR"
    
    print("✅ DRY principle test passed")


if __name__ == "__main__":
    test_robust_file_loading()
    test_caller_info_robustness()
    test_dry_principle_implementation()
    print("🎉 All robustness tests passed!")