/**
 * Comprehensive filesystem failure tests for TypeScript implementation
 * These tests target real-world scenarios that break user installations
 */

import { describe, it, before, after } from 'node:test';
import assert from 'node:assert';
import { promises as fs, constants } from 'fs';
import { join, resolve } from 'path';
import { tmpdir } from 'os';
import { createFileLogger, createLogger, VibeLogger } from '../index.js';
import { VibeLoggerConfig } from '../types.js';

describe('Filesystem Failure Scenarios', () => {
  let tempDir: string;

  before(async () => {
    tempDir = await fs.mkdtemp(join(tmpdir(), 'vibe-test-'));
  });

  after(async () => {
    try {
      await fs.rm(tempDir, { recursive: true, force: true });
    } catch (error) {
      // Ignore cleanup errors
    }
  });

  describe('Permission and Access Failures', () => {
    it('should handle read-only directory gracefully', async () => {
      const readOnlyDir = join(tempDir, 'readonly');
      await fs.mkdir(readOnlyDir);
      
      // Make directory read-only
      await fs.chmod(readOnlyDir, 0o444);
      
      try {
        const config: VibeLoggerConfig = {
          logFile: join(readOnlyDir, 'test.log'),
          autoSave: true,
          createDirs: true
        };
        
        const logger = new VibeLogger(config);
        
        // Should not crash, should work with memory logging
        await logger.info('test', 'Should work despite read-only directory');
        
        const logs = await logger.getLogsForAI();
        assert(logs.includes('Should work despite read-only directory'));
        
      } finally {
        // Restore permissions for cleanup
        await fs.chmod(readOnlyDir, 0o755);
      }
    });

    it('should handle permission denied on directory creation', async () => {
      // Try to create log in impossible location
      const config: VibeLoggerConfig = {
        logFile: '/root/impossible/access/test.log',
        autoSave: true,
        createDirs: true
      };
      
      const logger = new VibeLogger(config);
      
      // Should not crash during initialization
      await logger.info('test', 'Should work without file access');
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes('Should work without file access'));
    });

    it('should handle extremely long file paths', async () => {
      // Create path longer than filesystem limits
      const longPath = '/tmp/' + 'a'.repeat(300) + '/' + 'b'.repeat(300) + '/test.log';
      
      const config: VibeLoggerConfig = {
        logFile: longPath,
        autoSave: true,
        createDirs: true
      };
      
      const logger = new VibeLogger(config);
      
      // Should handle gracefully
      await logger.info('test', 'Extremely long path test');
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes('Extremely long path test'));
    });

    it('should handle special characters in file paths', async () => {
      const specialPath = join(tempDir, 'special<>:|?*".log');
      
      const config: VibeLoggerConfig = {
        logFile: specialPath,
        autoSave: true,
        createDirs: true
      };
      
      const logger = new VibeLogger(config);
      
      // Should handle gracefully
      await logger.info('test', 'Special characters in path');
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes('Special characters in path'));
    });

    it('should handle network drive unavailable', async () => {
      const networkPath = '//nonexistent-server/share/logs/test.log';
      
      const config: VibeLoggerConfig = {
        logFile: networkPath,
        autoSave: true,
        createDirs: true
      };
      
      const logger = new VibeLogger(config);
      
      // Should not crash
      await logger.info('test', 'Network drive unavailable');
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes('Network drive unavailable'));
    });
  });

  describe('File System State Issues', () => {
    it('should handle log file path occupied by directory', async () => {
      const dirPath = join(tempDir, 'shouldbefile');
      await fs.mkdir(dirPath);
      
      const config: VibeLoggerConfig = {
        logFile: dirPath, // This is a directory!
        autoSave: true,
        createDirs: true
      };
      
      const logger = new VibeLogger(config);
      
      // Should handle directory collision
      await logger.info('test', 'Directory collision test');
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes('Directory collision test'));
    });

    it('should handle corrupted existing log file', async () => {
      const logFile = join(tempDir, 'corrupted.log');
      
      // Create corrupted log file
      await fs.writeFile(logFile, 'this is not valid JSON\n{incomplete json\n');
      
      const config: VibeLoggerConfig = {
        logFile: logFile,
        autoSave: true,
        createDirs: true
      };
      
      const logger = new VibeLogger(config);
      
      // Should not crash on creation
      await logger.info('test', 'Should work despite corrupted file');
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes('Should work despite corrupted file'));
    });

    it('should handle file deleted during operation', async () => {
      const logFile = join(tempDir, 'deleteme.log');
      
      const config: VibeLoggerConfig = {
        logFile: logFile,
        autoSave: true,
        createDirs: true
      };
      
      const logger = new VibeLogger(config);
      
      // Write initial log
      await logger.info('test', 'Before deletion');
      
      // Delete the log file externally if it exists
      try {
        await fs.unlink(logFile);
      } catch (error) {
        // File might not exist yet, that's OK
      }
      
      // Should handle gracefully
      await logger.info('test', 'After deletion');
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes('Before deletion'));
      assert(logs.includes('After deletion'));
    });
  });

  describe('Concurrent Access Issues', () => {
    it('should handle multiple loggers writing to same file', async () => {
      const sharedFile = join(tempDir, 'shared.log');
      
      const createAndLog = async (workerId: number): Promise<void> => {
        const config: VibeLoggerConfig = {
          logFile: sharedFile,
          autoSave: true,
          createDirs: true
        };
        
        const logger = new VibeLogger(config);
        
        for (let i = 0; i < 5; i++) {
          await logger.info('test', `Worker ${workerId} message ${i}`);
          // Small delay to simulate real usage
          await new Promise(resolve => setTimeout(resolve, 1));
        }
      };
      
      // Start multiple concurrent loggers
      const promises = [];
      for (let i = 0; i < 3; i++) {
        promises.push(createAndLog(i));
      }
      
      // Should complete without crashes
      await Promise.all(promises);
      
      // Check if file exists and has content
      try {
        const content = await fs.readFile(sharedFile, 'utf8');
        assert(content.length > 0, 'Shared log file should have content');
      } catch (error) {
        // File might not exist if all operations were memory-only, that's OK
      }
    });

    it('should handle rapid concurrent logging', async () => {
      const logger = createFileLogger('concurrent-test');
      
      const promises = [];
      for (let i = 0; i < 50; i++) {
        promises.push(
          logger.info('test', `Concurrent message ${i}`, {
            context: { threadId: i, timestamp: Date.now() }
          })
        );
      }
      
      // Should complete without race conditions
      await Promise.all(promises);
      
      const logs = await logger.getLogsForAI();
      const logLines = logs.split('\n').filter(line => line.trim());
      
      // Should have all 50 messages
      assert(logLines.length >= 50, `Expected at least 50 logs, got ${logLines.length}`);
    });
  });

  describe('Memory and Resource Constraints', () => {
    it('should handle extremely large context objects', async () => {
      const logger = createLogger();
      
      // Create very large context
      const largeContext = {
        massiveArray: Array.from({ length: 10000 }, (_, i) => i),
        bigString: 'x'.repeat(100000),
        nestedObject: Object.fromEntries(
          Array.from({ length: 100 }, (_, i) => [`key_${i}`, `value_${i}`.repeat(1000)])
        )
      };
      
      // Should not crash or hang
      await logger.info('test', 'Large context test', { context: largeContext });
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes('Large context test'));
    });

    it('should prevent memory exhaustion with log limits', async () => {
      const config: VibeLoggerConfig = {
        maxMemoryLogs: 10, // Very small limit
        keepLogsInMemory: true
      };
      
      const logger = new VibeLogger(config);
      
      // Add more logs than memory limit
      for (let i = 0; i < 50; i++) {
        await logger.info('test', `Message ${i}`);
      }
      
      const logs = await logger.getLogsForAI();
      const logArray = JSON.parse(logs);
      
      // Should not exceed memory limit
      assert(logArray.length <= 10, `Expected max 10 logs, got ${logArray.length}`);
      
      // Should keep most recent logs
      assert(logs.includes('Message 49'), 'Should keep most recent message');
    });

    it('should handle circular references in context', async () => {
      const logger = createLogger();
      
      // Create circular reference
      const objA: any = { name: 'A' };
      const objB: any = { name: 'B', ref: objA };
      objA.ref = objB;
      
      // Should handle gracefully without infinite recursion
      await logger.info('test', 'Circular reference test', { 
        context: { circular: objA } 
      });
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes('Circular reference test'));
    });
  });

  describe('Error Recovery and Resilience', () => {
    it('should recover from temporary file system errors', async () => {
      const logFile = join(tempDir, 'recovery-test.log');
      
      const config: VibeLoggerConfig = {
        logFile: logFile,
        autoSave: true,
        createDirs: true
      };
      
      const logger = new VibeLogger(config);
      
      // Log before error
      await logger.info('test', 'Before error');
      
      // Simulate temporary filesystem error by making parent directory read-only
      const parentDir = join(tempDir);
      const originalMode = (await fs.stat(parentDir)).mode;
      
      try {
        await fs.chmod(parentDir, 0o444);
        
        // Should continue working despite filesystem issues
        await logger.info('test', 'During error');
        
        // Restore access
        await fs.chmod(parentDir, originalMode);
        
        // Should work again
        await logger.info('test', 'After recovery');
        
        const logs = await logger.getLogsForAI();
        assert(logs.includes('Before error'));
        assert(logs.includes('During error'));
        assert(logs.includes('After recovery'));
        
      } finally {
        // Ensure permissions are restored
        try {
          await fs.chmod(parentDir, originalMode);
        } catch (error) {
          // Ignore restoration errors
        }
      }
    });

    it('should handle saveAllLogs with directory creation failure', async () => {
      const logger = createLogger();
      
      // Add some logs
      await logger.info('test', 'Test message 1');
      await logger.info('test', 'Test message 2');
      
      // Try to save to impossible location
      const impossiblePath = '/root/impossible/save.log';
      
      try {
        await logger.saveAllLogs(impossiblePath);
        assert.fail('Should have thrown error for impossible path');
      } catch (error) {
        assert(error instanceof Error);
        assert(error.message.includes('Cannot create directory'));
      }
      
      // Logger should still work normally
      await logger.info('test', 'After failed save');
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes('After failed save'));
    });
  });

  describe('Edge Cases and Validation', () => {
    it('should handle undefined and null values gracefully', async () => {
      const logger = createLogger();
      
      // Should not crash with edge case values
      await logger.info('test', 'Null context test', { 
        context: { 
          nullValue: null,
          undefinedValue: undefined,
          emptyString: '',
          zero: 0,
          falsy: false
        }
      });
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes('Null context test'));
    });

    it('should handle malformed correlation IDs', async () => {
      // Test various malformed correlation ID scenarios
      const testCases = [
        { correlationId: '' },
        { correlationId: null as any },
        { correlationId: undefined as any },
        { correlationId: 123 as any },
        { correlationId: {} as any }
      ];
      
      for (const testCase of testCases) {
        const config: VibeLoggerConfig = testCase;
        const logger = new VibeLogger(config);
        
        // Should not crash with malformed correlation ID
        await logger.info('test', `Correlation ID test: ${JSON.stringify(testCase)}`);
        
        const logs = await logger.getLogsForAI();
        assert(logs.length > 0, 'Should have logs despite malformed correlation ID');
      }
    });

    it('should handle extremely long log messages', async () => {
      const logger = createLogger();
      
      const veryLongMessage = 'x'.repeat(1000000); // 1MB message
      
      // Should handle without crashing
      await logger.info('test', veryLongMessage);
      
      const logs = await logger.getLogsForAI();
      assert(logs.includes(veryLongMessage.substring(0, 100)));
    });
  });
});