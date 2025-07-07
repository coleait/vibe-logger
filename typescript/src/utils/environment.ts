/**
 * Environment detection and information gathering utilities
 * 
 * Collects runtime environment information for log entries,
 * similar to Python's EnvironmentInfo.collect()
 */

import { platform, type, arch, version } from 'os';
import { EnvironmentInfo, RuntimeEnvironment } from '../types.js';

/**
 * Environment information collector
 */
export class EnvironmentCollector {
  private static cachedInfo: EnvironmentInfo | null = null;

  /**
   * Collect current environment information
   * Caches result for performance since environment doesn't change during runtime
   */
  static collect(): EnvironmentInfo {
    if (this.cachedInfo === null) {
      this.cachedInfo = {
        node_version: this.getNodeVersion(),
        os: platform(),
        platform: type(),
        architecture: arch(),
        runtime: this.detectRuntime()
      };
    }
    return this.cachedInfo;
  }

  /**
   * Force refresh of cached environment information
   */
  static refresh(): EnvironmentInfo {
    this.cachedInfo = null;
    return this.collect();
  }

  /**
   * Get Node.js version
   */
  private static getNodeVersion(): string {
    try {
      return process.version || 'unknown';
    } catch {
      return 'unknown';
    }
  }

  /**
   * Detect the current JavaScript runtime environment
   */
  private static detectRuntime(): RuntimeEnvironment {
    try {
      // Check for Node.js
      if (typeof process !== 'undefined' && process.versions?.node) {
        return 'node';
      }

      // Check for Deno
      if (typeof (globalThis as any).Deno !== 'undefined') {
        return 'deno';
      }

      // Check for Bun
      if (typeof (globalThis as any).Bun !== 'undefined') {
        return 'bun';
      }

      // Check for browser
      if (typeof globalThis !== 'undefined' && 'window' in globalThis) {
        return 'browser';
      }

      return 'unknown';
    } catch {
      return 'unknown';
    }
  }

  /**
   * Get additional runtime information
   */
  static getExtendedInfo(): Record<string, any> {
    const info: Record<string, any> = {};

    try {
      // Node.js specific information
      if (typeof process !== 'undefined') {
        info.processId = process.pid;
        info.nodeEnv = process.env.NODE_ENV || 'development';
        info.platform_version = process.platform;
        
        if (process.versions) {
          info.v8_version = process.versions.v8;
          info.uv_version = process.versions.uv;
          info.openssl_version = process.versions.openssl;
        }

        if (process.memoryUsage) {
          const memory = process.memoryUsage();
          info.memory_usage = {
            rss: memory.rss,
            heapTotal: memory.heapTotal,
            heapUsed: memory.heapUsed,
            external: memory.external
          };
        }
      }

      // Browser specific information
      if (typeof globalThis !== 'undefined' && 'window' in globalThis && 'navigator' in globalThis) {
        const navigator = (globalThis as any).navigator;
        info.user_agent = navigator?.userAgent;
        info.browser_language = navigator?.language;
        info.browser_platform = navigator?.platform;
      }

      // Deno specific information
      if (typeof (globalThis as any).Deno !== 'undefined') {
        const Deno = (globalThis as any).Deno;
        info.deno_version = Deno.version?.deno;
        info.typescript_version = Deno.version?.typescript;
      }

      // Bun specific information
      if (typeof (globalThis as any).Bun !== 'undefined') {
        const Bun = (globalThis as any).Bun;
        info.bun_version = Bun.version;
      }

    } catch (error) {
      info.environment_error = String(error);
    }

    return info;
  }

  /**
   * Check if running in specific environment
   */
  static isNode(): boolean {
    return this.detectRuntime() === 'node';
  }

  static isBrowser(): boolean {
    return this.detectRuntime() === 'browser';
  }

  static isDeno(): boolean {
    return this.detectRuntime() === 'deno';
  }

  static isBun(): boolean {
    return this.detectRuntime() === 'bun';
  }
}