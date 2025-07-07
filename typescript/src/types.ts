/**
 * TypeScript type definitions for VibeCoding Logger
 * 
 * These types define the core interfaces while maintaining JSON compatibility
 * with the Python implementation. The JSON field names use snake_case to match
 * the Python version, while TypeScript code uses camelCase.
 */

/**
 * Log levels supported by VibeCoding Logger
 */
export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARNING = 'WARNING',
  ERROR = 'ERROR',
  CRITICAL = 'CRITICAL'
}

/**
 * Environment information captured with each log entry
 * JSON field names match Python implementation
 */
export interface EnvironmentInfo {
  node_version: string;     // process.version
  os: string;              // os.platform()
  platform: string;       // os.type()
  architecture: string;   // os.arch()
  runtime: string;        // 'node' | 'browser' | 'deno' | 'bun'
}

/**
 * Core log entry structure - matches Python JSON output exactly
 * All field names use snake_case for JSON compatibility
 */
export interface LogEntry {
  timestamp: string;              // ISO 8601 UTC format
  level: LogLevel;               // Log level
  correlation_id: string;        // UUID or custom correlation ID
  operation: string;             // What the code was trying to do
  message: string;              // Human readable message
  context: Record<string, any>; // Rich context data
  environment: EnvironmentInfo; // Runtime environment info
  source?: string;              // File location and function name
  stack_trace?: string;         // Error stack trace (for errors)
  human_note?: string;          // Instructions for AI analysis
  ai_todo?: string;            // Specific AI tasks or requests
}

/**
 * Configuration options for VibeCoding Logger
 * Uses camelCase for TypeScript code, converted to snake_case in JSON
 */
export interface VibeLoggerConfig {
  correlationId?: string;       // Custom correlation ID
  logFile?: string;            // Path to log file
  autoSave?: boolean;          // Auto-save to file
  maxFileSizeMb?: number;      // Max file size before rotation
  keepLogsInMemory?: boolean;  // Keep logs in memory
  maxMemoryLogs?: number;      // Max number of logs in memory
  createDirs?: boolean;        // Auto-create log directories
}

/**
 * Options for individual log calls
 */
export interface LogOptions {
  context?: Record<string, any>;  // Additional context data
  humanNote?: string;            // Note for AI analysis
  aiTodo?: string;              // AI task or request
  includeStack?: boolean;       // Include stack trace
}

/**
 * Exception information extracted from errors
 */
export interface ErrorInfo {
  message: string;        // Error message
  name: string;          // Error type/name
  stack?: string;        // Stack trace if available
  originalError: any;    // Original error object for context
}

/**
 * Runtime environment detection
 */
export type RuntimeEnvironment = 'node' | 'browser' | 'deno' | 'bun' | 'unknown';

/**
 * File operation result
 */
export interface FileOperationResult {
  success: boolean;
  error?: string;
  rotated?: boolean;  // If file was rotated during operation
}