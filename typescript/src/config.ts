/**
 * Configuration management for VibeCoding Logger
 * 
 * Provides default configuration and environment variable support
 * following TypeScript best practices while maintaining compatibility
 * with Python implementation concepts.
 */

import { resolve, join } from 'path';
import { homedir } from 'os';
import { VibeLoggerConfig } from './types.js';

/**
 * Default configuration values
 */
const DEFAULT_CONFIG: Required<VibeLoggerConfig> = {
  correlationId: '',           // Will be auto-generated if empty
  logFile: '',                // Will be auto-generated if empty
  autoSave: true,
  maxFileSizeMb: 10,
  keepLogsInMemory: true,
  maxMemoryLogs: 1000,
  createDirs: true
};

/**
 * Configuration class with defaults and environment variable support
 */
export class VibeLoggerConfigManager {
  private config: Required<VibeLoggerConfig>;

  constructor(options: VibeLoggerConfig = {}) {
    // Start with defaults
    this.config = { ...DEFAULT_CONFIG };
    
    // Apply environment variables
    this.loadFromEnvironment();
    
    // Apply provided options (highest priority)
    Object.assign(this.config, options);
    
    // Generate defaults for empty values
    this.generateDefaults();
  }

  /**
   * Load configuration from environment variables
   * Matches Python naming convention: VIBE_*
   */
  private loadFromEnvironment(): void {
    const env = process.env;

    if (env.VIBE_CORRELATION_ID) {
      this.config.correlationId = env.VIBE_CORRELATION_ID;
    }

    if (env.VIBE_LOG_FILE) {
      this.config.logFile = env.VIBE_LOG_FILE;
    }

    if (env.VIBE_AUTO_SAVE !== undefined) {
      this.config.autoSave = env.VIBE_AUTO_SAVE.toLowerCase() === 'true';
    }

    if (env.VIBE_MAX_FILE_SIZE_MB) {
      const size = parseInt(env.VIBE_MAX_FILE_SIZE_MB, 10);
      if (!isNaN(size) && size > 0) {
        this.config.maxFileSizeMb = size;
      }
    }

    if (env.VIBE_KEEP_LOGS_IN_MEMORY !== undefined) {
      this.config.keepLogsInMemory = env.VIBE_KEEP_LOGS_IN_MEMORY.toLowerCase() === 'true';
    }

    if (env.VIBE_MAX_MEMORY_LOGS) {
      const count = parseInt(env.VIBE_MAX_MEMORY_LOGS, 10);
      if (!isNaN(count) && count >= 0) {
        this.config.maxMemoryLogs = count;
      }
    }

    if (env.VIBE_CREATE_DIRS !== undefined) {
      this.config.createDirs = env.VIBE_CREATE_DIRS.toLowerCase() === 'true';
    }
  }

  /**
   * Generate default values for empty configuration
   */
  private generateDefaults(): void {
    // Generate correlation ID if not provided
    if (!this.config.correlationId) {
      this.config.correlationId = this.generateCorrelationId();
    }

    // Generate log file path if not provided
    if (!this.config.logFile) {
      this.config.logFile = this.generateDefaultLogFile();
    }
  }

  /**
   * Generate a unique correlation ID
   */
  private generateCorrelationId(): string {
    return `vibe-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Generate default log file path with timestamp
   * Matches Python convention: ~/.vibe_logs/vibe_YYYYMMDD_HHMMSS.log
   */
  private generateDefaultLogFile(): string {
    const timestamp = new Date().toISOString()
      .replace(/[-:]/g, '')
      .replace('T', '_')
      .split('.')[0]; // Remove milliseconds and timezone

    const logDir = resolve(homedir(), '.vibe_logs');
    return join(logDir, `vibe_${timestamp}.log`);
  }

  /**
   * Create a default file configuration for a specific project
   */
  static createDefaultFileConfig(projectName: string): VibeLoggerConfigManager {
    const timestamp = new Date().toISOString()
      .replace(/[-:]/g, '')
      .replace('T', '_')
      .split('.')[0];

    const logDir = resolve(homedir(), '.vibe_logs', projectName);
    const logFile = join(logDir, `vibe_${timestamp}.log`);

    return new VibeLoggerConfigManager({
      logFile,
      autoSave: true,
      createDirs: true
    });
  }

  /**
   * Create configuration from environment variables only
   */
  static fromEnvironment(): VibeLoggerConfigManager {
    return new VibeLoggerConfigManager(); // Will load from env automatically
  }

  /**
   * Get the current configuration
   */
  getConfig(): Required<VibeLoggerConfig> {
    return { ...this.config };
  }

  /**
   * Update configuration with new values
   */
  updateConfig(updates: Partial<VibeLoggerConfig>): void {
    Object.assign(this.config, updates);
    this.generateDefaults(); // Regenerate any empty values
  }

  /**
   * Validate configuration values
   */
  validate(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (this.config.maxFileSizeMb <= 0) {
      errors.push('maxFileSizeMb must be greater than 0');
    }

    if (this.config.maxMemoryLogs < 0) {
      errors.push('maxMemoryLogs must be non-negative');
    }

    if (!this.config.correlationId) {
      errors.push('correlationId cannot be empty');
    }

    if (!this.config.logFile) {
      errors.push('logFile cannot be empty');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}