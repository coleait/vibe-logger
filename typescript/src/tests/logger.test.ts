/**
 * Basic tests for VibeCoding Logger - TypeScript Implementation
 * 
 * Mirrors the Python test structure but adapted for Node.js testing patterns
 */

import { test, describe } from 'node:test';
import { strict as assert } from 'node:assert';
import { tmpdir } from 'os';
import { join } from 'path';
import { unlink } from 'fs/promises';

import { 
  VibeLogger, 
  createLogger, 
  createFileLogger,
  LogLevel,
  type VibeLoggerConfig 
} from '../index.js';

describe('VibeLogger Basic Tests', () => {
  test('should create logger with default config', async () => {
    const logger = createLogger();
    assert.ok(logger instanceof VibeLogger);
    
    const config = logger.getConfig();
    assert.ok(config.correlationId);
    assert.equal(config.autoSave, true);
    assert.equal(config.keepLogsInMemory, true);
  });

  test('should log basic info message', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    const entry = await logger.info('test_operation', 'Test message', {
      context: { key: 'value' },
      humanNote: 'Test note'
    });

    assert.equal(entry.level, LogLevel.INFO);
    assert.equal(entry.operation, 'test_operation');
    assert.equal(entry.message, 'Test message');
    assert.equal(entry.context.key, 'value');
    assert.equal(entry.human_note, 'Test note');
    assert.ok(entry.timestamp);
    assert.ok(entry.correlation_id);
  });

  test('should handle different log levels', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    const debugEntry = await logger.debug('debug_op', 'Debug message');
    const infoEntry = await logger.info('info_op', 'Info message');
    const warningEntry = await logger.warning('warning_op', 'Warning message');
    const errorEntry = await logger.error('error_op', 'Error message');
    const criticalEntry = await logger.critical('critical_op', 'Critical message');

    assert.equal(debugEntry.level, LogLevel.DEBUG);
    assert.equal(infoEntry.level, LogLevel.INFO);
    assert.equal(warningEntry.level, LogLevel.WARNING);
    assert.equal(errorEntry.level, LogLevel.ERROR);
    assert.equal(criticalEntry.level, LogLevel.CRITICAL);

    // Error and critical should have stack traces
    assert.ok(errorEntry.stack_trace);
    assert.ok(criticalEntry.stack_trace);
  });

  test('should log exceptions properly', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    const testError = new Error('Test error message');
    const entry = await logger.logException('test_exception', testError, {
      context: { errorType: 'test' },
      aiTodo: 'Fix this error'
    });

    assert.equal(entry.level, LogLevel.ERROR);
    assert.equal(entry.operation, 'test_exception');
    assert.ok(entry.message.includes('Error: Test error message'));
    assert.equal(entry.context.errorType, 'test');
    assert.equal(entry.ai_todo, 'Fix this error');
    assert.ok(entry.stack_trace);
    assert.equal(entry.context.error_type, 'Error');
  });

  test('should handle non-Error exceptions', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    // Test string throw
    const stringEntry = await logger.logException('string_error', 'String error');
    assert.ok(stringEntry.message.includes('StringError: String error'));

    // Test number throw
    const numberEntry = await logger.logException('number_error', 42);
    assert.ok(numberEntry.message.includes('UnknownError: 42'));

    // Test object throw
    const objectEntry = await logger.logException('object_error', { custom: 'error' });
    assert.ok(objectEntry.message.includes('ObjectError'));
  });

  test('should maintain correlation ID across logs', async () => {
    const correlationId = 'test-correlation-123';
    const logger = createLogger({
      correlationId,
      keepLogsInMemory: true,
      autoSave: false
    });

    const entry1 = await logger.info('op1', 'Message 1');
    const entry2 = await logger.error('op2', 'Message 2');

    assert.equal(entry1.correlation_id, correlationId);
    assert.equal(entry2.correlation_id, correlationId);
    assert.equal(logger.getCorrelationId(), correlationId);
  });

  test('should get logs for AI', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    await logger.info('operation1', 'Message 1');
    await logger.error('operation2', 'Message 2');

    const aiLogs = await logger.getLogsForAI();
    const parsed = JSON.parse(aiLogs);

    assert.equal(parsed.length, 2);
    assert.equal(parsed[0].operation, 'operation1');
    assert.equal(parsed[1].operation, 'operation2');
  });

  test('should filter logs by operation', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    await logger.info('user_login', 'User logged in');
    await logger.info('user_logout', 'User logged out');
    await logger.info('data_fetch', 'Data fetched');

    const userLogs = await logger.getLogsForAI('user_');
    const parsed = JSON.parse(userLogs);

    assert.equal(parsed.length, 2);
    assert.ok(parsed.every((log: any) => log.operation.startsWith('user_')));
  });

  test('should manage memory limits', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      maxMemoryLogs: 3,
      autoSave: false
    });

    // Add more logs than the limit
    await logger.info('op1', 'Message 1');
    await logger.info('op2', 'Message 2');
    await logger.info('op3', 'Message 3');
    await logger.info('op4', 'Message 4');
    await logger.info('op5', 'Message 5');

    const logs = await logger.getLogs();
    assert.equal(logs.length, 3);
    
    // Should keep the most recent logs
    assert.equal(logs[0].operation, 'op3');
    assert.equal(logs[1].operation, 'op4');
    assert.equal(logs[2].operation, 'op5');
  });

  test('should clear logs', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    await logger.info('op1', 'Message 1');
    await logger.info('op2', 'Message 2');

    let logs = await logger.getLogs();
    assert.equal(logs.length, 2);

    await logger.clearLogs();
    logs = await logger.getLogs();
    assert.equal(logs.length, 0);
  });

  test('should include environment information', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    const entry = await logger.info('env_test', 'Environment test');

    assert.ok(entry.environment);
    assert.ok(entry.environment.node_version);
    assert.ok(entry.environment.os);
    assert.ok(entry.environment.platform);
    assert.ok(entry.environment.architecture);
    assert.equal(entry.environment.runtime, 'node');
  });
});

