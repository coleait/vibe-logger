# VibeCoding Logger

**AI-Native Logging for LLM Agent Development - Multi-Language Implementation**

VibeCoding Logger is a specialized logging library designed for AI-driven development where LLMs need rich, structured context to understand and debug code effectively. Unlike traditional human-readable logs, this creates "AI briefing packages" with comprehensive context, correlation tracking, and embedded human annotations.

## 🎯 Concept

In VibeCoding (AI-driven development), the quality of debugging depends on how much context you can provide to the LLM. Traditional logs are designed for humans, but LLMs need structured, machine-readable data with rich context to provide accurate analysis and solutions.

## ✨ Key Features

- **🤖 AI-Optimized**: Structured JSON format optimized for LLM consumption
- **📦 Rich Context**: Function arguments, stack traces, environment info
- **🔗 Correlation Tracking**: Track request flows across operations
- **💬 Human Annotations**: Embed AI instructions directly in logs (`human_note`, `ai_todo`)
- **⏰ Timestamped Files**: Automatic file saving with timestamp-based naming
- **🔄 Log Rotation**: Prevent large files with automatic rotation
- **🧵 Thread Safe**: Safe for concurrent/multi-threaded applications
- **🌍 UTC Timestamps**: Consistent timezone handling
- **💾 Memory Management**: Configurable memory limits to prevent OOM

## 🌍 Language Support

| Language | Status | Package | Documentation |
|----------|--------|---------|---------------|
| **Python** | ✅ **Stable** | `pip install vibelogger` | [Python Docs](python/README.md) |
| **TypeScript/Node.js** | ✅ **Stable** | `npm install vibelogger` | [TypeScript Docs](typescript/README.md) |
| **Go** | 📋 **Planned** | - | - |
| **Rust** | 📋 **Planned** | - | - |

## 🚀 Quick Start

### Installation

**Python:**
```bash
pip install vibelogger
```

**TypeScript/Node.js:**
```bash
npm install vibelogger
```

### Vibe Usage
Add this instruction to your project's CLAUDE.md file to enable AI-assisted debugging:

```markdown
### Project Logging
* Use vibelogger library for all logging needs
* vibelogger instruction: https://github.com/fladdict/vibe-logger/blob/main/README.md
* Check ./logs/<project_name>/ folder for debugging data when issues occur
```

Then simply ask Claude Code or other AI assistants to implement logging in your code. When debugging is needed, instruct the AI to read the log files for context.

### Basic Usage

**Python:**
```python
from vibelogger import create_file_logger

# Create logger with auto-save to timestamped file
logger = create_file_logger("my_project")

# Log with rich context for AI analysis
logger.info(
    operation="fetchUserProfile",
    message="Starting user profile fetch",
    context={"user_id": "123", "source": "api_endpoint"},
    human_note="AI-TODO: Check if user exists before fetching profile"
)

# Logs are automatically saved to ./logs/my_project/ folder
# AI can read these files when debugging is needed
```

**TypeScript/Node.js:**
```typescript
import { createFileLogger } from 'vibelogger';

// Create logger with auto-save to timestamped file
const logger = createFileLogger("my_project");

// Log with rich context for AI analysis
await logger.info(
    "fetchUserProfile",
    "Starting user profile fetch",
    {
        context: { user_id: "123", source: "api_endpoint" },
        human_note: "AI-TODO: Check if user exists before fetching profile"
    }
);

// Logs are automatically saved to ./logs/my_project/ folder
// AI can read these files when debugging is needed
```

For complete documentation:
- **Python**: [python/README.md](python/README.md)
- **TypeScript**: [typescript/README.md](typescript/README.md)

## 📋 Advanced Usage

### Custom Configuration

```python
from vibelogger import create_logger, VibeLoggerConfig

config = VibeLoggerConfig(
    log_file="./logs/custom.log",
    max_file_size_mb=50,
    auto_save=True,
    keep_logs_in_memory=True,
    max_memory_logs=1000
)
logger = create_logger(config=config)
```

### Environment-Based Configuration

```python
from vibelogger import create_env_logger

# Set environment variables:
# VIBE_LOG_FILE=/path/to/logfile.log
# VIBE_MAX_FILE_SIZE_MB=25
# VIBE_AUTO_SAVE=true

logger = create_env_logger()
```

