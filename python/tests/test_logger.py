import json
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from vibelogger import (
    VibeLogger,
    LogLevel,
    VibeLoggerConfig,
    create_logger,
    create_file_logger,
    create_env_logger
)


class TestVibeLogger:
    def test_basic_logging(self):
        logger = create_logger()
        
        entry = logger.info(
            operation="test_operation",
            message="Test message",
            context={"key": "value"}
        )
        
        assert entry.level == "INFO"
        assert entry.operation == "test_operation"
        assert entry.message == "Test message"
        assert entry.context == {"key": "value"}
        assert len(logger.logs) == 1

    def test_log_levels(self):
        logger = create_logger()
        
        logger.debug("op", "debug msg")
        logger.info("op", "info msg")
        logger.warning("op", "warning msg")
        logger.error("op", "error msg")
        logger.critical("op", "critical msg")
        
        assert len(logger.logs) == 5
        assert logger.logs[0].level == "DEBUG"
        assert logger.logs[1].level == "INFO"
        assert logger.logs[2].level == "WARNING"
        assert logger.logs[3].level == "ERROR"
        assert logger.logs[4].level == "CRITICAL"

    def test_exception_logging(self):
        logger = create_logger()
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            entry = logger.log_exception(
                operation="test_exception",
                exception=e,
                context={"error_context": "test"}
            )
        
        assert entry.level == "ERROR"
        assert "ValueError: Test error" in entry.message
        assert entry.stack_trace is not None
        assert "ValueError" in entry.stack_trace

    def test_file_logging(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            config = VibeLoggerConfig(log_file=log_file, auto_save=True)
            logger = create_logger(config=config)
            
            logger.info("test_op", "Test message")
            
            # Check file exists and contains log
            assert Path(log_file).exists()
            with open(log_file, 'r') as f:
                content = f.read()
                assert "test_op" in content
                assert "Test message" in content
        finally:
            Path(log_file).unlink(missing_ok=True)

    def test_memory_management(self):
        config = VibeLoggerConfig(
            keep_logs_in_memory=True,
            max_memory_logs=3
        )
        logger = create_logger(config=config)
        
        # Add more logs than the limit
        for i in range(5):
            logger.info("test_op", f"Message {i}")
        
        # Should only keep the last 3 logs
        assert len(logger.logs) == 3
        assert logger.logs[0].message == "Message 2"
        assert logger.logs[2].message == "Message 4"

    def test_no_memory_logging(self):
        config = VibeLoggerConfig(keep_logs_in_memory=False)
        logger = create_logger(config=config)
        
        logger.info("test_op", "Test message")
        
        # Should not store logs in memory
        assert len(logger.logs) == 0

    def test_thread_safety(self):
        logger = create_logger()
        results = []
        
        def worker(worker_id):
            for i in range(10):
                logger.info("worker", f"Worker {worker_id} - Message {i}")
                results.append(f"{worker_id}-{i}")
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 50 total logs (5 workers * 10 messages each)
        assert len(logger.logs) == 50
        assert len(results) == 50

    def test_correlation_id(self):
        correlation_id = "test-correlation-123"
        logger = create_logger(correlation_id=correlation_id)
        
        entry = logger.info("test_op", "Test message")
        
        assert entry.correlation_id == correlation_id
        assert logger.correlation_id == correlation_id

    def test_human_annotations(self):
        logger = create_logger()
        
        entry = logger.info(
            operation="test_op",
            message="Test message",
            human_note="This is a note for AI",
            ai_todo="Please analyze this specific issue"
        )
        
        assert entry.human_note == "This is a note for AI"
        assert entry.ai_todo == "Please analyze this specific issue"

    def test_get_logs_for_ai(self):
        logger = create_logger()
        
        logger.info("operation1", "Message 1")
        logger.error("operation2", "Message 2")
        
        ai_logs = logger.get_logs_for_ai()
        parsed = json.loads(ai_logs)
        
        assert len(parsed) == 2
        assert parsed[0]["operation"] == "operation1"
        assert parsed[1]["operation"] == "operation2"

    def test_operation_filter(self):
        logger = create_logger()
        
        logger.info("fetch_user", "Message 1")
        logger.info("save_data", "Message 2")
        logger.info("fetch_user", "Message 3")
        
        filtered = logger.get_logs_for_ai(operation_filter="fetch_user")
        parsed = json.loads(filtered)
        
        assert len(parsed) == 2
        assert all("fetch_user" in log["operation"] for log in parsed)

    def test_environment_variables(self):
        with patch.dict('os.environ', {
            'VIBE_LOG_FILE': '/tmp/test.log',
            'VIBE_AUTO_SAVE': 'false',
            'VIBE_MAX_FILE_SIZE_MB': '25'
        }):
            logger = create_env_logger()
            
            assert logger.config.log_file == '/tmp/test.log'
            assert logger.config.auto_save is False
            assert logger.config.max_file_size_mb == 25

    def test_create_file_logger(self):
        logger = create_file_logger("test_project")
        
        assert logger.log_file is not None
        assert "test_project" in logger.log_file
        assert "vibe_" in logger.log_file
        assert logger.log_file.endswith(".log")

    def test_utc_timestamp(self):
        logger = create_logger()
        entry = logger.info("test_op", "Test message")
        
        # Check that timestamp ends with 'Z' or '+00:00' (UTC indicators)
        assert entry.timestamp.endswith('Z') or '+00:00' in entry.timestamp

    def test_clear_logs(self):
        logger = create_logger()
        
        logger.info("test_op", "Message 1")
        logger.info("test_op", "Message 2")
        assert len(logger.logs) == 2
        
        logger.clear_logs()
        assert len(logger.logs) == 0


class TestVibeLoggerConfig:
    def test_default_config(self):
        config = VibeLoggerConfig()
        
        assert config.auto_save is True
        assert config.max_file_size_mb == 10
        assert config.create_dirs is True
        assert config.keep_logs_in_memory is True
        assert config.max_memory_logs == 1000

    def test_from_env_defaults(self):
        config = VibeLoggerConfig.from_env()
        
        # Should use defaults when env vars not set
        assert config.auto_save is True
        assert config.max_file_size_mb == 10
        assert config.log_level == "INFO"

    def test_default_file_config(self):
        config = VibeLoggerConfig.default_file_config("test_project")
        
        assert config.log_file is not None
        assert "test_project" in config.log_file
        assert config.auto_save is True