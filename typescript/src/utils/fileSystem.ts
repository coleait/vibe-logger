/**
 * File system utilities for VibeCoding Logger
 * 
 * Handles file operations with thread safety and error handling,
 * similar to Python implementation but using Node.js patterns
 */

import { promises as fs, constants, Stats } from 'fs';
import { dirname, resolve } from 'path';
import { FileOperationResult } from '../types.js';

/**
 * Thread-safe file operations manager
 */
export class FileSystemManager {
  private static writeQueues = new Map<string, Promise<any>>();

  /**
   * Ensure directory exists, creating it if necessary
   * Returns true if directory is accessible, false if not
   */
  static async ensureDirectory(filePath: string): Promise<boolean> {
    try {
      const dir = dirname(resolve(filePath));
      await fs.mkdir(dir, { recursive: true });
      return true;
    } catch (error) {
      // Handle all directory creation failures gracefully
      // This includes: permission denied, read-only filesystem, disk full, etc.
      const errorCode = (error as any).code;
      if (errorCode === 'EEXIST') {
        return true; // Directory already exists
      }
      
      // All other errors (EACCES, EROFS, ENOSPC, ENAMETOOLONG, etc.)
      // should not crash the logger - return false to disable file logging
      return false;
    }
  }

  /**
   * Check if file exists
   */
  static async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath, constants.F_OK);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get file size in MB
   */
  static async getFileSizeMb(filePath: string): Promise<number> {
    try {
      const stats: Stats = await fs.stat(filePath);
      return stats.size / (1024 * 1024);
    } catch {
      return 0;
    }
  }

  /**
   * Append text to file with thread safety
   * Uses a queue per file to prevent concurrent writes
   */
  static async appendToFile(filePath: string, content: string): Promise<FileOperationResult> {
    const resolvedPath = resolve(filePath);
    
    // Get or create queue for this file
    const existingQueue = this.writeQueues.get(resolvedPath) || Promise.resolve();
    
    // Chain the new write operation
    const newQueue = existingQueue
      .then(async () => {
        try {
          await fs.appendFile(resolvedPath, content, 'utf8');
          return { success: true };
        } catch (error) {
          return { 
            success: false, 
            error: error instanceof Error ? error.message : String(error)
          };
        }
      })
      .catch((error) => ({
        success: false,
        error: error instanceof Error ? error.message : String(error)
      }));

    // Update the queue
    this.writeQueues.set(resolvedPath, newQueue);

    // Clean up completed queues after a delay
    newQueue.finally(() => {
      setTimeout(() => {
        if (this.writeQueues.get(resolvedPath) === newQueue) {
          this.writeQueues.delete(resolvedPath);
        }
      }, 1000);
    });

    return await newQueue;
  }

  /**
   * Rotate log file if it exceeds size limit
   */
  static async rotateFileIfNeeded(filePath: string, maxSizeMb: number): Promise<FileOperationResult> {
    try {
      const resolvedPath = resolve(filePath);
      
      if (!(await this.fileExists(resolvedPath))) {
        return { success: true };
      }

      const currentSizeMb = await this.getFileSizeMb(resolvedPath);
      
      if (currentSizeMb <= maxSizeMb) {
        return { success: true };
      }

      // Generate rotated filename with timestamp
      const timestamp = new Date().toISOString()
        .replace(/[-:]/g, '')
        .replace('T', '_')
        .split('.')[0];
      
      const rotatedPath = `${resolvedPath}.${timestamp}`;

      // Rename current file
      await fs.rename(resolvedPath, rotatedPath);

      return { 
        success: true, 
        rotated: true 
      };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Write entire content to file (for batch operations)
   */
  static async writeFile(filePath: string, content: string): Promise<FileOperationResult> {
    try {
      const resolvedPath = resolve(filePath);
      await fs.writeFile(resolvedPath, content, 'utf8');
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Read entire file content
   */
  static async readFile(filePath: string): Promise<{ success: boolean; content?: string; error?: string }> {
    try {
      const resolvedPath = resolve(filePath);
      const content = await fs.readFile(resolvedPath, 'utf8');
      return { success: true, content };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Read file line by line (for loading existing logs)
   */
  static async* readFileLines(filePath: string): AsyncGenerator<string, void, unknown> {
    try {
      const content = await fs.readFile(resolve(filePath), 'utf8');
      const lines = content.split('\n');
      
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed) {
          yield trimmed;
        }
      }
    } catch (error) {
      // If file doesn't exist or can't be read, just return without yielding
      return;
    }
  }

  /**
   * Clean up completed write queues (for memory management)
   */
  static clearCompletedQueues(): void {
    this.writeQueues.clear();
  }
}