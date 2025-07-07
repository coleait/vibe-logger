/**
 * VibeCoding Logger - TypeScript Implementation
 * 
 * AI-Native Logging for LLM Agent Development
 * 
 * CONCEPT:
 * This logger is designed specifically for VibeCoding (AI-driven development) where
 * LLMs need rich, structured context to understand and debug code effectively.
 * Unlike traditional human-readable logs, this creates "AI briefing packages" with
 * comprehensive context, correlation tracking, and embedded human annotations.
 * 
 * KEY FEATURES:
 * - Structured JSON format optimized for LLM consumption
 * - Rich context including function arguments, stack traces, environment info
 * - Correlation IDs to track request flows across operations
 * - Human annotation fields (humanNote, aiTodo) for AI instructions
 * - Automatic file saving with timestamp-based naming
 * - Thread-safe operations for concurrent environments
 * 
 * BASIC USAGE:
 * ```typescript
 * import { createFileLogger } from 'vibe-logger';
 * 
 * // Create logger with auto-save to timestamped file
 * const logger = createFileLogger('my-project');
 * 
 * // Log with rich context
 * logger.info('fetchUserProfile', 'Starting user profile fetch', {
 *   context: { userId: '123', source: 'api_endpoint' },
 *   humanNote: 'AI-TODO: Check if user exists before fetching profile'
 * });
 * 
 * // Log exceptions with full context
 * try {
 *   const result = riskyOperation();
 * } catch (error) {
 *   logger.logException('fetchUserProfile', error, {
 *     context: { userId: '123' },
 *     aiTodo: 'Suggest proper error handling for this case'
 *   });
 * }
 * 
 * // Get logs formatted for AI analysis
 * const aiContext = logger.getLogsForAI();
 * ```
 */

import { LogEntry, LogLevel, LogOptions, ErrorInfo, VibeLoggerConfig } from './types.js';
import { VibeLoggerConfigManager } from './config.js';
import { EnvironmentCollector } from './utils/environment.js';
import { FileSystemManager } from './utils/fileSystem.js';

/**
 * Core VibeCoding Logger implementation
 */
export class VibeLogger {
  private config: Required<VibeLoggerConfig>;
  private correlationId: string;
  private environment = EnvironmentCollector.collect();
  private logs: LogEntry[] = [];
  private memoryMutex = Promise.resolve(); // Simple mutex using Promise chaining

  constructor(configOptions?: VibeLoggerConfig) {
    const configManager = new VibeLoggerConfigManager(configOptions);
    const validation = configManager.validate();
    
    if (!validation.valid) {
      throw new Error(`Invalid configuration: ${validation.errors.join(', ')}`);
    }

    this.config = configManager.getConfig();
    this.correlationId = this.config.correlationId;

    // Ensure log directory exists if auto-save is enabled
    if (this.config.autoSave && this.config.createDirs) {
      FileSystemManager.ensureDirectory(this.config.logFile).catch(error => {
        console.error('Failed to create log directory:', error);
      });
    }
  }

  /**
   * Get caller information (file, line, function)
   * TypeScript equivalent of Python's inspect functionality
   */
  private getCallerInfo(): string | undefined {
    try {
      const stack = new Error().stack;
      if (!stack) return undefined;

      const lines = stack.split('\n');
      // Skip: Error(), getCallerInfo(), the calling log method, and find the actual caller
      const callerLine = lines[4];
      
      if (!callerLine) return undefined;

      // Extract meaningful part of stack trace
      const match = callerLine.match(/at\s+(.+)\s+\((.+):(\d+):(\d+)\)/);
      if (match) {
        const [, functionName, filePath, lineNumber] = match;
        const fileName = filePath?.split('/').pop() || filePath || 'unknown';
        return `${fileName}:${lineNumber} in ${functionName}()`;
      }

      // Fallback for different stack trace formats
      return callerLine.trim().replace(/^\s*at\s+/, '');
    } catch {
      return undefined;
    }
  }