### Memory-Efficient Logging

```python
from vibelogger import VibeLoggerConfig, create_logger

# For long-running processes - disable memory storage
config = VibeLoggerConfig(
    log_file="./logs/production.log",
    keep_logs_in_memory=False,  # Don't store logs in memory
    auto_save=True
)
logger = create_logger(config=config)
```

## 🔧 AI Integration

The logger creates structured data that LLMs can immediately understand:

```json
{
  "timestamp": "2025-07-07T08:36:42.123Z",
  "level": "ERROR", 
  "correlation_id": "req_abc123",
  "operation": "fetchUserProfile",
  "message": "User profile not found",
  "context": {
    "user_id": "user-123",
    "query": "SELECT * FROM users WHERE id = ?"
  },
  "environment": {
    "python_version": "3.11.0",
    "os": "Darwin"
  },
  "source": "/app/user_service.py:42 in get_user_profile()",
  "human_note": "AI-TODO: Check database connection",
  "ai_todo": "Analyze why user lookup is failing"
}
```

### Key Fields for AI Analysis

- **`timestamp`**: ISO format with UTC timezone
- **`correlation_id`**: Links related operations across the request
- **`operation`**: What the code was trying to accomplish
- **`context`**: Function arguments, variables, state information
- **`environment`**: Runtime info for reproduction
- **`source`**: Exact file location and function name
- **`human_note`**: Natural language instructions for the AI
- **`ai_todo`**: Specific analysis requests

## 📁 Log File Organization

Logs are automatically organized with timestamps in your project folder:

```
./logs/
├── my_project/
│   ├── vibe_20250707_143052.log
│   ├── vibe_20250707_151230.log
│   └── vibe_20250707_163045.log.20250707_170000  # Rotated
└── other_project/
    └── vibe_20250707_144521.log
```

## 🛡️ Thread Safety

VibeCoding Logger is fully thread-safe:

```python
import threading
from vibelogger import create_file_logger

logger = create_file_logger("multi_threaded_app")

def worker(worker_id):
    logger.info(
        operation="worker_task",
        message=f"Worker {worker_id} processing",
        context={"worker_id": worker_id}
    )

# Safe to use across multiple threads
threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
```

## 🎯 VibeCoding Workflow

1. **Setup VibeCoding Logger**: Add logging instructions to your CLAUDE.md file
2. **Code with Rich Logging**: Ask AI to implement vibelogger in your code
3. **Run Your Code**: Logger captures detailed context automatically
4. **Debug with AI**: When issues occur, instruct AI to read the log files
5. **Get Precise Solutions**: AI analyzes the structured logs and provides targeted fixes

## 📚 Documentation

### Core Documentation
- **[VibeCoding Concept & Theory](docs/CONCEPT.md)** - Understanding VibeCoding and AI-native logging
- **[Technical Specification](docs/SPECIFICATION.md)** - Detailed API and implementation spec
- **[Python Implementation](python/README.md)** - Python-specific documentation and examples

### Examples
- **Python**: [`python/examples/`](python/examples/) - Basic usage and framework integrations
- **TypeScript**: [`typescript/`](typescript/) - Coming soon (contributors needed!)

### Framework Integrations
- **Django**: [`python/examples/integrations/django_integration.py`](python/examples/integrations/django_integration.py)
- **FastAPI**: [`python/examples/integrations/fastapi_integration.py`](python/examples/integrations/fastapi_integration.py)
- **Flask**: [`python/examples/integrations/flask_integration.py`](python/examples/integrations/flask_integration.py)
- **Standard Logging**: [`python/examples/integrations/standard_logging_example.py`](python/examples/integrations/standard_logging_example.py)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 Why VibeCoding Logger?

Traditional logging is designed for human debugging. But in the age of AI-assisted development, we need logs that AI can understand and act upon. VibeCoding Logger bridges this gap by providing:

- **Context-Rich Data**: Everything an LLM needs to understand the problem
- **Structured Format**: Machine-readable JSON instead of human-readable text  
- **AI Instructions**: Direct communication with your AI assistant
- **Correlation Tracking**: Understanding of request flows and relationships

Transform your debugging from "guess and check" to "analyze and solve" with AI-native logging.

---

**Built for the VibeCoding era - where humans design and AI implements.** 🚀