/**
 * VibeCoding Logger - TypeScript/Node.js Implementation
 * 
 * AI-Native Logging for LLM Agent Development
 * 
 * @example
 * ```typescript
 * import { createFileLogger } from 'vibe-logger';
 * 
 * const logger = createFileLogger('my-project');
 * 
 * logger.info('user_login', 'User authentication started', {
 *   context: { userId: '123', method: 'oauth' },
 *   humanNote: 'Monitor for suspicious patterns',
 *   aiTodo: 'Check for anomalies in login time'
 * });
 * ```
 */

// Core exports
export { VibeLogger, createLogger, createFileLogger, createEnvLogger } from './logger.js';
export { VibeLoggerConfigManager } from './config.js';

// Type exports
export type {
  LogEntry,
  LogOptions,
  VibeLoggerConfig,
  EnvironmentInfo,
  ErrorInfo,
  FileOperationResult,
  RuntimeEnvironment
} from './types.js';

export { LogLevel } from './types.js';

// Utility exports
export { EnvironmentCollector } from './utils/environment.js';
export { FileSystemManager } from './utils/fileSystem.js';

// Version information
export const VERSION = '0.1.0';