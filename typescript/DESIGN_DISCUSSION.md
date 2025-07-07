# TypeScript Implementation Design Discussion

## 🎯 Goal
Create a TypeScript/Node.js implementation of VibeCoding Logger that maintains JSON compatibility with Python version while following TypeScript/Node.js best practices.

## 🤝 Shared Design Elements

### JSON Log Format (Identical)
```typescript
interface LogEntry {
  timestamp: string;           // ISO 8601 UTC
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  correlation_id: string;      // UUID or custom
  operation: string;           // What the code was trying to do
  message: string;            // Human readable message
  context: Record<string, any>; // Rich context data
  environment: EnvironmentInfo; // Runtime environment
  source?: string;            // File location and function
  stack_trace?: string;       // Error stack trace
  human_note?: string;        // Instructions for AI
  ai_todo?: string;          // Specific AI tasks
}
```

### Core API (Similar)
```typescript
// Should match Python API as closely as possible
logger.info(operation, message, options?)
logger.error(operation, message, options?)
logger.logException(operation, error, options?)
logger.getLogsForAI(operationFilter?)
```

## 🔄 Language Difference Discussions

### 1. **Exception Handling**

**Python Approach:**
```python
def log_exception(self, operation: str, exception: Exception, ...):
    # Python has built-in exception types
    stack_trace = traceback.format_exc()
```

**TypeScript Challenges:**
- JavaScript errors don't have consistent structure
- Stack traces vary between environments
- Error types are less standardized

**Proposed TypeScript Solution:**
```typescript
logException(operation: string, error: Error | unknown, options?: LogOptions) {
  // Handle both Error objects and unknown thrown values
  const errorInfo = this.extractErrorInfo(error);
  // Normalize stack traces across Node.js/browser
}

private extractErrorInfo(error: unknown): ErrorInfo {
  if (error instanceof Error) {
    return { message: error.message, stack: error.stack, name: error.name };
  }
  // Handle primitive throws: throw "string", throw 42, etc.
  return { message: String(error), stack: undefined, name: 'UnknownError' };
}
```

### 2. **File System Operations**

**Python Approach:**
```python
from pathlib import Path
import threading

self._file_lock = threading.Lock()
with self._file_lock:
    with open(self.log_file, 'a', encoding='utf-8') as f:
        f.write(entry.to_json() + '\n')
```

**TypeScript Options:**

**Option A: Synchronous (fs.writeFileSync)**
```typescript
import { writeFileSync } from 'fs';
import { Mutex } from 'async-mutex';

private fileMutex = new Mutex();

async saveToFile(entry: LogEntry): Promise<void> {
  await this.fileMutex.runExclusive(() => {
    writeFileSync(this.logFile, entry.toJson() + '\n', { flag: 'a', encoding: 'utf8' });
  });
}
```

**Option B: Asynchronous (fs.promises)**
```typescript
import { appendFile } from 'fs/promises';

async saveToFile(entry: LogEntry): Promise<void> {
  await this.fileMutex.runExclusive(async () => {
    await appendFile(this.logFile, entry.toJson() + '\n', 'utf8');
  });
}
```

**Discussion Question:** Should we use sync or async file operations?
- **Sync**: Simpler, matches Python behavior, logging shouldn't block
- **Async**: More Node.js idiomatic, better for high-throughput

### 3. **Configuration Management**

**Python Approach:**
```python
@dataclass
class VibeLoggerConfig:
    correlation_id: Optional[str] = None
    log_file: Optional[str] = None
    # ... other fields
```

**TypeScript Options:**

**Option A: Interface + Partial**
```typescript
interface VibeLoggerConfig {
  correlationId?: string;
  logFile?: string;
  autoSave?: boolean;
  maxFileSizeMb?: number;
  keepLogsInMemory?: boolean;
  maxMemoryLogs?: number;
  createDirs?: boolean;
}

// Usage: new VibeLogger(config?: Partial<VibeLoggerConfig>)
```

**Option B: Class with Defaults**
```typescript
class VibeLoggerConfig {
  correlationId?: string;
  logFile?: string;
  autoSave = true;
  maxFileSizeMb = 10;
  keepLogsInMemory = true;
  maxMemoryLogs = 1000;
  createDirs = true;

  constructor(options?: Partial<VibeLoggerConfig>) {
    Object.assign(this, options);
  }
}
```

### 4. **Naming Conventions**

**Python Style:** `snake_case`
```python
correlation_id, log_file, max_file_size_mb, get_logs_for_ai()
```

