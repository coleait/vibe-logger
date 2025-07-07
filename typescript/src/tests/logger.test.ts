/**
 * Comprehensive test suite for VibeCoding Logger TypeScript implementation
 * 
 * This test suite mirrors the Python test structure to ensure cross-language
 * compatibility and feature parity.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';
import { tmpdir } from 'os';
import { join } from 'path';
import { writeFileSync, unlinkSync, existsSync, readFileSync, mkdtempSync } from 'fs';
import { rmSync } from 'fs';

import {
  createLogger,
  createFileLogger,
  createEnvLogger,
  VibeLogger,
  LogLevel,
  type VibeLoggerConfig,
  type LogEntry
} from '../index.js';

describe('VibeLogger Core Tests', () => {
  test('basic logging functionality', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    const entry = await logger.info('test_operation', 'Test message', {
      context: { key: 'value' }
    });

    assert.strictEqual(entry.level, 'INFO');
    assert.strictEqual(entry.operation, 'test_operation');
    assert.strictEqual(entry.message, 'Test message');
    assert.deepStrictEqual(entry.context, { key: 'value' });
    
    const logs = await logger.getLogs();
    assert.strictEqual(logs.length, 1);
  });

  test('all log levels work correctly', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    await logger.debug('op', 'debug msg');
    await logger.info('op', 'info msg');
    await logger.warning('op', 'warning msg');
    await logger.error('op', 'error msg');
    await logger.critical('op', 'critical msg');

    const logs = await logger.getLogs();
    assert.strictEqual(logs.length, 5);
    assert.strictEqual(logs[0]?.level, 'DEBUG');
    assert.strictEqual(logs[1]?.level, 'INFO');
    assert.strictEqual(logs[2]?.level, 'WARNING');
    assert.strictEqual(logs[3]?.level, 'ERROR');
    assert.strictEqual(logs[4]?.level, 'CRITICAL');
  });

  test('exception logging', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    const testError = new Error('Test error');
    const entry = await logger.logException('test_exception', testError, {
      context: { error_context: 'test' }
    });

    assert.strictEqual(entry.level, 'ERROR');
    assert(entry.message.includes('Error: Test error'));
    assert(entry.stack_trace !== undefined);
    assert(entry.stack_trace!.includes('Error'));
    
    // Check that the original context is preserved
    assert.strictEqual(entry.context.error_context, 'test');
    // The logException method adds error details to context
    assert(entry.context.error_type !== undefined);
    assert(entry.context.original_error !== undefined);
  });

  test('exception logging with different error types', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    // Test different error types
    const errors = [
      new Error('Standard Error'),
      'String error',
      42,
      { customError: 'Object error' },
      null,
      undefined
    ];

    for (const [index, error] of errors.entries()) {
      await logger.logException(`error_type_${index}`, error);
    }

    const logs = await logger.getLogs();
    assert.strictEqual(logs.length, 6);
    
    // Verify they all have ERROR level
    for (const log of logs) {
      assert.strictEqual(log.level, 'ERROR');
    }
  });

  test('file logging functionality', async () => {
    const tempDir = mkdtempSync(join(tmpdir(), 'vibe-logger-test-'));
    const logFile = join(tempDir, 'test.log');

    try {
      const logger = createLogger({
        logFile,
        autoSave: true,
        keepLogsInMemory: true,
        createDirs: true
      });

      await logger.info('test_op', 'Test message');

      // Wait a bit for file operations
      await new Promise(resolve => setTimeout(resolve, 100));

      assert(existsSync(logFile));
      const content = readFileSync(logFile, 'utf8');
      assert(content.includes('test_op'));
      assert(content.includes('Test message'));
    } finally {
      rmSync(tempDir, { recursive: true, force: true });
    }
  });

  test('memory management with limits', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      maxMemoryLogs: 3,
      autoSave: false
    });

    // Add more logs than the limit
    for (let i = 0; i < 5; i++) {
      await logger.info('test_op', `Message ${i}`);
    }

    const logs = await logger.getLogs();
    assert.strictEqual(logs.length, 3);
    assert.strictEqual(logs[0]?.message, 'Message 2');
    assert.strictEqual(logs[2]?.message, 'Message 4');
  });

  test('memory disabled logging', async () => {
    const logger = createLogger({
      keepLogsInMemory: false,
      autoSave: false
    });

    await logger.info('test_op', 'Test message');

    const logs = await logger.getLogs();
    assert.strictEqual(logs.length, 0);
  });

  test('correlation ID functionality', async () => {
    const correlationId = 'test-correlation-123';
    const logger = createLogger({
      correlationId,
      keepLogsInMemory: true,
      autoSave: false
    });

    const entry = await logger.info('test_op', 'Test message');

    assert.strictEqual(entry.correlation_id, correlationId);
    assert.strictEqual(logger.getCorrelationId(), correlationId);
  });

  test('human annotations', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    const entry = await logger.info('test_op', 'Test message', {
      humanNote: 'This is a note for AI',
      aiTodo: 'Please analyze this specific issue'
    });

    assert.strictEqual(entry.human_note, 'This is a note for AI');
    assert.strictEqual(entry.ai_todo, 'Please analyze this specific issue');
  });

  test('get logs for AI analysis', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    await logger.info('operation1', 'Message 1');
    await logger.error('operation2', 'Message 2');

    const aiLogs = await logger.getLogsForAI();
    const parsed = JSON.parse(aiLogs);

    assert.strictEqual(parsed.length, 2);
    assert.strictEqual(parsed[0].operation, 'operation1');
    assert.strictEqual(parsed[1].operation, 'operation2');
  });

  test('operation filter for AI logs', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    await logger.info('fetch_user', 'Message 1');
    await logger.info('save_data', 'Message 2');
    await logger.info('fetch_user', 'Message 3');

    const filtered = await logger.getLogsForAI('fetch_user');
    const parsed = JSON.parse(filtered);

    assert.strictEqual(parsed.length, 2);
    assert(parsed.every((log: any) => log.operation.includes('fetch_user')));
  });

  test('UTC timestamp format', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    const entry = await logger.info('test_op', 'Test message');

    // Check that timestamp ends with 'Z' or contains '+00:00' (UTC indicators)
    assert(entry.timestamp.endsWith('Z') || entry.timestamp.includes('+00:00'));
  });

  test('clear logs functionality', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    await logger.info('test_op', 'Message 1');
    await logger.info('test_op', 'Message 2');
    
    let logs = await logger.getLogs();
    assert.strictEqual(logs.length, 2);

    await logger.clearLogs();
    logs = await logger.getLogs();
    assert.strictEqual(logs.length, 0);
  });
});

describe('Logger Configuration Tests', () => {
  test('default configuration values', () => {
    const logger = createLogger();
    
    // Test that logger was created with reasonable defaults
    assert(typeof logger.getCorrelationId() === 'string');
    assert(logger.getCorrelationId().length > 0);
  });

  test('environment variable configuration', () => {
    // Set environment variables
    process.env.VIBE_LOG_FILE = '/tmp/test.log';
    process.env.VIBE_AUTO_SAVE = 'false';
    process.env.VIBE_MAX_FILE_SIZE_MB = '25';
    process.env.VIBE_CORRELATION_ID = 'env-test-id';

    try {
      const logger = createEnvLogger();
      
      assert.strictEqual(logger.getCorrelationId(), 'env-test-id');
      // Additional config tests would require accessing internal config
    } finally {
      // Clean up environment variables
      delete process.env.VIBE_LOG_FILE;
      delete process.env.VIBE_AUTO_SAVE;
      delete process.env.VIBE_MAX_FILE_SIZE_MB;
      delete process.env.VIBE_CORRELATION_ID;
    }
  });

  test('file logger creation', () => {
    const logger = createFileLogger('test_project');
    
    // Verify that correlation ID was generated
    assert(typeof logger.getCorrelationId() === 'string');
    assert(logger.getCorrelationId().length > 0);
  });
});

describe('Concurrency and Thread Safety Tests', () => {
  test('concurrent logging operations', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false,
      maxMemoryLogs: 1000
    });

    const promises: Promise<LogEntry>[] = [];
    const workerCount = 5;
    const messagesPerWorker = 10;

    // Create concurrent logging operations
    for (let workerId = 0; workerId < workerCount; workerId++) {
      for (let i = 0; i < messagesPerWorker; i++) {
        promises.push(
          logger.info(`worker_${workerId}`, `Message ${i}`, {
            context: { worker: workerId, iteration: i }
          })
        );
      }
    }

    // Wait for all operations to complete
    await Promise.all(promises);

    const logs = await logger.getLogs();
    assert.strictEqual(logs.length, workerCount * messagesPerWorker);

    // Verify all worker IDs are represented
    const workerIds = new Set();
    for (const log of logs) {
      workerIds.add(log.context.worker);
    }
    assert.strictEqual(workerIds.size, workerCount);
  });

  test('concurrent file operations', async () => {
    const tempDir = mkdtempSync(join(tmpdir(), 'vibe-logger-concurrent-'));
    const logFile = join(tempDir, 'concurrent.log');

    try {
      const logger = createLogger({
        logFile,
        autoSave: true,
        keepLogsInMemory: false,
        createDirs: true
      });

      const promises: Promise<LogEntry>[] = [];
      
      // Create concurrent file write operations
      for (let i = 0; i < 20; i++) {
        promises.push(
          logger.info('concurrent_test', `Concurrent message ${i}`)
        );
      }

      await Promise.all(promises);

      // Wait for file operations to complete
      await new Promise(resolve => setTimeout(resolve, 200));

      assert(existsSync(logFile));
      const content = readFileSync(logFile, 'utf8');
      const lines = content.trim().split('\n').filter(line => line.length > 0);
      assert.strictEqual(lines.length, 20);
    } finally {
      rmSync(tempDir, { recursive: true, force: true });
    }
  });
});

describe('Error Handling and Edge Cases', () => {
  test('invalid file path handling', async () => {
    const logger = createLogger({
      logFile: '/invalid/path/file.log',
      autoSave: true,
      createDirs: false,
      keepLogsInMemory: true
    });

    // Should not throw error even with invalid file path
    const entry = await logger.info('test', 'Should not crash on file error');
    
    assert(entry !== undefined);
    assert.strictEqual(entry.operation, 'test');
  });

  test('malformed context handling', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    // Test with various problematic context data
    const problematicContexts = [
      { function: () => 'not serializable' },
      { large_data: 'x'.repeat(100000) },
      { nested: { very: { deep: { nesting: { structure: 'value' } } } } },
      { unicode: '🚀🎉💻🔥' },
      { none_value: null },
      { empty_dict: {} },
      { empty_list: [] },
    ];

    for (const [i, context] of problematicContexts.entries()) {
      try {
        const entry = await logger.info(`context_test_${i}`, 'Testing problematic context', {
          context
        });
        assert(entry !== undefined);
      } catch (error) {
        // Some contexts might fail, but shouldn't crash the logger
        console.warn(`Context ${i} failed (acceptable):`, error);
      }
    }
  });

  test('correlation ID edge cases', async () => {
    // Test with custom correlation ID
    const customId = 'custom-test-id-123';
    const logger1 = createLogger({
      correlationId: customId,
      keepLogsInMemory: true,
      autoSave: false
    });
    assert.strictEqual(logger1.getCorrelationId(), customId);

    // Test with empty correlation ID (should generate one)
    const logger2 = createLogger({
      correlationId: '',
      keepLogsInMemory: true,
      autoSave: false
    });
    assert(logger2.getCorrelationId() !== '');
    assert(logger2.getCorrelationId().length > 0);

    // Test unique generation
    const logger3 = createLogger();
    const logger4 = createLogger();
    assert(logger3.getCorrelationId() !== logger4.getCorrelationId());
  });

  test('environment info collection', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    const entry = await logger.info('env_test', 'Testing environment info');

    assert(entry.environment);
    assert(typeof entry.environment.node_version === 'string');
    assert(typeof entry.environment.os === 'string');
    assert(typeof entry.environment.platform === 'string');
    assert(typeof entry.environment.architecture === 'string');
    assert(typeof entry.environment.runtime === 'string');
  });
});

describe('Performance and Memory Tests', () => {
  test('memory efficiency with large log volumes', async () => {
    const logger = createLogger({
      maxMemoryLogs: 100,
      keepLogsInMemory: true,
      autoSave: false
    });

    // Generate many logs with varying sizes
    for (let i = 0; i < 500; i++) {
      const context = { 
        iteration: i, 
        data: 'x'.repeat(i % 100) 
      };
      await logger.info('memory_efficiency_test', `Log ${i}`, { context });
    }

    const logs = await logger.getLogs();
    assert.strictEqual(logs.length, 100);

    // Should keep the most recent logs
    assert.strictEqual(logs[logs.length - 1]?.context.iteration, 499);
    assert.strictEqual(logs[0]?.context.iteration, 400);
  });

  test('logging performance', async () => {
    const logger = createLogger({
      keepLogsInMemory: true,
      autoSave: false
    });

    const startTime = Date.now();
    
    // Measure time for many calls
    const promises = [];
    for (let i = 0; i < 100; i++) {
      promises.push(logger.info('perf_test', `Message ${i}`));
    }
    await Promise.all(promises);
    
    const duration = Date.now() - startTime;

    // Should complete 100 logs in reasonable time (less than 1 second)
    assert(duration < 1000);

    const logs = await logger.getLogs();
    assert.strictEqual(logs.length, 100);

    // All entries should have source info
    for (const log of logs) {
      assert(log.source !== undefined);
    }
  });
});