  /**
   * Extract error information from various error types
   */
  private extractErrorInfo(error: unknown): ErrorInfo {
    if (error instanceof Error) {
      return {
        message: error.message,
        name: error.name,
        stack: error.stack,
        originalError: error
      };
    }

    // Handle non-Error throws (strings, numbers, objects, etc.)
    if (typeof error === 'string') {
      return {
        message: error,
        name: 'StringError',
        originalError: error
      };
    }

    if (typeof error === 'object' && error !== null) {
      return {
        message: JSON.stringify(error),
        name: 'ObjectError',
        originalError: error
      };
    }

    return {
      message: String(error),
      name: 'UnknownError',
      originalError: error
    };
  }

  /**
   * Create a log entry with all context information
   */
  private createLogEntry(
    level: LogLevel,
    operation: string,
    message: string,
    options: LogOptions = {}
  ): LogEntry {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      correlation_id: this.correlationId,
      operation,
      message,
      context: options.context || {},
      environment: this.environment,
      source: this.getCallerInfo(),
      human_note: options.humanNote,
      ai_todo: options.aiTodo
    };

    // Add stack trace for errors or if explicitly requested
    if (level === LogLevel.ERROR || level === LogLevel.CRITICAL || options.includeStack) {
      entry.stack_trace = new Error().stack;
    }

