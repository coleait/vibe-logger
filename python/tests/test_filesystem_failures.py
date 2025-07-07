"""
Tests for file system failure scenarios that real users encounter.
Focus on graceful degradation and error recovery.
"""

import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

from vibelogger import create_file_logger, create_logger, VibeLoggerConfig


class TestFileSystemFailures:
    """Test file system failure scenarios that break real usage."""
    
    def test_read_only_directory(self):
        """Test behavior when log directory is read-only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "readonly_logs"
            log_dir.mkdir()
            
            # Make directory read-only
            os.chmod(log_dir, 0o444)
            
            try:
                config = VibeLoggerConfig(
                    log_file=log_dir / "test.log",
                    auto_save=True
                )
                logger = create_logger(config=config)
                
                # Should not crash, should store in memory
                logger.info("test", "This should work despite read-only dir")
                
                # Verify log is in memory
                assert len(logger.logs) == 1
                assert logger.logs[0].message == "This should work despite read-only dir"
                
            finally:
                # Restore permissions for cleanup
                os.chmod(log_dir, 0o755)
    
    def test_no_permission_to_create_directory(self):
        """Test when user can't create the log directory."""
        # Try to create log in root directory (should fail on most systems)
        config = VibeLoggerConfig(
            log_file="/root/impossible/test.log",
            auto_save=True
        )
        
        logger = create_logger(config=config)
        
        # Should not crash, should store in memory
        logger.info("test", "Should work without file")
        
        assert len(logger.logs) == 1
        assert logger.logs[0].message == "Should work without file"
    
    def test_disk_full_simulation(self):
        """Simulate disk full during write operation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            config = VibeLoggerConfig(
                log_file=log_file,
                auto_save=True
            )
            logger = create_logger(config=config)
            
            # Mock file write to raise OSError (disk full)
            original_write = Path.write_text
            def mock_write_disk_full(self, *args, **kwargs):
                raise OSError(28, "No space left on device")
            
            with patch.object(Path, 'write_text', mock_write_disk_full):
                # Should not crash
                logger.info("test", "This write should fail gracefully")
                
                # Should still be in memory
                assert len(logger.logs) == 1
                assert logger.logs[0].message == "This write should fail gracefully"
    
    def test_file_locked_by_another_process(self):
        """Test behavior when log file is locked by another process."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "locked.log"
            
            # Create and lock the file
            with open(log_file, 'w') as f:
                f.write("locked by another process\n")
                
                config = VibeLoggerConfig(
                    log_file=log_file,
                    auto_save=True
                )
                logger = create_logger(config=config)
                
                # Should handle gracefully (exact behavior may vary by OS)
                logger.info("test", "Should handle locked file")
                
                # Should be in memory at minimum
                assert len(logger.logs) == 1
    
    def test_corrupted_existing_log_file(self):
        """Test loading from a corrupted existing log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "corrupted.log"
            
            # Create corrupted log file
            log_file.write_text("this is not valid JSON\n{incomplete json\n")
            
            config = VibeLoggerConfig(
                log_file=log_file,
                auto_save=True
            )
            logger = create_logger(config=config)
            
            # Should not crash on creation
            logger.info("test", "Should work despite corrupted file")
            
            # Should be able to write new logs
            assert len(logger.logs) == 1
    
    def test_log_file_becomes_directory(self):
        """Test when log file path is occupied by a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "shouldbefile"
            
            # Create directory where file should be
            log_path.mkdir()
            
            config = VibeLoggerConfig(
                log_file=log_path,  # This is a directory!
                auto_save=True
            )
            logger = create_logger(config=config)
            
            # Should not crash
            logger.info("test", "Should handle directory collision")
            
            assert len(logger.logs) == 1
    
    def test_extremely_long_file_path(self):
        """Test with extremely long file paths that exceed OS limits."""
        # Create very long path (over 255 chars typically)
        long_name = "a" * 300
        long_path = f"/tmp/{long_name}/{long_name}/{long_name}.log"
        
        config = VibeLoggerConfig(
            log_file=long_path,
            auto_save=True
        )
        logger = create_logger(config=config)
        
        # Should not crash
        logger.info("test", "Should handle long paths gracefully")
        
        assert len(logger.logs) == 1
    
    def test_special_characters_in_path(self):
        """Test paths with special characters that might break file systems."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Special characters that might cause issues
            special_name = "log<>:|?*\".log"
            log_file = Path(temp_dir) / special_name
            
            config = VibeLoggerConfig(
                log_file=log_file,
                auto_save=True
            )
            logger = create_logger(config=config)
            
            # Should handle gracefully
            logger.info("test", "Special characters in path")
            
            assert len(logger.logs) == 1
    
    def test_network_drive_unavailable(self):
        """Test when log file is on an unavailable network drive."""
        # Simulate network drive path
        network_path = Path("//nonexistent-server/share/logs/test.log")
        
        config = VibeLoggerConfig(
            log_file=network_path,
            auto_save=True
        )
        logger = create_logger(config=config)
        
        # Should not crash
        logger.info("test", "Network drive unavailable")
        
        assert len(logger.logs) == 1
    
    def test_file_system_full_during_rotation(self):
        """Test disk full during log rotation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "rotation_test.log"
            
            config = VibeLoggerConfig(
                log_file=log_file,
                max_file_size_mb=0.001,  # Very small to force rotation
                auto_save=True
            )
            logger = create_logger(config=config)
            
            # Fill up the log to trigger rotation
            for i in range(10):
                logger.info("test", f"Large message {i} " + "x" * 100)
            
            # Mock rotation to fail
            with patch('shutil.move', side_effect=OSError(28, "No space left")):
                # Should not crash during rotation failure
                logger.info("test", "After rotation failure")
                
                assert len(logger.logs) > 0