describe('VibeLogger File Operations', () => {
  test('should save logs to file', async () => {
    const logFile = join(tmpdir(), `test-${Date.now()}.log`);
    
    try {
      const logger = createLogger({
        logFile,
        autoSave: true,
        keepLogsInMemory: false
      });

      await logger.info('file_test', 'Test file logging');
      
      // Give file operations time to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      // File should exist and contain the log
      const { FileSystemManager } = await import('../utils/fileSystem.js');
      const fileResult = await FileSystemManager.readFile(logFile);
      
      assert.ok(fileResult.success);
      assert.ok(fileResult.content);
      assert.ok(fileResult.content.includes('file_test'));
      assert.ok(fileResult.content.includes('Test file logging'));
    } finally {
      // Cleanup
      try {
        await unlink(logFile);
      } catch {
        // Ignore cleanup errors
      }
    }
  });

  test('should create file logger for project', async () => {
    const logger = createFileLogger('test-project');
    
    assert.ok(logger instanceof VibeLogger);
    
    const config = logger.getConfig();
    assert.ok(config.logFile);
    assert.ok(config.logFile.includes('test-project'));
    assert.equal(config.autoSave, true);
  });
});

describe('VibeLogger Configuration', () => {
  test('should validate configuration', async () => {
    // Valid configuration should work
    const validLogger = createLogger({
      maxFileSizeMb: 10,
      maxMemoryLogs: 100
    });
    assert.ok(validLogger);

    // Invalid configuration should throw
    assert.throws(() => {
      createLogger({
        maxFileSizeMb: -1  // Invalid
      });
    });

    assert.throws(() => {
      createLogger({
        maxMemoryLogs: -1  // Invalid
      });
    });
  });

  test('should handle memory-only logging', async () => {
    const logger = createLogger({
      keepLogsInMemory: false,
      autoSave: false
    });

    await logger.info('memory_test', 'This should not be stored');
    
    const logs = await logger.getLogs();
    assert.equal(logs.length, 0);
  });
});