    return entry;
  }

  /**
   * Add log entry to memory (with thread safety)
   */
  private async addToMemory(entry: LogEntry): Promise<void> {
    this.memoryMutex = this.memoryMutex.then(() => {
      if (this.config.keepLogsInMemory) {
        this.logs.push(entry);
        
        // Trim logs if exceeding memory limit
        if (this.logs.length > this.config.maxMemoryLogs) {
          this.logs.shift(); // Remove oldest entry
        }
      }
    });

    await this.memoryMutex;
  }

  /**
   * Save log entry to file (async, non-blocking)
   */
  private async saveToFile(entry: LogEntry): Promise<void> {
    if (!this.config.autoSave || !this.config.logFile) {
      return;
    }

    try {
      // Check if file rotation is needed
      await FileSystemManager.rotateFileIfNeeded(
        this.config.logFile, 
        this.config.maxFileSizeMb
      );

      // Append log entry
      const jsonLine = JSON.stringify(entry, null, 0) + '\n';
      await FileSystemManager.appendToFile(this.config.logFile, jsonLine);
    } catch (error) {
      // Log file errors shouldn't crash the application
      console.error('Failed to save log to file:', error);
    }
  }

  /**
   * Core logging method
   */
  async log(
    level: LogLevel,
    operation: string,
    message: string,
    options?: LogOptions
  ): Promise<LogEntry> {
    const entry = this.createLogEntry(level, operation, message, options);

    // Add to memory and save to file concurrently
    await Promise.all([
      this.addToMemory(entry),
      this.saveToFile(entry)
    ]);

    return entry;
  }

  /**
   * Log debug message
   */
  async debug(operation: string, message: string, options?: LogOptions): Promise<LogEntry> {
    return this.log(LogLevel.DEBUG, operation, message, options);
  }

  /**
   * Log info message
   */
  async info(operation: string, message: string, options?: LogOptions): Promise<LogEntry> {
    return this.log(LogLevel.INFO, operation, message, options);
  }

  /**
   * Log warning message
   */
  async warning(operation: string, message: string, options?: LogOptions): Promise<LogEntry> {
    return this.log(LogLevel.WARNING, operation, message, options);
  }

  /**
   * Log error message
   */
  async error(operation: string, message: string, options?: LogOptions): Promise<LogEntry> {
    return this.log(LogLevel.ERROR, operation, message, options);
  }

  /**
   * Log critical message
   */
  async critical(operation: string, message: string, options?: LogOptions): Promise<LogEntry> {
    return this.log(LogLevel.CRITICAL, operation, message, options);
  }

  /**
   * Log exception with full context
   */
  async logException(
    operation: string,
    error: unknown,
    options: Omit<LogOptions, 'includeStack'> = {}
  ): Promise<LogEntry> {
    const errorInfo = this.extractErrorInfo(error);
    
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: LogLevel.ERROR,
      correlation_id: this.correlationId,
      operation,
      message: `${errorInfo.name}: ${errorInfo.message}`,
      context: {
        ...(options.context || {}),
        error_type: errorInfo.name,
        original_error: errorInfo.originalError
      },
      environment: this.environment,
      source: this.getCallerInfo(),
      stack_trace: errorInfo.stack,
      human_note: options.humanNote,
      ai_todo: options.aiTodo
    };

    await Promise.all([
      this.addToMemory(entry),
      this.saveToFile(entry)
    ]);

    return entry;
  }

  /**
   * Get all logs as JSON string formatted for AI consumption
   */
  async getLogsForAI(operationFilter?: string): Promise<string> {
    await this.memoryMutex; // Wait for any pending memory operations

    let logsToReturn = this.logs;
    
    if (operationFilter) {
      logsToReturn = this.logs.filter(log => 
        log.operation.includes(operationFilter)
      );
    }

    return JSON.stringify(logsToReturn, null, 2);
  }

  /**
   * Get logs as array of objects
   */
  async getLogs(operationFilter?: string): Promise<LogEntry[]> {
    await this.memoryMutex;

    if (operationFilter) {
      return this.logs.filter(log => 
        log.operation.includes(operationFilter)
      );
    }

    return [...this.logs]; // Return copy to prevent external modification
  }

  /**
   * Clear all logs from memory
   */
  async clearLogs(): Promise<void> {
    this.memoryMutex = this.memoryMutex.then(() => {
      this.logs = [];
    });
    await this.memoryMutex;
  }

  /**
   * Save all current logs to a file
   */
  async saveAllLogs(filePath?: string): Promise<void> {
    const targetFile = filePath || this.config.logFile;
    if (!targetFile) {
      throw new Error('No log file specified');
    }

    await this.memoryMutex; // Wait for pending operations

    if (this.config.createDirs) {
      await FileSystemManager.ensureDirectory(targetFile);
    }

    const content = this.logs
      .map(log => JSON.stringify(log, null, 0))
      .join('\n') + '\n';

    const result = await FileSystemManager.writeFile(targetFile, content);
    if (!result.success) {
      throw new Error(`Failed to save logs: ${result.error}`);
    }
  }

  /**
   * Load logs from a file
   */
  async loadLogsFromFile(filePath: string): Promise<void> {
    const loadedLogs: LogEntry[] = [];

    for await (const line of FileSystemManager.readFileLines(filePath)) {
      try {
        const logData = JSON.parse(line);
        // Validate that it's a proper log entry
        if (logData.timestamp && logData.level && logData.operation) {
          loadedLogs.push(logData as LogEntry);
        }
      } catch (error) {
        console.error('Failed to parse log line:', error);
      }
    }

    // Add loaded logs to memory
    this.memoryMutex = this.memoryMutex.then(() => {
      this.logs.push(...loadedLogs);
      
      // Trim if exceeding memory limit
      if (this.logs.length > this.config.maxMemoryLogs) {
        this.logs = this.logs.slice(-this.config.maxMemoryLogs);
      }
    });

    await this.memoryMutex;
  }

  /**
   * Get current configuration
   */
  getConfig(): Required<VibeLoggerConfig> {
    return { ...this.config };
  }

  /**
   * Get correlation ID
   */
  getCorrelationId(): string {
    return this.correlationId;
  }
}

/**
 * Create a logger with custom configuration
 */
export function createLogger(config?: VibeLoggerConfig): VibeLogger {
  return new VibeLogger(config);
}

/**
 * Create a file logger for a specific project
 */
export function createFileLogger(projectName: string): VibeLogger {
  const configManager = VibeLoggerConfigManager.createDefaultFileConfig(projectName);
  return new VibeLogger(configManager.getConfig());
}

/**
 * Create a logger configured from environment variables
 */
export function createEnvLogger(): VibeLogger {
  const configManager = VibeLoggerConfigManager.fromEnvironment();
  return new VibeLogger(configManager.getConfig());
}