**TypeScript Style:** `camelCase`
```typescript
correlationId, logFile, maxFileSizeMb, getLogsForAI()
```

**Proposal:** Use TypeScript conventions in code, but keep JSON field names identical:
```typescript
class VibeLogger {
  private correlationId: string;  // camelCase in code
  
  info(operation: string, message: string, options?: {
    context?: Record<string, any>;
    humanNote?: string;  // camelCase parameter
    aiTodo?: string;
  }) {
    return new LogEntry({
      correlation_id: this.correlationId,  // snake_case in JSON
      human_note: options?.humanNote,      // Convert to snake_case
      ai_todo: options?.aiTodo
    });
  }
}
```

### 5. **Environment Information**

**Python Approach:**
```python
@dataclass
class EnvironmentInfo:
    python_version: str
    os: str
    platform: str
    architecture: str
```

**TypeScript Approach:**
```typescript
interface EnvironmentInfo {
  node_version: string;     // process.version
  os: string;              // os.platform()
  platform: string;       // os.type()
  architecture: string;   // os.arch()
  runtime?: string;       // 'node' | 'browser' | 'deno' | 'bun'
}

class EnvironmentInfo {
  static collect(): EnvironmentInfo {
    return {
      node_version: process.version,
      os: require('os').platform(),
      platform: require('os').type(),
      architecture: require('os').arch(),
      runtime: this.detectRuntime()
    };
  }
  
  private static detectRuntime(): string {
    if (typeof process !== 'undefined' && process.versions?.node) return 'node';
    if (typeof window !== 'undefined') return 'browser';
    if (typeof Deno !== 'undefined') return 'deno';
    if (typeof Bun !== 'undefined') return 'bun';
    return 'unknown';
  }
}
```

### 6. **Memory Management**

**Python Approach:**
```python
with self._logs_lock:
    self.logs.append(entry)
    if len(self.logs) > max_logs:
        self.logs.pop(0)
```

**TypeScript Approach:**
```typescript
import { Mutex } from 'async-mutex';

class VibeLogger {
  private logs: LogEntry[] = [];
  private logsMutex = new Mutex();
  
  private async addToMemory(entry: LogEntry): Promise<void> {
    await this.logsMutex.runExclusive(() => {
      this.logs.push(entry);
      if (this.logs.length > this.config.maxMemoryLogs) {
        this.logs.shift(); // Remove first element
      }
    });
  }
}
```

### 7. **Package Structure**

**Python Structure:**
```
python/vibelogger/
├── __init__.py
├── logger.py
├── config.py
├── handlers.py
└── formatters.py
```

**Proposed TypeScript Structure:**
```
typescript/src/
├── index.ts           // Main exports
├── logger.ts          // Core logger
├── config.ts          // Configuration
├── types.ts           // TypeScript interfaces
├── handlers/          // Standard logging integration
│   ├── index.ts
│   └── winston.ts     // Winston adapter
├── formatters/        // Log formatters
│   ├── index.ts
│   └── structured.ts
└── utils/
    ├── environment.ts
    └── fileSystem.ts
```

## 🤔 Open Questions for Discussion

### 1. **Async vs Sync File Operations**
- Should file writes be async (Node.js idiomatic) or sync (simpler, matches Python)?
- How do we handle async in a logging context that shouldn't block?

### 2. **Error Handling Philosophy**
- How strict should we be about unknown error types?
- Should we try to serialize complex objects thrown as errors?

### 3. **Browser Support**
- Should we support browser environments?
- How do we handle file operations in browser (localStorage? IndexedDB?)?

### 4. **Dependencies**
- Minimize dependencies (like Python version) or use popular libraries?
- async-mutex for threading, winston for standard logging integration?

### 5. **Testing Strategy**
- Use Jest (popular) or Node.js built-in test runner?
- How do we test file operations and threading?

### 6. **Package Distribution**
- CommonJS + ESM dual package?
- Separate packages for Node.js vs browser?

## 📝 Proposed Minimal API

```typescript
// Main logger creation
import { createFileLogger, createLogger, VibeLoggerConfig } from 'vibe-logger';

// Simple usage (matches Python)
const logger = createFileLogger('my-project');

logger.info('user_login', 'User authentication started', {
  context: { userId: '123', method: 'oauth' },
  humanNote: 'Monitor for suspicious patterns',
  aiTodo: 'Check for anomalies in login time'
});

// Advanced usage
const config = new VibeLoggerConfig({
  logFile: './logs/custom.log',
  maxFileSizeMb: 50,
  autoSave: true
});

const customLogger = createLogger(config);
```

Let's discuss these design decisions before implementation!