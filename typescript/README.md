# VibeCoding Logger - TypeScript/Node.js Implementation

**AI-Native Logging for LLM Agent Development**

This is the TypeScript/Node.js implementation of VibeCoding Logger, designed to maintain full JSON compatibility with the Python version while following TypeScript best practices.

## ✨ Features

- 🤖 **AI-Optimized JSON Logging** - Structured format perfect for LLM consumption
- 🔗 **Correlation Tracking** - Link related operations across your application
- 💬 **Human Annotations** - Embed AI instructions directly in logs
- 🧵 **Thread-Safe Operations** - Safe for concurrent Node.js applications
- 📁 **Automatic File Management** - Timestamped files with rotation
- 💾 **Memory Management** - Configurable limits to prevent memory issues
- 🌍 **Environment Detection** - Automatic runtime environment information
- 📊 **Zero Dependencies** - Minimal footprint, maximum compatibility

## 🚀 Quick Start

### Installation

```bash
npm install vibe-logger
```

### Basic Usage

```typescript
import { createFileLogger } from 'vibe-logger';

// Create logger with auto-save to timestamped file
const logger = createFileLogger('my-project');

// Log with rich context for AI analysis
await logger.info('user_login', 'User authentication started', {
  context: {
    userId: '123',
    method: 'oauth',
    ipAddress: '192.168.1.100'
  },
  humanNote: 'Monitor for suspicious patterns',
  aiTodo: 'Check if multiple failed attempts from this IP'
});

// Log exceptions with full context
try {
  await riskyOperation();
} catch (error) {
  await logger.logException('payment_processing', error, {
    context: { orderId: 'order-123', amount: 99.99 },
    aiTodo: 'Suggest error handling improvements'
  });
}

// Get logs formatted for AI analysis
const aiContext = await logger.getLogsForAI();
console.log(aiContext); // Send this to your LLM
```

## 📖 API Reference

### Creating Loggers

```typescript
import { createLogger, createFileLogger, createEnvLogger } from 'vibe-logger';

// Basic logger
const logger = createLogger({
  correlationId: 'custom-id',
  keepLogsInMemory: true,
  autoSave: false
});

// File logger (recommended)
const fileLogger = createFileLogger('project-name');

// Environment-configured logger
const envLogger = createEnvLogger(); // Uses VIBE_* env vars
```

### Logging Methods

```typescript
// All methods return Promise<LogEntry>
await logger.debug(operation, message, options?);
await logger.info(operation, message, options?);
await logger.warning(operation, message, options?);
await logger.error(operation, message, options?);
await logger.critical(operation, message, options?);

// Exception logging
await logger.logException(operation, error, options?);
```

### Log Options

```typescript
interface LogOptions {
  context?: Record<string, any>;  // Rich context data
  humanNote?: string;            // Instructions for AI
  aiTodo?: string;              // Specific AI tasks
  includeStack?: boolean;       // Force stack trace inclusion
}
```

## ⚙️ Configuration

### Object Configuration

```typescript
import { createLogger, type VibeLoggerConfig } from 'vibe-logger';

const config: VibeLoggerConfig = {
  correlationId: 'custom-correlation-id',
  logFile: './logs/app.log',
  autoSave: true,
  maxFileSizeMb: 50,
  keepLogsInMemory: true,
  maxMemoryLogs: 1000,
  createDirs: true
};

const logger = createLogger(config);
```

### Environment Variables

```bash
export VIBE_LOG_FILE=./logs/app.log
export VIBE_MAX_FILE_SIZE_MB=25
export VIBE_AUTO_SAVE=true
export VIBE_KEEP_LOGS_IN_MEMORY=true
export VIBE_MAX_MEMORY_LOGS=500
export VIBE_CORRELATION_ID=my-service-id
```

## 🔧 Advanced Usage

### Memory Management

```typescript
// For long-running services - minimize memory usage
const logger = createLogger({
  keepLogsInMemory: false,  // Don't store in memory
  autoSave: true,          // Save directly to file
  maxFileSizeMb: 100       // Rotate at 100MB
});
```

### Correlation Tracking

```typescript
// Use same correlation ID across related operations
const correlationId = `request-${Date.now()}`;
const logger = createLogger({ correlationId });

await logger.info('request_start', 'Processing API request');
await logger.info('auth_check', 'Validating credentials');
await logger.info('business_logic', 'Executing core logic');
await logger.info('request_end', 'Request completed');

// All logs will have the same correlation_id
```

### Error Handling

```typescript
// Handles all JavaScript error types
const errors = [
  new Error('Standard error'),
  'String error',
  { custom: 'object error' },
  42,
  null
];

for (const error of errors) {
  await logger.logException('error_handling', error);
}
```

## 📊 Log Format

Logs are structured JSON compatible with the Python implementation:

```json
{
  "timestamp": "2025-07-07T10:30:45.123Z",
  "level": "ERROR",
  "correlation_id": "req-abc-123",
  "operation": "payment_processing",
  "message": "Payment gateway timeout",
  "context": {
    "orderId": "order-123",
    "amount": 99.99,
    "gateway": "stripe"
  },
  "environment": {
    "node_version": "v20.10.0",
    "os": "darwin",
    "platform": "Darwin",
    "architecture": "arm64",
    "runtime": "node"
  },
  "source": "payment.ts:42 in processPayment()",
  "stack_trace": "Error: Payment gateway timeout\n    at processPayment...",
  "human_note": "Payment timeouts have increased lately",
  "ai_todo": "Analyze payment gateway performance trends"
}
```

## 🧪 Testing

```bash
# Build the project
npm run build

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Type checking
npm run lint
```

## 📁 File Organization

Logs are automatically organized with timestamps in your project folder:

```
./logs/
├── my-project/
│   ├── vibe_20250707_143052.log
│   ├── vibe_20250707_151230.log
│   └── vibe_20250707_163045.log.20250707_170000  # Rotated
└── other-project/
    └── vibe_20250707_144521.log
```

## 🎯 AI Integration Workflow

1. **Code with VibeCoding Logger** - Add rich logging throughout your application
2. **Run Your Code** - Logger captures detailed context automatically  
3. **Get AI Analysis** - Use `getLogsForAI()` to get formatted data
4. **Send to LLM** - Paste structured logs into ChatGPT, Claude, etc.
5. **Get Precise Solutions** - LLM provides targeted fixes with full context

## 🔗 Cross-Language Compatibility

This TypeScript implementation maintains 100% JSON format compatibility with:
- **Python** (reference implementation)
- **Future languages** (Go, Rust, etc.)

## 📚 Examples

See the `examples/` directory for:
- Basic usage patterns
- Advanced configuration
- Error handling
- Memory management
- Correlation tracking

## 🤝 Contributing

Contributions welcome! Please see the main repository guidelines and:

1. Follow TypeScript best practices
2. Maintain JSON compatibility with Python version
3. Add tests for new features
4. Update documentation

## 📄 License

MIT License - see [LICENSE](../LICENSE) file for details.

---

**Built for the VibeCoding era - where humans design and AI implements.** 🚀