class TestConcurrentFileAccess:
    """Test concurrent access scenarios that break in real usage."""
    
    def test_multiple_loggers_same_file(self):
        """Test multiple logger instances writing to same file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "shared.log"
            
            def create_and_log(worker_id):
                config = VibeLoggerConfig(
                    log_file=log_file,
                    auto_save=True
                )
                logger = create_logger(config=config)
                
                for i in range(5):
                    logger.info("test", f"Worker {worker_id} message {i}")
                    time.sleep(0.01)  # Small delay
            
            # Start multiple threads
            threads = []
            for i in range(3):
                t = threading.Thread(target=create_and_log, args=(i,))
                threads.append(t)
                t.start()
            
            # Wait for completion
            for t in threads:
                t.join()
            
            # File should exist and be readable
            if log_file.exists():
                content = log_file.read_text()
                # Should have some valid content
                assert len(content) > 0
    
    def test_logger_file_deleted_during_operation(self):
        """Test when log file is deleted while logger is active."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "deleteme.log"
            
            config = VibeLoggerConfig(
                log_file=log_file,
                auto_save=True
            )
            logger = create_logger(config=config)
            
            # Write initial log
            logger.info("test", "Before deletion")
            
            # Delete the log file externally
            if log_file.exists():
                log_file.unlink()
            
            # Should handle gracefully
            logger.info("test", "After deletion")
            
            assert len(logger.logs) == 2


class TestMemoryConstraints:
    """Test memory-related failures that affect real users."""
    
    def test_extremely_large_context_object(self):
        """Test logging extremely large context objects."""
        logger = create_logger()
        
        # Create very large context
        large_context = {
            "massive_list": list(range(10000)),
            "big_string": "x" * 100000,
            "nested": {f"key_{i}": f"value_{i}" * 1000 for i in range(100)}
        }
        
        # Should not crash or hang
        logger.info("test", "Large context test", context=large_context)
        
        assert len(logger.logs) == 1
        # Context should be preserved (or gracefully handled)
        assert logger.logs[0].context is not None
    
    def test_memory_exhaustion_prevention(self):
        """Test that logger prevents memory exhaustion."""
        config = VibeLoggerConfig(
            max_memory_logs=10,  # Very small limit
            keep_logs_in_memory=True
        )
        logger = create_logger(config=config)
        
        # Add more logs than memory limit
        for i in range(50):
            logger.info("test", f"Message {i}")
        
        # Should not exceed memory limit
        assert len(logger.logs) <= 10
        
        # Should keep most recent logs
        assert logger.logs[-1].message == "Message 49"
    
    def test_circular_reference_in_context(self):
        """Test logging objects with circular references."""
        logger = create_logger()
        
        # Create circular reference
        obj_a = {"name": "A"}
        obj_b = {"name": "B", "ref": obj_a}
        obj_a["ref"] = obj_b
        
        # Should handle gracefully without infinite recursion
        logger.info("test", "Circular reference test", context={"circular": obj_a})
        
        assert len(logger.logs) == 1